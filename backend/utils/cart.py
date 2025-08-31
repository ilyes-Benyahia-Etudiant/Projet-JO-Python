from typing import List, Dict, Any, Iterable
from uuid import uuid4
from fastapi import HTTPException

from backend.utils.db import fetch_offres_by_ids, insert_commande


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
    # Le router/Stripe les sérialise si besoin (ici on laisse tel quel pour éviter un couplage à JSON)
    # On peut retourner déjà sérialisé si tu préfères; ici c'est cart_json attendu côté stripe_client.
    import json
    return {
        "user_id": user_id,
        "cart": json.dumps(cart_meta)[:4500],
    }


def process_cart_purchase(user_id: str, cart: list[dict], user_token: str | None = None, use_service: bool = False) -> int:
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
                from backend.utils.db import insert_commande_service
                row = insert_commande_service(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid)
            elif user_token:
                from backend.utils.db import insert_commande_with_token
                row = insert_commande_with_token(user_token, user_id, offre_id, token, price_paid)
            else:
                from backend.utils.db import insert_commande
                row = insert_commande(user_id=user_id, offre_id=offre_id, token=token, price_paid=price_paid)
            if row:
                created += 1
    return created