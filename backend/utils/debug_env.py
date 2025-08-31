import os
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
print("Chemin .env détecté :", env_path)

# Lire brut sans dotenv
print("\n--- Contenu brut du .env ---")
with open(env_path, "r", encoding="utf-8") as f:
    print(f.read())

# Charger avec dotenv
load_dotenv(env_path, override=True)
print("\n--- Valeurs après load_dotenv ---")
print("SUPABASE_URL =", os.environ.get("SUPABASE_URL"))
print("SUPABASE_KEY =", os.environ.get("SUPABASE_ANON_KEY")[:10], "...")
