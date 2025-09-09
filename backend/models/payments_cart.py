from typing import List, Dict, Any, Iterable
from fastapi import HTTPException

from .db import fetch_offres_by_ids

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
    import json
    cart_meta = [{"id": oid, "quantity": qty} for oid, qty in quantities.items()]
    return {
        "user_id": user_id,
        "cart": json.dumps(cart_meta)[:4500],
    }