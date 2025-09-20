from typing import List, Optional, Dict, Any
from backend.infra.supabase_client import get_supabase, get_service_supabase
import logging

logger = logging.getLogger(__name__)

def list_evenements() -> List[dict]:
    try:
        res = get_supabase().table("evenements").select("*").order("date_evenement", desc=False).execute()
        return res.data or []
    except Exception:
        return []

def get_evenement(evenement_id: str) -> Optional[dict]:
    if not evenement_id:
        return None
    try:
        res = (
            get_supabase()
            .table("evenements")
            .select("*")
            .eq("id", evenement_id)
            .single()
            .execute()
        )
        return res.data or None
    except Exception:
        return None

def create_evenement(data: Dict[str, Any]) -> Optional[dict]:
    try:
        res = get_service_supabase().table("evenements").insert(data).execute()
        rows = getattr(res, "data", None) or []
        if isinstance(rows, list) and rows:
            return rows[0]
        return {"status": "ok"}
    except Exception:
        logger.exception("evenements.repository.create_evenement failed data=%s", data)
        return None

def update_evenement(evenement_id: str, data: Dict[str, Any]) -> Optional[dict]:
    try:
        res = (
            get_service_supabase()
            .table("evenements")
            .update(data)
            .eq("id", evenement_id)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if isinstance(rows, list) and rows:
            return rows[0]
        return {"status": "ok"}
    except Exception:
        logger.exception("evenements.repository.update_evenement failed id=%s data=%s", evenement_id, data)
        return None

def delete_evenement(evenement_id: str) -> bool:
    try:
        get_service_supabase().table("evenements").delete().eq("id", evenement_id).execute()
        return True
    except Exception:
        logger.exception("evenements.repository.delete_evenement failed id=%s", evenement_id)
        return False