from typing import List, Optional, Dict, Any
from backend.infra.supabase_client import get_supabase, get_service_supabase
import logging

logger = logging.getLogger(__name__)

# module backend.admin.repository
def fetch_admin_commandes(limit: int = 100) -> List[dict]:
    """
    Commandes pour l'admin, sans jointures (retourne aussi user_id/offre_id pour l'affichage fallback)
    """
    try:
        res = (
            get_service_supabase()
            .table("commandes")
            .select(
                "id, token, price_paid, created_at, user_id, offre_id, users(email), offres(title, price)"
            )
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        logger.exception("admin.repository.fetch_admin_commandes failed")
        return []


def fetch_admin_users(limit: int = 100) -> List[dict]:
    """
    Liste basique des utilisateurs pour l'admin.
    """
    try:
        res = (
            get_service_supabase()
            .table("users")
            .select("id, email, full_name, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def count_table_rows(table_name: str) -> int:
    """
    Compte les lignes d'une table via Supabase.
    Utilise count='exact' si disponible, sinon fallback sur len(data).
    """
    try:
        client = get_service_supabase()
        res = client.table(table_name).select("id", count="exact").execute()
        if getattr(res, "count", None) is not None:
            return int(res.count)  # type: ignore
        return len(res.data or [])
    except Exception:
        return 0


def delete_user(user_id: str) -> bool:
    try:
        get_service_supabase().table("users").delete().eq("id", user_id).execute()
        # res.data peut être vide selon la politique; considérer succès si pas d'erreur
        return True
    except Exception:
        logger.exception("admin.repository.delete_user failed id=%s", user_id)
        return False


def update_user(user_id: str, data: Dict[str, Any]) -> Optional[dict]:
    try:
        res = (
            get_service_supabase()
            .table("users")
            .update(data)
            .eq("id", user_id)
            .execute()
        )
        updated = (res.data or [None])[0]
        if not updated:
            # Fallback: relire l'utilisateur
            res2 = (
                get_service_supabase()
                .table("users")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )
            return res2.data or None
        return updated
    except Exception:
        logger.exception("admin.repository.update_user failed id=%s data=%s", user_id, data)
        return None


def delete_commande(commande_id: str) -> bool:
    try:
        get_service_supabase().table("commandes").delete().eq("id", commande_id).execute()
        return True
    except Exception:
        logger.exception("admin.repository.delete_commande failed id=%s", commande_id)
        return False


def update_commande(commande_id: str, data: Dict[str, Any]) -> Optional[dict]:
    try:
        res = (
            get_service_supabase()
            .table("commandes")
            .update(data)
            .eq("id", commande_id)
            .execute()
        )
        updated = (res.data or [None])[0]
        if not updated:
            # Fallback: relire la commande
            res2 = (
                get_service_supabase()
                .table("commandes")
                .select("*")
                .eq("id", commande_id)
                .single()
                .execute()
            )
            return res2.data or None
        return updated
    except Exception:
        logger.exception("admin.repository.update_commande failed id=%s data=%s", commande_id, data)
        return None

# Récupérer une commande par ID (pour préremplir le formulaire d'édition)
def get_commande_by_id(commande_id: str) -> Optional[dict]:
    if not commande_id:
        return None
    try:
        res = (
            get_service_supabase()
            .table("commandes")
            .select("id, token, price_paid, created_at, user_id, offre_id")
            .eq("id", commande_id)
            .single()
            .execute()
        )
        return res.data or None
    except Exception:
        logger.exception("admin.repository.get_commande_by_id failed id=%s", commande_id)
        return None