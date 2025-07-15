from fastapi import HTTPException
from app.database import supabase
from app.models import UserRegister, UserLogin

def register_user(user: UserRegister):
    # Créer l'utilisateur via Supabase Auth
    response = supabase.auth.sign_up({
        "email": user.email,
        "password": user.password,
        
    })

    if hasattr(response, 'error'):
        raise HTTPException(status_code=400, detail=response.error.message)

    # Optionnel : Enregistrer le pseudo dans une table users
    user_data = {
        "id": response.user.id,
        "email": user.email,
        "username": user.nom
        
    }
    supabase.table("users").insert(user_data).execute()
    return {"message": "User registered successfully"}

def login_user(user: UserLogin):
    response = supabase.auth.sign_in_with_password({
        "email": user.email,
        "password": user.password
    })

    if hasattr(response, 'error'):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {"access_token": response.session.access_token, "user": response.user}