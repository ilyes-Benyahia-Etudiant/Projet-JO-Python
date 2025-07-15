from database import supabase  # Change selon ton projet

# Données à insérer
new_user = {
    "email": "test@example.com",
    "nom": "Test User",
    "password": "monMotDePasse123",
}

# Insertion dans la table "users"
response = supabase.table("users").insert(new_user).execute()

# Vérifie si des données ont bien été renvoyées
if response.data and isinstance(response.data, list) and len(response.data) > 0:
    print("✅ Utilisateur inséré avec succès :", response.data)
else:
    print("❌ Aucune donnée retournée, insertion potentiellement échouée.")