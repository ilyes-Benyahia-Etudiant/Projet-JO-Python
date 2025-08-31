import os
from pathlib import Path
from dotenv import load_dotenv

# Charger explicitement le .env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

def _clean_env(v: str) -> str:
    return (v or "").strip().strip("'").strip('"').strip("`")

SUPABASE_URL = _clean_env(os.getenv("SUPABASE_URL") or "")
SUPABASE_KEY = _clean_env(os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "")

print("Chemin du .env utilisé :", ENV_PATH)
print("SUPABASE_URL :", SUPABASE_URL)
print("SUPABASE_KEY (début) :", SUPABASE_KEY[:10] + "...")

# Test rapide de résolution DNS
import socket
try:
    hostname = SUPABASE_URL.replace("https://", "").split("/")[0]
    print("Hostname Supabase :", hostname)
    ip = socket.gethostbyname(hostname)
    print("Résolution DNS OK :", ip)
except Exception as e:
    print("❌ Erreur DNS :", e)
