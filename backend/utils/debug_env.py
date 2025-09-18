# module backend.utils.debug_env
import os
from dotenv import load_dotenv

if __name__ == "__main__":
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
    anon = os.environ.get("SUPABASE_ANON_KEY") or ""
    print("SUPABASE_KEY =", (anon[:10] + " ...") if anon else None)
    print("SUPABASE_SERVICE_KEY present =", bool(os.environ.get("SUPABASE_SERVICE_KEY")))
    print("SUPABASE_SERVICE_KEY prefix =", repr((os.environ.get('SUPABASE_SERVICE_KEY') or '')[:6]) + '...')
# (Le contenu complet n'est pas affiché pour éviter d'exposer le secret.)
