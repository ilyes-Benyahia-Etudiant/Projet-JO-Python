# Module: backend/models/offres.py
from typing import List, Optional, Dict, Any
from backend.models.db import get_supabase, get_service_supabase
import logging

logger = logging.getLogger(__name__)

def fetch_offres() -> List[dict]:
    try:
        res = get_supabase().table("offres").select("*").execute()
        return res.data or []
    except Exception:
        return []

def fetch_admin_commandes(limit: int = 100) -> List[dict]:
    """
    Commandes pour l'admin, avec jointures sur users et offres
    """
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, price_paid, created_at, users(email), offres(title, price)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def fetch_user_commandes(user_id: str, limit: int = 50) -> List[dict]:
    """
    Commandes de l'utilisateur connecté (jointure offre)
    """
    if not user_id:
        return []
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, price_paid, created_at, offres(title, price)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def get_offre(offre_id: str) -> Optional[dict]:
    try:
        res = get_supabase().table("offres").select("*").eq("id", offre_id).single().execute()
        return res.data or None
    except Exception:
        return None

def create_offre(data: Dict[str, Any]) -> Optional[dict]:
    try:
        # Certaines versions de supabase-py ne supportent pas .select() après insert
        res = get_service_supabase().table("offres").insert(data).execute()
        rows = getattr(res, "data", None) or []
        if isinstance(rows, list) and rows:
            return rows[0]
        # Fallback: retourner un dict truthy si la réponse n'inclut pas les lignes
        return {"status": "ok"}
    except Exception:
        logger.exception("create_offre failed data=%s", data)
        return None

def update_offre(offre_id: str, data: Dict[str, Any]) -> Optional[dict]:
    try:
        # Certaines versions de supabase-py ne supportent pas .select() après update
        res = (
            get_service_supabase()
            .table("offres")
            .update(data)
            .eq("id", offre_id)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if isinstance(rows, list) and rows:
            return rows[0]
        # Fallback: retourner un dict truthy si la réponse n'inclut pas les lignes
        return {"status": "ok"}
    except Exception:
        logger.exception("update_offre failed id=%s data=%s", offre_id, data)
        return None

def delete_offre(offre_id: str) -> bool:
    try:
        get_service_supabase().table("offres").delete().eq("id", offre_id).execute()
        return True
    except Exception:
        logger.exception("delete_offre failed id=%s", offre_id)
        return False