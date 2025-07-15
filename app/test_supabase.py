from database import supabase

# Test : Récupère tous les utilisateurs de la table "users"
response = supabase.table("users").select("*").execute()

# Affiche les résultats
print("Données récupérées depuis Supabase :")
print(response.data)