import os
from dotenv import load_dotenv

# Charger le .env depuis la racine
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

print("Fichier .env chargé depuis :", ENV_PATH)

# Vérification brute
print("Brut depuis os.environ :", os.environ.get("SUPABASE_URL"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

print("URL :", SUPABASE_URL)
print("KEY (début) :", SUPABASE_KEY[:10] if SUPABASE_KEY else None)
