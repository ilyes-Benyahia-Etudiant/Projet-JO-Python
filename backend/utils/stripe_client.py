from typing import Dict, Any, List
import json
from fastapi import HTTPException, Request

from backend.config import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    CHECKOUT_SUCCESS_PATH,
    CHECKOUT_CANCEL_PATH,
)

try:
    import stripe
except ImportError:
    stripe = None


def require_stripe():
    if stripe is None:
        raise HTTPException(status_code=500, detail="Stripe non installé (pip install stripe).")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY manquant")
    stripe.api_key = STRIPE_SECRET_KEY


def create_session(base_url: str, line_items: List[Dict[str, Any]], metadata: Dict[str, str]):
    sep = "&" if "?" in CHECKOUT_SUCCESS_PATH else "?"
    return stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=f"{base_url}{CHECKOUT_SUCCESS_PATH}{sep}session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}{CHECKOUT_CANCEL_PATH}",
        metadata=metadata,
    )

async def parse_event(request: Request) -> Dict[str, Any]:
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    if not STRIPE_WEBHOOK_SECRET:
        # Dev only (non sécurisé)
        return json.loads(payload.decode("utf-8"))
    try:
        return stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook invalid: {e}")


def extract_metadata(event: Dict[str, Any]) -> (str, list):
    """
    Renvoie (user_id, cart_list) extraits de l'événement Stripe.
    """
    session = (event.get("data") or {}).get("object") or {}
    metadata = session.get("metadata") or {}
    user_id = metadata.get("user_id") or ""
    try:
        cart = json.loads(metadata.get("cart") or "[]")
    except Exception:
        cart = []
    return user_id, cart

def get_session(session_id: str) -> Dict[str, Any]:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id manquant")
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Session introuvable: {e}")

def extract_metadata_from_session(session: Dict[str, Any]) -> (str, list):
    metadata = session.get("metadata") or {}
    user_id = metadata.get("user_id") or ""
    try:
        cart = json.loads(metadata.get("cart") or "[]")
    except Exception:
        cart = []
    return user_id, cart