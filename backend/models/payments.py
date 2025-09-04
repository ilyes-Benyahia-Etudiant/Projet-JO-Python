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

def extract_metadata(event: Dict[str, Any]) -> (str, list):
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

# Cart helpers (migrés)
def aggregate_quantities(items: List[Dict[str, Any]]) -> Dict[str, int]:
    if not items:
        raise HTTPException(status_code=400, detail="Panier vide")
    quantities: Dict[str, int] = {}
    for it in items:
        offre_id = str(it.get("id") or "").strip()
        qty = int(it.get("quantity") or 0)
        if not offre_id or qty <= 0:
            continue
        quantities[offre_id] = quantities.get(offre_id, 0) + qty
    if not quantities:
        raise HTTPException(status_code=400, detail="Panier invalide")
    return quantities

def get_offers_map(ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    offers = fetch_offres_by_ids(list(ids))
    return {str(o.get("id")): o for o in offers}

def _price_from_offer(offer: Dict[str, Any]) -> float:
    try:
        return float(offer.get("price") or 0)
    except Exception:
        return 0.0

def to_line_items(offers_by_id: Dict[str, Dict[str, Any]], quantities: Dict[str, int]) -> List[Dict[str, Any]]:
    line_items: List[Dict[str, Any]] = []
    for offre_id, qty in quantities.items():
        offer = offers_by_id.get(offre_id)
        if not offer:
            continue
        unit_price = _price_from_offer(offer)
        if unit_price <= 0:
            continue
        unit_amount = int(round(unit_price * 100))
        title = offer.get("title") or "Article"
        line_items.append({
            "quantity": qty,
            "price_data": {
                "currency": "eur",
                "unit_amount": unit_amount,
                "product_data": {"name": title},
            },
        })
    if not line_items:
        raise HTTPException(status_code=400, detail="Aucun article valide")
    return line_items

def make_metadata(user_id: str, quantities: Dict[str, int]) -> Dict[str, str]:
    cart_meta = [{"id": oid, "quantity": qty} for oid, qty in quantities.items()]
    return {
        "user_id": user_id,
        "cart": json.dumps(cart_meta)[:4500],
    }

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