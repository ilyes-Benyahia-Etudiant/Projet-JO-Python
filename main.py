from backend.infra.supabase_client import get_supabase

def main():
    try:
        _ = get_supabase()
        print("Client Supabase initialisé avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'appel Supabase: {e}")

if __name__ == "__main__":
    main()