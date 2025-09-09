from typing import List, Dict, Any, Iterable, Optional
import json
from uuid import uuid4
from fastapi import HTTPException, Request

from backend.config import (
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    CHECKOUT_SUCCESS_PATH,
    CHECKOUT_CANCEL_PATH,
)
from backend.models.db import (
    fetch_offres_by_ids,
    insert_commande,
    insert_commande_with_token,
    insert_commande_service,
)

try:
    import stripe
except ImportError:
    stripe = None

# Stripe helpers
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

def _parse_metadata_dict(metadata: Dict[str, Any]) -> (str, list):
    user_id = str(metadata.get("user_id") or "")
    try:
        cart = json.loads(metadata.get("cart") or "[]")
    except Exception:
        cart = []
    return user_id, cart

def extract_metadata(event: Dict[str, Any]) -> (str, list):
    session = (event.get("data") or {}).get("object") or {}
    metadata = session.get("metadata") or {}
    return _parse_metadata_dict(metadata)

def get_session(session_id: str) -> Dict[str, Any]:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id manquant")
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Session introuvable: {e}")

def extract_metadata_from_session(session: Dict[str, Any]) -> (str, list):
    metadata = session.get("metadata") or {}
    return _parse_metadata_dict(metadata)

# Cart helpers (migrés)
# Import des helpers panier factorisés (compatibilité avec anciens imports)
from .payments_cart import (
    aggregate_quantities,
    get_offers_map,
    _price_from_offer,
    make_metadata,
)
# RÉINTRODUIT: wrapper local pour rester patchable par les tests
def get_offers_map(ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    offers = fetch_offres_by_ids(list(ids))
    return {str(o.get("id")): o for o in offers}

def process_cart_purchase(
    user_id: str,
    cart: list[dict],
    user_token: Optional[str] = None,
    use_service: bool = False
) -> int:
    """
    Insère une ligne 'commandes' par ticket acheté.
    cart: [{ "id": "<offre_id>", "quantity": <int> }, ...]
    """
    ids = [str(x.get("id") or "") for x in cart if x.get("id")]
    offers_by_id = get_offers_map(ids)

    created = 0
    for entry in cart:
        offre_id = str(entry.get("id") or "")
        qty = int(entry.get("quantity") or 0)
        if not offre_id or qty <= 0:
            continue
        offer = offers_by_id.get(offre_id)
        if not offer:
            continue
        price = _price_from_offer(offer)
        if price <= 0:
            continue
        price_paid = f"{price:.2f}"
        for _ in range(qty):
            token = str(uuid4())
            if use_service:
                row = insert_commande_service(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid)
            elif user_token:
                row = insert_commande_with_token(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid, user_token=user_token)
            else:
                row = insert_commande(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid)
            if row:
                created += 1
    return created

def confirm_session_by_id(session_id: str, current_user_id: str, user_token: Optional[str]) -> int:
    """
    Récupère la session Stripe, vérifie l'état du paiement et la propriété,
    puis insère les commandes et renvoie le nombre créé.
    """
    session = get_session(session_id)

    payment_status = session.get("payment_status") or ""
    if payment_status != "paid":
        raise HTTPException(status_code=400, detail=f"Paiement non confirmé (payment_status={payment_status})")

    meta_user_id, cart_list = extract_metadata_from_session(session)
    if meta_user_id and meta_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Session appartenant à un autre utilisateur")

    created = process_cart_purchase(current_user_id, cart_list, user_token=user_token)
    return created