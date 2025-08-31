import sys
from backend.utils.db import get_supabase

TABLES = ["users", "offres", "commandes"]

def check_table(client, table_name: str) -> tuple[bool, str]:
    try:
        res = client.table(table_name).select("*").limit(1).execute()
        count = len(res.data or [])
        return True, f"OK ({count} ligne(s) récupérée(s) en échantillon)"
    except Exception as e:
        return False, f"ERREUR: {e}"

def main():
    client = get_supabase()
    print("Vérification des tables Supabase:")
    print("--------------------------------")
    ok_all = True
    for name in TABLES:
        ok, msg = check_table(client, name)
        print(f"- {name}: {msg}")
        ok_all = ok_all and ok
    if not ok_all:
        print("\nAstuce: si la table 'users' n'existe pas (ex: vous utilisez auth.users), donnez-moi le schéma exact et j’adapte.")
        sys.exit(1)
    print("\nTout est accessible ✅")
    sys.exit(0)

if __name__ == "__main__":
    main()