from typing import Any, Dict
from .repository import get_user_orders, get_offers

def get_user_dashboard(user_id: str) -> Dict[str, Any]:
    offres = get_offers()
    commandes = get_user_orders(user_id)
    return {"offres": offres, "commandes": commandes}