from typing import Any, Dict, Optional
import logging
from supabase import create_client
from backend.config import SUPABASE_URL, SUPABASE_ANON
from backend.infra.supabase_client import get_supabase, get_service_supabase

logger = logging.getLogger(__name__)

def get_ticket_by_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Récupère une 'commande' (billet) par token, avec détails d'offre.
    """
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, user_id, created_at, offres(title, description, image), users(full_name,email)")
            .eq("token", token)
            .limit(1)
            .execute()
        )
        data = (res.data or [])
        return data[0] if data else None
    except Exception:
        return None


def get_last_validation(token: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la dernière validation enregistrée pour ce token.
    """
    try:
        res = (
            get_supabase()
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


def insert_validation(
    token: str,
    commande_id: str,
    admin_id: str,
    status: str = "validated",
    user_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Insère un enregistrement de validation.
    - Essaie d'abord via clé service (bypass RLS)
    - En fallback, tente via le JWT admin (respecte RLS) si fourni
    """
    try:
        res = (
            get_service_supabase()
            .table("ticket_validations")
            .insert({
                "token": token,
                "commande_id": commande_id,
                "scanned_by": admin_id,
                "status": status,
            })
            .select("*")  # S'assure de récupérer la ligne insérée
            .execute()
        )
        rows = res.data or []
        return rows[0] if isinstance(rows, list) and rows else (res.data or None)
    except Exception:
        logger.exception(
            "insert_validation via service-role failed (commande_id=%s, admin_id=%s)",
            commande_id,
            admin_id,
        )
        # Fallback: utiliser le token utilisateur (admin) si disponible
        if user_token:
            try:
                client = create_client(SUPABASE_URL, SUPABASE_ANON)
                client.postgrest.auth(user_token)
                res = (
                    client
                    .table("ticket_validations")
                    .insert({
                        "token": token,
                        "commande_id": commande_id,
                        "scanned_by": admin_id,
                        "status": status,
                    })
                    .select("*")
                    .execute()
                )
                rows = res.data or []
                return rows[0] if isinstance(rows, list) and rows else (res.data or None)
            except Exception:
                logger.exception(
                    "insert_validation via user-token failed (commande_id=%s, admin_id=%s)",
                    commande_id,
                    admin_id,
                )
        return None