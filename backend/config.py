# backend.config
from pathlib import Path
import os
from dotenv import load_dotenv

# Calculer le chemin du projet puis charger .env de manière explicite
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

PUBLIC_DIR = BASE_DIR / "public"
TEMPLATES_DIR = BASE_DIR / "templates"

def _clean_env(v: str) -> str:
    # Supprime espaces, guillemets simples/doubles et backticks
    return (v or "").strip().strip("'").strip('"').strip("`")

# Supabase
SUPABASE_URL = _clean_env(os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "")
SUPABASE_KEY = _clean_env(os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "")
SUPABASE_ANON = _clean_env(os.getenv("SUPABASE_ANON_KEY") or "")

# Normalisations utiles
if SUPABASE_URL and not SUPABASE_URL.startswith("http"):
    SUPABASE_URL = "https://" + SUPABASE_URL
if SUPABASE_URL.endswith("/"):
    SUPABASE_URL = SUPABASE_URL.rstrip("/")

# Cookies/ Sécurité
COOKIE_SECURE = (os.getenv("COOKIE_SECURE", "false").lower() == "true")
ADMIN_EMAILS = [e.strip() for e in os.getenv("ADMIN_EMAILS", "admin@example.com").split(",") if e.strip()]
ADMIN_SIGNUP_CODE = os.getenv("ADMIN_SIGNUP_CODE", "")  # legacy
# Supprime l'ancien si présent
# ADMIN_SECRET_PASSWORD = os.getenv("ADMIN_SECRET_PASSWORD", "")  # Comment ou supprime

# Ajoute ou garde
ADMIN_SECRET_HASH = os.getenv("ADMIN_SECRET_HASH", "")

# CORS (dev)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
RESET_REDIRECT_URL = os.getenv("RESET_REDIRECT_URL", "http://localhost:8000/auth/reset")
SIGNUP_REDIRECT_URL = os.getenv("SIGNUP_REDIRECT_URL", "http://localhost:8000/auth")
STRIPE_PUBLIC_KEY = _clean_env(os.getenv("STRIPE_PUBLIC_KEY") or "")
STRIPE_SECRET_KEY = _clean_env(os.getenv("STRIPE_SECRET_KEY") or "")
STRIPE_WEBHOOK_SECRET = _clean_env(os.getenv("STRIPE_WEBHOOK_SECRET") or "")
CHECKOUT_SUCCESS_PATH = os.getenv("CHECKOUT_SUCCESS_PATH", "/session?payment=success")
CHECKOUT_CANCEL_PATH = os.getenv("CHECKOUT_CANCEL_PATH", "/session?payment=cancel")
SUPABASE_SERVICE_KEY = _clean_env(os.getenv("SUPABASE_SERVICE_KEY") or "")

BASE_URL = _clean_env(os.getenv("BASE_URL") or "http://localhost:8000")