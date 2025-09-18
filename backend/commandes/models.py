# module backend.commandes.models
from typing import List, Dict, Any, Optional
from backend.infra.supabase_client import get_service_supabase
from backend.admin import repository as admin_repository
import logging

logger = logging.getLogger(__name__)

def fetch_admin_commandes(limit: int = 100) -> List[dict]:
    # Délègue à la source unique de vérité
    return admin_repository.fetch_admin_commandes(limit)

def create_pending_commande(offre_id: str, user_id: str, price_paid: float) -> Optional[Dict[str, Any]]:
    try:
        res = (
            get_service_supabase()
            .table("commandes")
            .insert({
                "offre_id": offre_id,
                "user_id": user_id,
                "price_paid": price_paid,
            })
            .select("id, token")
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Erreur create_pending_commande: {e}")
        return None

def fulfill_commande(token: str, stripe_session_id: str) -> bool:
    try:
        res = (
            get_service_supabase()
            .table("commandes")
            .update({
                "stripe_session_id": stripe_session_id,
            })
            .eq("token", token)
            .execute()
        )
        return len(res.data) > 0
    except Exception as e:
        logger.error(f"Erreur fulfill_commande: {e}")
        return False