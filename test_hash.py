import bcrypt
from backend.config import ADMIN_SECRET_HASH  # Assure-toi que config.py est importable

plain_password = "Session_Admin_12$"

if not ADMIN_SECRET_HASH:
    print("Erreur: ADMIN_SECRET_HASH n'est pas défini dans .env ou config.py")
else:
    match = bcrypt.checkpw(plain_password.encode('utf-8'), ADMIN_SECRET_HASH.encode('utf-8'))
    print(f"Correspondance du hash: {match}")
    if match:
        print("Le hash match bien – le problème vient d'ailleurs (ex: mot de passe utilisé lors du test).")
    else:
        print("Pas de correspondance – régénère le hash (voir étape 2).")