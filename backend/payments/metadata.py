"""
Sérialisation/désérialisation des métadonnées Stripe (user_id, cart).
"""
import json
from typing import Any, Dict, List, Tuple

def extract_metadata(event: Dict[str, Any]) -> Tuple[str | None, List[Dict[str, Any]]]:
    """
    Compat tests: retourne (user_id, cart)
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
    Compat tests: retourne (user_id, cart)
    """
    meta = (session or {}).get("metadata", {}) if isinstance(session, dict) else {}
    user_id = meta.get("user_id")
    cart_json = meta.get("cart")
    try:
        cart = json.loads(cart_json) if cart_json else []
    except Exception:
        cart = []
    return user_id, cart