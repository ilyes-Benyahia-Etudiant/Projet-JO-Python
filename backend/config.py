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

"""
Configuration centrale du backend.

- Charge le fichier .env à la racine du projet (BASE_DIR/.env)
- Expose les chemins utiles (PUBLIC_DIR, TEMPLATES_DIR)
- Normalise et expose les secrets/URLs (Supabase, Stripe), sécurité cookies, CORS/hosts
- Fournit des URLs de redirection pour les flux (reset/signup, checkout)
"""

def _clean_env(v: str) -> str:
    """
    Nettoie une valeur d'environnement:
    - supprime les espaces et guillemets (simples, doubles) et backticks
    - retourne toujours une chaîne (jamais None)
    """
    # Supprime espaces, guillemets simples/doubles et backticks
    return (v or "").strip().strip("'").strip('"').strip("`")

# Supabase: URLs et clés (public/anon/service)
# - SUPABASE_URL peut parfois être sans schéma: on préfixe en https:// si nécessaire
# - Les clés sont nettoyées pour éviter des guillemets collés depuis certains envs
SUPABASE_URL = _clean_env(os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "")
SUPABASE_KEY = _clean_env(os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "")
SUPABASE_ANON = _clean_env(os.getenv("SUPABASE_ANON_KEY") or "")

# Normalisations utiles
if SUPABASE_URL and not SUPABASE_URL.startswith("http"):
    SUPABASE_URL = "https://" + SUPABASE_URL
if SUPABASE_URL.endswith("/"):
    SUPABASE_URL = SUPABASE_URL.rstrip("/")

# Cookies/ Sécurité: drapeaux et secrets pour rôles admin/scanner
COOKIE_SECURE = (os.getenv("COOKIE_SECURE", "false").lower() == "true")
ADMIN_EMAILS = [e.strip() for e in os.getenv("ADMIN_EMAILS", "admin@example.com").split(",") if e.strip()]
ADMIN_SIGNUP_CODE = os.getenv("ADMIN_SIGNUP_CODE", "")  # legacy
# ADMIN_SECRET_PASSWORD: obsolète — remplacé par ADMIN_SECRET_HASH

# Ajoute ou garde: hash secrets (éviter stockage en clair)
ADMIN_SECRET_HASH = _clean_env(os.getenv("ADMIN_SECRET_HASH", ""))
SCANNER_SECRET_HASH = _clean_env(os.getenv("SCANNER_SECRET_HASH", ""))

# CORS (dev)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# URLs de redirection post-actions auth
RESET_REDIRECT_URL = os.getenv("RESET_REDIRECT_URL", "http://localhost:8000/auth/reset")
SIGNUP_REDIRECT_URL = os.getenv("SIGNUP_REDIRECT_URL", "http://localhost:8000/auth")

# Stripe: clés publiques/privées et secrets webhook
STRIPE_PUBLIC_KEY = _clean_env(os.getenv("STRIPE_PUBLIC_KEY") or "")
STRIPE_SECRET_KEY = _clean_env(os.getenv("STRIPE_SECRET_KEY") or "")
STRIPE_WEBHOOK_SECRET = _clean_env(os.getenv("STRIPE_WEBHOOK_SECRET") or "")

# Pages de succès/annulation du checkout
CHECKOUT_SUCCESS_PATH = os.getenv("CHECKOUT_SUCCESS_PATH", "/session?payment=success")
CHECKOUT_CANCEL_PATH = os.getenv("CHECKOUT_CANCEL_PATH", "/session?payment=cancel")

# Supabase service key (opérations privilégiées côté serveur)
SUPABASE_SERVICE_KEY = _clean_env(os.getenv("SUPABASE_SERVICE_KEY") or "")

BASE_URL = _clean_env(os.getenv("BASE_URL") or "http://localhost:8000")