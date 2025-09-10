import re

def validate_password_strength(v: str) -> str:
    if not re.search(r'[A-Z]', v):
        raise ValueError('Le mot de passe doit contenir au moins une majuscule')
    if not re.search(r'[a-z]', v):
        raise ValueError('Le mot de passe doit contenir au moins une minuscule')
    if not re.search(r'\d', v):
        raise ValueError('Le mot de passe doit contenir au moins un chiffre')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'\"\\|,.<>\/?]', v):
        raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
    return v