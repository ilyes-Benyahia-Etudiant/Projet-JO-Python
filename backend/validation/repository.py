# module backend.validation.repository
from typing import Any, Dict, Optional
import logging
from supabase import create_client
from backend.config import SUPABASE_URL, SUPABASE_ANON
from backend.infra.supabase_client import get_service_supabase
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

def get_ticket_by_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Récupère une 'commande' (billet) par token, avec détails d'offre et l'utilisateur (incluant bio pour vérification).
    """
    from backend.infra.supabase_client import get_supabase
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, user_id, created_at, offres(title, description, image), users(full_name,email,bio)")
            .eq("token", token)
            .single()
            .execute()
        )
        return res.data or None
    except Exception:
        return None

def get_last_validation(token: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la dernière validation enregistrée pour ce token.
    """
    try:
        res = (
            get_service_supabase()
            .table("ticket_validations")
            .select("id, token, commande_id, scanned_at, scanned_by, status")
            .eq("token", token)
            .order("scanned_at", desc=True)
            .limit(1)
            .execute()
        )
        data = (res.data or [])
        return data[0] if data else None
    except Exception:
        return None


def insert_validation(token: str, commande_id: str, admin_id: str, status: str = "validated", user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    # Utilise le client service-role pour éviter les problèmes RLS.
    # Retourne None en cas de doublon (23505), le service traitera 'already_validated'.
    payload = {
        "token": token,
        "commande_id": commande_id,
        "scanned_by": admin_id,
        "status": status,
    }

    client = get_service_supabase()
    try:
        res = client.table("ticket_validations").insert(payload).execute()
        data = res.data or []
        if isinstance(data, list):
            return data[0] if data else payload
        if isinstance(data, dict):
            return data
        return payload
    except APIError as e:
        code = None
        if e.args and isinstance(e.args[0], dict):
            code = e.args[0].get("code")
        if code == "23505":
            return None
        return None