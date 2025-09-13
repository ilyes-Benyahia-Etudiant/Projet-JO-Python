"""
Cas d'usage 'payments': orchestre repository, cart, stripe, metadata.
"""
from typing import Optional, Dict, Any, List
from uuid import uuid4
from fastapi import HTTPException

from . import repository
from . import cart
from . import stripe_client
from . import metadata as meta
from typing import Any, Dict, List

from . import cart as cart_logic
from . import stripe_client
from .repository import get_offers_map
from .metadata import extract_metadata_from_session

def process_cart_purchase(
    *,
    user_id: str,
    cart: List[Dict[str, Any]],
    success_url: str,
    cancel_url: str,
) -> Dict[str, Any]:
    """
    Prépare la session Stripe à partir d'un user_id et d'un panier.
    success_url et cancel_url doivent être fournis par l'appelant (vue).
    """
    quantities = cart_logic.aggregate_quantities(cart)
    offers = get_offers_map(list(quantities.keys()))
    line_items = cart_logic.to_line_items(offers, quantities)
    metadata = cart_logic.make_metadata(user_id, quantities)
    session = stripe_client.create_session(
        line_items=line_items,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    return session

def confirm_session_by_id(session_id: str) -> Dict[str, Any]:
    """
    Récupère la session stripe et ses métadonnées (user_id, cart).
    """
    session = stripe_client.get_session(session_id)
    meta = extract_metadata_from_session(session)
    return {"session": session, "metadata": meta}

def process_cart_purchase(
    user_id: str,
    cart_list: List[Dict[str, Any]],
    user_token: Optional[str] = None,
    use_service: bool = False
) -> int:
    """
    Insère une ligne 'commandes' par ticket acheté.
    cart_list: [{ "id": "<offre_id>", "quantity": <int> }, ...]
    """
    ids = [str(x.get("id") or "") for x in cart_list if x.get("id")]
    offers_by_id = get_offers_map(ids)

    created = 0
    for entry in cart_list:
        offre_id = str(entry.get("id") or "")
        qty = int(entry.get("quantity") or 0)
        if not offre_id or qty <= 0:
            continue
        offer = offers_by_id.get(offre_id)
        if not offer:
            continue
        price = cart.price_from_offer(offer)
        if price <= 0:
            continue
        price_paid = f"{price:.2f}"
        for _ in range(qty):
            token = str(uuid4())
            if use_service:
                row = repository.insert_commande_service(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid)
            elif user_token:
                row = repository.insert_commande_with_token(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid, user_token=user_token)
            else:
                row = repository.insert_commande(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid)
            if row:
                created += 1
    return created

def confirm_session_by_id(session_id: str, current_user_id: str, user_token: Optional[str]) -> int:
    """
    Récupère la session Stripe, vérifie l'état du paiement et la propriété,
    puis insère les commandes et renvoie le nombre créé.
    """
    stripe_client.require_stripe()
    session = stripe_client.get_session(session_id)

    payment_status = session.get("payment_status") or ""
    if payment_status != "paid":
        raise HTTPException(status_code=400, detail=f"Paiement non confirmé (payment_status={payment_status})")

    meta_user_id, cart_list = meta.extract_metadata_from_session(session)
    if meta_user_id and meta_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Session appartenant à un autre utilisateur")

    created = process_cart_purchase(current_user_id, cart_list, user_token=user_token)
    return created