from dotenv import load_dotenv
import os
from supabase import create_client, Client

# Charger les variables d'environnement depuis .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Veuillez définir SUPABASE_URL et SUPABASE_ANON_KEY dans le fichier .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def main():
    # Exemple: lister les tables (via RPC ou schema introspection si configuré)
    # Ici on fait juste un ping simple en essayant de récupérer la date serveur via RPC si vous avez une fonction 'now'
    try:
        # Exemple d'appel (à adapter selon votre projet)
        # response = supabase.rpc("now").execute()
        # print(response)
        print("Client Supabase initialisé avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'appel Supabase: {e}")


if __name__ == "__main__":
    main()