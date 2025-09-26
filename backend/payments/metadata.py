"""
Sérialisation/désérialisation des métadonnées Stripe (user_id, cart).
"""
import json
from typing import Any, Dict, List, Tuple

# module backend.payments.metadata
def extract_metadata(event: Dict[str, Any]) -> Tuple[str | None, List[Dict[str, Any]]]:
    """
    Extrait (user_id, cart) depuis un event Stripe (webhook).
    - Attend event.data.object.metadata.{user_id, cart}
    - cart est un JSON sérialisé [{"id": "<offre_id>", "quantity": <int>}]
    - Tolérant aux erreurs: retourne (user_id, []) si parsing JSON échoue.
    """
    data_obj = (event or {}).get("data", {}).get("object", {}) if isinstance(event, dict) else {}
    meta = data_obj.get("metadata") or {}
    user_id = meta.get("user_id")
    cart_json = meta.get("cart")
    try:
        cart = json.loads(cart_json) if cart_json else []
    except Exception:
        cart = []
    return user_id, cart

def extract_metadata_from_session(session: Dict[str, Any]) -> Tuple[str | None, List[Dict[str, Any]]]:
    """
    Extrait (user_id, cart) depuis une session Stripe Checkout (lecture directe).
    - Attend session["metadata"] = {user_id, cart(JSON)}
    - Tolérant aux erreurs: retourne (user_id, []) si parsing JSON échoue.
    """
    meta = (session or {}).get("metadata", {}) if isinstance(session, dict) else {}
    user_id = meta.get("user_id")
    cart_json = meta.get("cart")
    try:
        cart = json.loads(cart_json) if cart_json else []
    except Exception:
        cart = []
    return user_id, cart