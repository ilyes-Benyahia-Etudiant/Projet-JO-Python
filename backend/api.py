from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import jwt
import httpx
import logging
from supabase import create_client, Client
from typing import Optional
import urllib.parse
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Veuillez définir SUPABASE_URL et SUPABASE_ANON_KEY dans le fichier .env")

# URL de redirection des emails (prod ou local)
FRONTEND_URL = (
    os.getenv("PUBLIC_SITE_URL")
    or os.getenv("FRONTEND_URL")
    or os.getenv("RENDER_EXTERNAL_URL")
    or "http://localhost:8000"
)
if FRONTEND_URL and not FRONTEND_URL.startswith("http"):
    FRONTEND_URL = f"https://{FRONTEND_URL}"

# Déterminer automatiquement si les cookies doivent être 'secure'
_cookie_secure_env = os.getenv("COOKIE_SECURE")
if _cookie_secure_env is not None:
    COOKIE_SECURE = _cookie_secure_env.strip().lower() in ("1", "true", "yes")
else:
    # Par défaut: secure=True si FRONTEND_URL est en HTTPS, sinon False (utile en local)
    COOKIE_SECURE = FRONTEND_URL.lower().startswith("https://")

# Liste blanche des emails admin (séparés par des virgules), comparés en minuscules
_admin_emails_env = os.getenv("ADMIN_EMAILS", "")
ADMIN_EMAILS = {e.strip().lower() for e in _admin_emails_env.split(",") if e.strip()}
# Log de diagnostic (dev): combien d'emails admin chargés
logger.info("Admin allowlist loaded: %d email(s)", len(ADMIN_EMAILS))

def is_admin_email(email: Optional[str]) -> bool:
    return (email or "").strip().lower() in ADMIN_EMAILS

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = FastAPI(title="JO-PROJET API", version="1.0.0")

CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS")
if CORS_ALLOW_ORIGINS:
    allowed_origins = [o.strip() for o in CORS_ALLOW_ORIGINS.split(",") if o.strip()]
else:
    allowed_origins = ["http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

public_dir = os.path.join(os.path.dirname(__file__), '..', 'public')
public_dir = os.path.abspath(public_dir)
app.mount("/static", StaticFiles(directory=public_dir), name="public_static")

@app.get("/", response_class=FileResponse)
def root():
    index_path = os.path.join(public_dir, "index.html")
    return FileResponse(index_path)

@app.get("/auth", response_class=FileResponse)
def auth_page():
    auth_path = os.path.join(public_dir, "Authentification.html")
    return FileResponse(auth_path)

# Nouvelle route de session côté backend
@app.get("/session", response_class=FileResponse)
def session_page():
    session_path = os.path.join(public_dir, "session.html")
    return FileResponse(session_path)

class PublicKeys(BaseModel):
    supabase_url: str
    supabase_anon_key: str

@app.get("/config", response_model=PublicKeys)
def get_public_config():
    return PublicKeys(supabase_url=SUPABASE_URL, supabase_anon_key=SUPABASE_ANON_KEY)

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

def get_bearer_token(request: Request) -> str:
    auth = request.headers.get('Authorization')
    if not auth or not auth.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail="Authorization Bearer token requis")
    return auth.split(' ', 1)[1]

class Profile(BaseModel):
    id: str
    email: str

@app.get("/profile")
async def get_profile(token: str = Depends(get_bearer_token)):
    try:
        user = None
        try:
            res = supabase.auth.get_user(token)
            user = getattr(res, 'user', None) or (res.get('user') if isinstance(res, dict) else None)
        except Exception:
            user = None
        if not user:
            raise HTTPException(status_code=401, detail="Token invalide")
        uid = user.get('id') if isinstance(user, dict) else getattr(user, 'id', None)
        uemail = user.get('email') if isinstance(user, dict) else getattr(user, 'email', None)
        return {"id": str(uid), "email": str(uemail)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur profil: {e}")

@app.get("/secure")
async def secure_route(token: str = Depends(get_bearer_token)):
    if SUPABASE_JWT_SECRET:
        try:
            jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"JWT invalide: {e}")
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/session")
async def create_session(request: Request, response: Response):
    try:
        body = await request.json()
        token: Optional[str] = body.get('access_token') if isinstance(body, dict) else None
        if not token:
            raise HTTPException(status_code=400, detail="access_token manquant")
        if SUPABASE_JWT_SECRET:
            try:
                jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"JWT invalide: {e}")
        response.set_cookie(
            key="sb_access",
            value=token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="Lax",
            max_age=60*60
        )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création session: {e}")

@app.get("/me")
async def me(request: Request):
    token = request.cookies.get("sb_access")
    if not token:
        raise HTTPException(status_code=401, detail="Cookie de session manquant")
    try:
        res = supabase.auth.get_user(token)
        user = getattr(res, 'user', None) or (res.get('user') if isinstance(res, dict) else None)
        if not user:
            raise HTTPException(status_code=401, detail="Token invalide")
        uid = user.get('id') if isinstance(user, dict) else getattr(user, 'id', None)
        uemail = user.get('email') if isinstance(user, dict) else getattr(user, 'email', None)
        # Fallback: on regarde aussi le user_metadata.role renvoyé par Supabase (utile en dev)
        user_metadata = None
        if isinstance(user, dict):
            user_metadata = (user.get('user_metadata') or user.get('app_metadata') or {})
        else:
            user_metadata = getattr(user, 'user_metadata', None) or getattr(user, 'app_metadata', None) or {}
        role_meta = None
        if isinstance(user_metadata, dict):
            role_meta = user_metadata.get('role')
        is_admin = is_admin_email(uemail) or (str(role_meta).strip().lower() == 'admin')
        role = "admin" if is_admin else "user"
        return {"id": uid, "email": uemail, "role": role}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur /me: {e}")

@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("sb_access")
    return {"ok": True}

@app.get("/admin", response_class=FileResponse)
def admin_page(request: Request):
    # Vérifier si l'utilisateur a un cookie de session valide
    token = request.cookies.get("sb_access")
    if not token:
        # Rediriger vers la page de connexion si pas de token
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=302)
    
    try:
        # Vérifier le token et le rôle
        res = supabase.auth.get_user(token)
        user = getattr(res, 'user', None) or (res.get('user') if isinstance(res, dict) else None)
        if not user:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/", status_code=302)
        
        uemail = user.get('email') if isinstance(user, dict) else getattr(user, 'email', None)
        user_metadata = None
        if isinstance(user, dict):
            user_metadata = (user.get('user_metadata') or user.get('app_metadata') or {})
        else:
            user_metadata = getattr(user, 'user_metadata', None) or getattr(user, 'app_metadata', None) or {}
        
        role_meta = None
        if isinstance(user_metadata, dict):
            role_meta = user_metadata.get('role')
        
        is_admin = is_admin_email(uemail) or (str(role_meta).strip().lower() == 'admin')
        
        if not is_admin:
            # Rediriger vers la page de session si pas admin
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/session", status_code=302)
        
        # Si admin, servir la page admin
        admin_path = os.path.join(public_dir, "admin.html")
        return FileResponse(admin_path)
        
    except Exception as e:
        logger.warning("Admin route access error: %s", e)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=302)

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
    type: str = "signup"

class UpdatePasswordRequest(BaseModel):
    password: str

async def supabase_auth_request(method: str, endpoint: str, json_data: dict = None, token: Optional[str] = None, extra_headers: Optional[dict] = None) -> dict:
    url = f"{SUPABASE_URL}/auth/v1{endpoint}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, json=json_data)
        return response.status_code, response.json() if response.content else {}

@app.post("/auth/signup")
async def auth_signup(request: SignupRequest, response: Response):
    try:
        redirect_q = urllib.parse.urlencode({"redirect_to": FRONTEND_URL})
        # Déterminer le rôle attendu selon l'allowlist
        desired_role = "admin" if is_admin_email(request.email) else "user"
        logger.info("Signup attempt: email=%s desired_role=%s", request.email, desired_role)
        
        payload = {"email": request.email, "password": request.password, "data": {"role": desired_role}}
        status_code, data = await supabase_auth_request(
            "POST",
            f"/signup?{redirect_q}",
            payload
        )
        
        # Debug: log what Supabase actually returns
        logger.info("Signup response from Supabase - status=%s data=%s", status_code, data)
        
        if status_code in (200, 201):
            # Supabase peut renvoyer soit { user, session }, soit directement un objet user (sans session)
            raw = data
            user = None
            session = None
            if isinstance(raw, dict) and ("user" in raw or "session" in raw):
                user = raw.get("user")
                session = raw.get("session")
            else:
                # data représente directement l'utilisateur créé
                user = raw
                session = None
            logger.info("Parsed signup (normalized): user=%s session=%s", bool(user), bool(session))
            
            # AJOUT: Si l'utilisateur a été créé avec succès ET qu'on a accès au user_id,
            # on force la mise à jour des métadonnées pour s'assurer que le rôle est bien sauvé
            user_id = None
            if user and isinstance(user, dict):
                user_id = user.get("id")
                current_metadata = user.get("user_metadata", {})
                logger.info("User created with metadata: %s", current_metadata)
                
                # Si le rôle n'est pas correctement défini dans les métadonnées, on le force
                if current_metadata.get("role") != desired_role:
                    logger.warning("Role mismatch in metadata, attempting to update user metadata")
                    # Utiliser l'API admin de Supabase pour forcer la mise à jour (nécessite service role key)
                    # Ou utiliser l'endpoint /user avec un token temporaire si disponible
                    if session and session.get("access_token"):
                        try:
                            update_status, update_data = await supabase_auth_request(
                                "PUT", 
                                "/user", 
                                {"data": {"role": desired_role}}, 
                                token=session["access_token"]
                            )
                            logger.info("Metadata update response: status=%s data=%s", update_status, update_data)
                        except Exception as e:
                            logger.error("Failed to update user metadata: %s", e)
            
            # Cas: utilisateur renvoyé sans session -> peut être une nouvelle inscription ou un email déjà existant
            if user and not session:
                email_confirmed_at = user.get("email_confirmed_at") if isinstance(user, dict) else None
                identities = user.get("identities") if isinstance(user, dict) else None
                logger.info("email_confirmed_at=%s identities_len=%s", email_confirmed_at, (len(identities) if isinstance(identities, list) else None))
                # Si confirmé OU aucune identity renvoyée -> considérer comme email déjà existant
                if email_confirmed_at or not identities:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": "Email déjà utilisé. Veuillez vous connecter ou réinitialiser votre mot de passe. Si vous n'avez pas reçu l'email, utilisez le bouton Renvoyer."}
                    )
                # Succès: email de confirmation envoyé pour une nouvelle inscription
                return {"success": True, "message": "Inscription réussie. Vérifiez votre boîte mail pour confirmer votre adresse.", "data": {"user_id": user.get("id") if isinstance(user, dict) else None, "role": desired_role}}
            
            # Cas: inscription réussie avec session (ex: confirmation auto)
            if session and session.get("access_token"):
                response.set_cookie(
                    key="sb_access",
                    value=session["access_token"],
                    httponly=True,
                    secure=COOKIE_SECURE,
                    samesite="Lax",
                    max_age=60*60
                )
                return {"success": True, "message": "Inscription réussie", "data": data}
            
            # Si status 200/201 mais réponse inattendue
            return JSONResponse(status_code=400, content={"success": False, "message": "Impossible de finaliser l'inscription. Réessayez ou utilisez un autre email."})
            
        elif status_code == 400:
            # Harmoniser les messages d'erreur Supabase pour user existant
            error_msg = (data.get("error_description") or data.get("msg") or data.get("message") or "Erreur d'inscription")
            msg_lower = error_msg.lower()
            if "already registered" in msg_lower or "exists" in msg_lower or "user already" in msg_lower:
                return JSONResponse(status_code=400, content={"success": False, "message": "Email déjà utilisé. Veuillez vous connecter ou réinitialiser votre mot de passe."})
            return JSONResponse(status_code=400, content={"success": False, "message": error_msg})
        else:
            return JSONResponse(status_code=status_code, content={"success": False, "message": "Erreur lors de l'inscription"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": f"Erreur serveur: {str(e)}"})

@app.post("/auth/login")
async def auth_login(request: Request, response: Response):
    try:
        # Support both JSON and form-encoded data
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            email = body.get("email")
            password = body.get("password")
        elif "application/x-www-form-urlencoded" in content_type:
            form = await request.form()
            email = form.get("email")
            password = form.get("password")
        else:
            return JSONResponse(status_code=400, content={"success": False, "message": "Type de contenu non supporté"})
        
        if not email or not password:
            if "application/json" in content_type:
                return JSONResponse(status_code=400, content={"success": False, "message": "Email et mot de passe requis"})
            else:
                # For form submission, redirect back with error (could be improved with session flash messages)
                return JSONResponse(status_code=400, content={"success": False, "message": "Email et mot de passe requis"})
        
        payload = {"email": email, "password": password}
        status_code, data = await supabase_auth_request("POST", "/token?grant_type=password", payload)
        
        if status_code in (200, 201):
            access_token = data.get("access_token")
            
            # Déterminer si l'utilisateur est admin pour choisir la redirection finale
            is_admin_user = False
            
            # Option A: synchroniser user_metadata.role à la connexion si allowlist => admin
            if access_token:
                try:
                    u_status, u_data = await supabase_auth_request("GET", "/user", token=access_token)
                    if u_status in (200, 201) and isinstance(u_data, dict):
                        uemail = u_data.get("email") or email
                        user_id = u_data.get("id")
                        meta = u_data.get("user_metadata") or {}
                        desired_admin = is_admin_email(uemail)
                        current_role = str((meta.get("role") or "")).strip().lower()
                        
                        # Synchroniser user_metadata.role dans Supabase auth
                        if desired_admin and current_role != "admin":
                            upd_status, upd_data = await supabase_auth_request(
                                "PUT",
                                "/user",
                                {"data": {"role": "admin"}},
                                token=access_token
                            )
                            logger.info("Login role sync: PUT /user status=%s", upd_status)
                        
                        # Déterminer le rôle admin effectif
                        is_admin_user = desired_admin or current_role == "admin"
                        
                        # Synchroniser public.users.role dans la DB relationnelle
                        if user_id and uemail:
                            try:
                                expected_role = "admin" if is_admin_user else "user"
                                # Authentifier les requêtes PostgREST avec le token du user (RLS)
                                supabase.postgrest.auth(access_token)
                                upsert_payload = {
                                    "id": user_id,
                                    "email": uemail,
                                    "role": expected_role,
                                    # laisser la DB/trigger gérer created_at/updated_at
                                    "last_sign_in": datetime.now(timezone.utc).isoformat(),
                                }
                                upsert_result = supabase.table("users").upsert(
                                    upsert_payload,
                                    on_conflict="id"
                                ).execute()
                                logger.info("DB users table upsert: success=%s", bool(getattr(upsert_result, 'data', None)))
                            except Exception as db_e:
                                logger.warning("Failed to sync users table: %s", db_e)
                            finally:
                                # Réinitialiser l'auth PostgREST
                                try:
                                    supabase.postgrest.auth(None)
                                except Exception:
                                    pass
                                    
                except Exception as e:
                    logger.warning("Login role sync failed: %s", e)
            
            # Fallback si on n'a pas pu lire le profil
            if not is_admin_user:
                try:
                    is_admin_user = is_admin_email(email)
                except Exception:
                    is_admin_user = False
            
            # Construire la réponse de redirection et y attacher le cookie
            from fastapi.responses import RedirectResponse
            target = "/admin" if is_admin_user else "/session"
            redirect = RedirectResponse(url=target, status_code=303)
            if access_token:
                redirect.set_cookie(
                    key="sb_access",
                    value=access_token,
                    httponly=True,
                    secure=COOKIE_SECURE,
                    samesite="Lax",
                    max_age=60*60
                )
            return redirect
                
        elif status_code == 400:
            error_msg = data.get("error_description") or data.get("error") or data.get("msg") or "Identifiants invalides"
            return JSONResponse(status_code=400, content={"success": False, "message": error_msg})
        else:
            return JSONResponse(status_code=status_code, content={"success": False, "message": "Erreur lors de la connexion"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": f"Erreur serveur: {str(e)}"})

@app.post("/auth/forgot")
async def auth_forgot_password(request: ForgotPasswordRequest):
    try:
        redirect_q = urllib.parse.urlencode({"redirect_to": FRONTEND_URL})
        status_code, data = await supabase_auth_request("POST", f"/recover?{redirect_q}", {"email": request.email})
        if status_code in (200, 201):
            return {"success": True, "message": "Email de réinitialisation envoyé si l'utilisateur existe."}
        elif status_code == 400:
            return JSONResponse(status_code=400, content={"success": False, "message": data.get("error_description") or data.get("msg") or "Erreur de demande de réinitialisation"})
        else:
            return JSONResponse(status_code=status_code, content={"success": False, "message": "Erreur lors de la demande de réinitialisation"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": f"Erreur serveur: {str(e)}"})

@app.post("/auth/resend")
async def auth_resend(request: ResendRequest):
    try:
        logger.info("Resend request: email=%s type=%s", request.email, request.type)
        # Supabase attend `type` dans le corps JSON; on conserve `redirect_to` en query
        redirect_q = urllib.parse.urlencode({"redirect_to": FRONTEND_URL})
        status_code, data = await supabase_auth_request(
            "POST",
            f"/resend?{redirect_q}",
            {"email": request.email, "type": request.type}
        )
        logger.info("Resend response from Supabase - status=%s data=%s", status_code, data)
        
        if status_code in (200, 201):
            return {"success": True, "message": "Email de confirmation renvoyé. Vérifiez votre boîte mail (y compris les spams)."}
        elif status_code == 400:
            error_msg = data.get("error_description") or data.get("msg") or data.get("message") or "Erreur de renvoi d'email"
            logger.info("Resend error: %s", error_msg)
            return JSONResponse(status_code=400, content={"success": False, "message": error_msg})
        elif status_code == 429:
            return JSONResponse(status_code=429, content={"success": False, "message": "Trop de tentatives. Réessayez plus tard."})
        else:
            logger.warning("Resend unexpected status: %s", status_code)
            return JSONResponse(status_code=status_code, content={"success": False, "message": "Erreur lors du renvoi d'email"})
    except Exception as e:
        logger.error("Resend exception: %s", str(e))
        return JSONResponse(status_code=500, content={"success": False, "message": f"Erreur serveur: {str(e)}"})

@app.post("/auth/update-password")
async def auth_update_password(request: UpdatePasswordRequest, http_request: Request, response: Response):
    try:
        token = http_request.cookies.get("sb_access")
        if not token:
            return JSONResponse(status_code=401, content={"success": False, "message": "Session expirée ou invalide. Reconnectez-vous."})
        status_code, data = await supabase_auth_request("PUT", "/user", {"password": request.password}, token=token)
        if status_code in (200, 201):
            return {"success": True, "message": "Mot de passe mis à jour."}
        elif status_code == 401:
            return JSONResponse(status_code=401, content={"success": False, "message": "Session expirée ou invalide. Reconnectez-vous."})
        else:
            return JSONResponse(status_code=status_code, content={"success": False, "message": data.get("error_description") or data.get("msg") or "Erreur lors de la mise à jour du mot de passe"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": f"Erreur serveur: {str(e)}"})
