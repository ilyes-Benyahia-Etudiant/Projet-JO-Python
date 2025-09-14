from typing import List
from backend.models.db import get_supabase
import logging

logger = logging.getLogger(__name__)

def fetch_admin_commandes(limit: int = 100) -> List[dict]:
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