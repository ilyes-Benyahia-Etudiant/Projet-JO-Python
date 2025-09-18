from typing import Any, Dict
from .repository import get_user_orders, get_offers

def get_user_dashboard(user_id: str) -> Dict[str, Any]:
    # Charger uniquement les offres pour la page /session
    offres = get_offers()
    return {"offres": offres}