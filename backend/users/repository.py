from typing import Any, Dict, List, Optional
from backend.infra.supabase_client import get_supabase, get_service_supabase

def get_user_orders(user_id: str) -> List[Dict[str, Any]]:
    # Remplacer par la logique locale si besoin
    # ... déjà défini dans ce fichier ...
    # Sert les commandes de l'utilisateur avec la jointure vers offres(title, price)
    if not user_id:
        return []
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, price_paid, created_at, offre_id, offres(title, price)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def get_offers() -> List[Dict[str, Any]]:
    # ... déjà défini dans ce fichier ...
    # Récupère les offres disponibles (triées par prix croissant si la colonne existe)
    try:
        res = (
            get_supabase()
            .table("offres")
            .select("*")
            .order("price", desc=False)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def get_user_by_email(email: str) -> Optional[dict]:
    try:
        res = get_supabase().table("users").select("*").eq("email", email).single().execute()
        return res.data or None
    except Exception:
        return None

def upsert_user_profile(user_id: str, email: str, role: Optional[str] = None) -> bool:
    if not email and not user_id:
        return False
    payload: Dict[str, Any] = {"email": email}
    if user_id:
        payload["id"] = user_id
    if role:
        payload["role"] = role
    try:
        get_service_supabase().table("users").upsert(payload).execute()
        return True
    except Exception:
        return False

def get_user_by_id(user_id: str) -> Optional[dict]:
    if not user_id:
        return None
    try:
        res = get_supabase().table("users").select("*").eq("id", user_id).single().execute()
        return res.data or None
    except Exception:
        return None