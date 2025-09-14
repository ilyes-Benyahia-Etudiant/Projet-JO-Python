from typing import List, Optional, Dict, Any
from backend.infra.supabase_client import get_supabase, get_service_supabase
import logging

logger = logging.getLogger(__name__)

def list_offres() -> List[dict]:
    try:
        res = get_supabase().table("offres").select("*").execute()
        return res.data or []
    except Exception:
        return []

def get_offre(offre_id: str) -> Optional[dict]:
    if not offre_id:
        return None
    try:
        res = (
            get_supabase()
            .table("offres")
            .select("*")
            .eq("id", offre_id)
            .single()
            .execute()
        )
        return res.data or None
    except Exception:
        return None

def create_offre(data: Dict[str, Any]) -> Optional[dict]:
    try:
        res = get_service_supabase().table("offres").insert(data).execute()
        rows = getattr(res, "data", None) or []
        if isinstance(rows, list) and rows:
            return rows[0]
        return {"status": "ok"}
    except Exception:
        logger.exception("offres.repository.create_offre failed data=%s", data)
        return None

def update_offre(offre_id: str, data: Dict[str, Any]) -> Optional[dict]:
    try:
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
        return {"status": "ok"}
    except Exception:
        logger.exception("offres.repository.update_offre failed id=%s data=%s", offre_id, data)
        return None

def delete_offre(offre_id: str) -> bool:
    try:
        get_service_supabase().table("offres").delete().eq("id", offre_id).execute()
        return True
    except Exception:
        logger.exception("offres.repository.delete_offre failed id=%s", offre_id)
        return False