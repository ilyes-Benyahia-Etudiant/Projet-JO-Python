from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import jwt
from supabase import create_client, Client

# Charger .env pour obtenir SUPABASE_URL, SUPABASE_ANON_KEY
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Veuillez définir SUPABASE_URL et SUPABASE_ANON_KEY dans le fichier .env")

# Initialiser Supabase client (pour opérations côté serveur si besoin)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = FastAPI(title="JO-PROJET API", version="1.0.0")

# CORS (adapter origin pour votre domaine/API Gateway)
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS")  # ex: "https://app.exemple.com,https://www.exemple.com"
if CORS_ALLOW_ORIGINS:
    allowed_origins = [o.strip() for o in CORS_ALLOW_ORIGINS.split(",") if o.strip()]
else:
    # Par défaut, même origine en dev
    allowed_origins = ["http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir le front statique
public_dir = os.path.join(os.path.dirname(__file__), 'public')
app.mount("/static", StaticFiles(directory=public_dir), name="public_static")

@app.get("/", response_class=FileResponse)
def root():
    index_path = os.path.join(public_dir, "index.html")
    return FileResponse(index_path)

# Exposer les variables publiques pour le front (évite de hardcoder dans index.html)
class PublicKeys(BaseModel):
    supabase_url: str
    supabase_anon_key: str

@app.get("/config", response_model=PublicKeys)
def get_public_config():
    return PublicKeys(supabase_url=SUPABASE_URL, supabase_anon_key=SUPABASE_ANON_KEY)

# Middleware/utilitaires d’auth (validation JWT côté serveur)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # Facultatif si vous validez côté Supabase

def get_bearer_token(request: Request) -> str:
    auth = request.headers.get('Authorization')
    if not auth or not auth.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail="Authorization Bearer token requis")
    return auth.split(' ', 1)[1]

class Profile(BaseModel):
    id: str
    email: str

@app.get("/profile", response_model=Profile)
async def get_profile(token: str = Depends(get_bearer_token)):
    # Méthode 1: Demander le profil via Supabase (recommandé)
    try:
        user = None
        try:
            res = supabase.auth.get_user(token)
            # supabase-py retourne un objet avec attribut 'user' ou un dict
            user = getattr(res, 'user', None) or (res.get('user') if isinstance(res, dict) else None)
        except Exception:
            user = None
        if not user:
            raise HTTPException(status_code=401, detail="Token invalide")
        # user peut être dict ou objet -> normaliser
        uid = user.get('id') if isinstance(user, dict) else getattr(user, 'id', None)
        uemail = user.get('email') if isinstance(user, dict) else getattr(user, 'email', None)
        return Profile(id=str(uid), email=str(uemail))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur profil: {e}")

# Exemple d’endpoint protégé (vérifie le token)
@app.get("/secure")
async def secure_route(token: str = Depends(get_bearer_token)):
    # Optionnel: validation locale du JWT si SUPABASE_JWT_SECRET disponible
    if SUPABASE_JWT_SECRET:
        try:
            jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"JWT invalide: {e}")
    return {"ok": True}

# Healthcheck pour l’API Gateway
@app.get("/health")
async def health():
    return {"status": "ok"}

# Endpoint pour créer une session (cookie HttpOnly) à partir d'un access_token
@app.post("/session")
async def create_session(request: Request, response: Response):
    try:
        body = await request.json()
        token: Optional[str] = body.get('access_token') if isinstance(body, dict) else None
        if not token:
            raise HTTPException(status_code=400, detail="access_token manquant")
        # Optionnel: valider localement si SUPABASE_JWT_SECRET est fourni
        if SUPABASE_JWT_SECRET:
            try:
                jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"JWT invalide: {e}")
        # Déposer un cookie HttpOnly (exemple simple, ajustez SameSite/Secure pour prod)
        response.set_cookie(
            key="sb_access",
            value=token,
            httponly=True,
            secure=False,  # passez à True derrière HTTPS
            samesite="Lax",
            max_age=60*60  # 1h
        )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création session: {e}")

# Endpoint protégé par cookie HttpOnly
@app.get("/me")
async def me(request: Request):
    token = request.cookies.get("sb_access")
    if not token:
        raise HTTPException(status_code=401, detail="Cookie de session manquant")
    # Vérification côté Supabase
    try:
        res = supabase.auth.get_user(token)
        user = getattr(res, 'user', None) or (res.get('user') if isinstance(res, dict) else None)
        if not user:
            raise HTTPException(status_code=401, detail="Token invalide")
        uid = user.get('id') if isinstance(user, dict) else getattr(user, 'id', None)
        uemail = user.get('email') if isinstance(user, dict) else getattr(user, 'email', None)
        return {"id": uid, "email": uemail}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur /me: {e}")

# Endpoint pour supprimer la session (logout)
@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("sb_access")
    return {"ok": True}