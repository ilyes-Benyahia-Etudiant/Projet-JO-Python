from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import jwt
import httpx
from supabase import create_client, Client
from typing import Optional

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

# Middleware/utilitaires d'auth (validation JWT côté serveur)
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

# Exemple d'endpoint protégé (vérifie le token)
@app.get("/secure")
async def secure_route(token: str = Depends(get_bearer_token)):
    # Optionnel: validation locale du JWT si SUPABASE_JWT_SECRET disponible
    if SUPABASE_JWT_SECRET:
        try:
            jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"JWT invalide: {e}")
    return {"ok": True}

# Healthcheck pour l'API Gateway
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

# =================== NOUVEAUX ENDPOINTS AUTH PROXY ===================

# Modèles Pydantic pour les requêtes auth
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResendRequest(BaseModel):
    email: str
    type: str = "signup"  # signup, email_change, etc.

class UpdatePasswordRequest(BaseModel):
    password: str

# Helper pour les requêtes vers Supabase Auth REST API
async def supabase_auth_request(method: str, endpoint: str, json_data: dict = None) -> dict:
    """Helper pour faire des requêtes vers l'API REST Supabase Auth"""
    url = f"{SUPABASE_URL}/auth/v1{endpoint}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, json=json_data)
        return response.status_code, response.json() if response.content else {}

@app.post("/auth/signup")
async def auth_signup(request: SignupRequest, response: Response):
    """Proxy pour l'inscription via Supabase Auth"""
    try:
        status_code, data = await supabase_auth_request(
            "POST", 
            "/signup",
            {"email": request.email, "password": request.password}
        )
        
        if status_code == 200 or status_code == 201:
            # Succès - vérifier si on a reçu une session
            session = data.get("session")
            if session and session.get("access_token"):
                # Poser le cookie de session automatiquement
                response.set_cookie(
                    key="sb_access",
                    value=session["access_token"],
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    max_age=60*60
                )
            return {"success": True, "message": "Inscription réussie", "data": data}
        
        elif status_code == 400:
            error_msg = data.get("error_description") or data.get("msg") or "Erreur d'inscription"
            if "already registered" in error_msg.lower() or "user already exists" in error_msg.lower():
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Cet email est déjà utilisé. Connectez-vous ou réinitialisez votre mot de passe."}
                )
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_msg}
            )
        
        else:
            return JSONResponse(
                status_code=status_code,
                content={"success": False, "message": "Erreur lors de l'inscription"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur serveur: {str(e)}"}
        )

@app.post("/auth/login")
async def auth_login(request: LoginRequest, response: Response):
    """Proxy pour la connexion via Supabase Auth"""
    try:
        status_code, data = await supabase_auth_request(
            "POST",
            "/token?grant_type=password",
            {"email": request.email, "password": request.password}
        )
        
        if status_code == 200:
            # Succès - poser le cookie de session
            access_token = data.get("access_token")
            if access_token:
                response.set_cookie(
                    key="sb_access",
                    value=access_token,
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    max_age=60*60
                )
            return {"success": True, "message": "Connexion réussie", "data": data}
        
        elif status_code == 400:
            error_msg = data.get("error_description") or data.get("msg") or "Email ou mot de passe incorrect"
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_msg}
            )
        
        else:
            return JSONResponse(
                status_code=status_code,
                content={"success": False, "message": "Erreur de connexion"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur serveur: {str(e)}"}
        )

@app.post("/auth/forgot")
async def auth_forgot_password(request: ForgotPasswordRequest):
    """Proxy pour la demande de réinitialisation de mot de passe"""
    try:
        status_code, data = await supabase_auth_request(
            "POST",
            "/recover",
            {"email": request.email}
        )
        
        if status_code == 200:
            return {"success": True, "message": "Email de réinitialisation envoyé"}
        
        elif status_code == 400:
            error_msg = data.get("error_description") or data.get("msg") or "Erreur lors de l'envoi de l'email"
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_msg}
            )
        
        else:
            return JSONResponse(
                status_code=status_code,
                content={"success": False, "message": "Erreur lors de la réinitialisation"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur serveur: {str(e)}"}
        )

@app.post("/auth/resend")
async def auth_resend(request: ResendRequest):
    """Proxy pour renvoyer l'email de confirmation"""
    try:
        status_code, data = await supabase_auth_request(
            "POST",
            "/resend",
            {"email": request.email, "type": request.type}
        )
        
        if status_code == 200:
            return {"success": True, "message": "Email de confirmation renvoyé"}
        
        elif status_code == 400:
            error_msg = data.get("error_description") or data.get("msg") or "Erreur lors du renvoi"
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_msg}
            )
        
        else:
            return JSONResponse(
                status_code=status_code,
                content={"success": False, "message": "Erreur lors du renvoi"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur serveur: {str(e)}"}
        )

@app.post("/auth/update-password")
async def auth_update_password(request: UpdatePasswordRequest, http_request: Request, response: Response):
    """Proxy pour mettre à jour le mot de passe (nécessite une session active)"""
    try:
        # Récupérer le token depuis le cookie ou l'en-tête Authorization
        token = http_request.cookies.get("sb_access")
        if not token:
            auth_header = http_request.headers.get('Authorization')
            if auth_header and auth_header.lower().startswith('bearer '):
                token = auth_header.split(' ', 1)[1]
        
        if not token:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Session requise pour mettre à jour le mot de passe"}
            )
        
        # Faire la requête vers Supabase avec le token d'autorisation
        url = f"{SUPABASE_URL}/auth/v1/user"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        async with httpx.AsyncClient() as client:
            http_response = await client.put(
                url, 
                headers=headers, 
                json={"password": request.password}
            )
            
            if http_response.status_code == 200:
                data = http_response.json() if http_response.content else {}
                # Optionnel: renouveler le cookie avec la nouvelle session si retournée
                new_session = data.get("session")
                if new_session and new_session.get("access_token"):
                    response.set_cookie(
                        key="sb_access",
                        value=new_session["access_token"],
                        httponly=True,
                        secure=False,
                        samesite="Lax",
                        max_age=60*60
                    )
                return {"success": True, "message": "Mot de passe mis à jour avec succès"}
            
            elif http_response.status_code == 401:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "message": "Session expirée ou invalide"}
                )
            
            else:
                error_data = http_response.json() if http_response.content else {}
                error_msg = error_data.get("error_description") or error_data.get("msg") or "Erreur lors de la mise à jour"
                return JSONResponse(
                    status_code=http_response.status_code,
                    content={"success": False, "message": error_msg}
                )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Erreur serveur: {str(e)}"}
        )