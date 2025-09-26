"""
Logique panier pure (pas de Stripe, pas de DB).
"""
from typing import List, Dict, Any
from fastapi import HTTPException

# module backend.payments.cart
def aggregate_quantities(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Agrège un panier brut [{id, quantity}, ...] en {offre_id: total_quantity}.
    - Ignore les lignes invalides (id vide, quantity <= 0).
    - Soulève HTTPException(400) si aucune ligne valide n’est présente.
    """
    quantities: Dict[str, int] = {}
    for it in items or []:
        offre_id = str(it.get("id") or "").strip()
        qty = int(it.get("quantity") or 0)
        if not offre_id or qty <= 0:
            continue
        quantities[offre_id] = quantities.get(offre_id, 0) + qty
    if not quantities:
        raise HTTPException(status_code=400, detail="Panier invalide")
    return quantities

def _price_from_offer(offer: Dict[str, Any]) -> float:
    try:
        return float(offer.get("price") or 0)
    except Exception:
        return 0.0

def price_from_offer(offer: Dict[str, Any]) -> float:
    """
    Helper public pour récupérer le prix d’une offre (float).
    - Autorise offer.get("price") à être str|float|int.
    - Retourne 0.0 si parsing impossible.
    """
    # Alias public pour éviter d'appeler une fonction "privée" depuis le service
    return _price_from_offer(offer)

def to_line_items(offers_by_id: Dict[str, Dict[str, Any]], quantities: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Construit les line_items Stripe à partir des offres et quantités.
    - Si 'price_id' est présent dans l'offre, utilise {"price": "<price_id>"}.
    - Sinon, construit 'price_data' avec unit_amount (en centimes) et product_data.name.
    - Ignore les offres introuvables ou à quantité/prix non valides.
    - Soulève HTTPException(400) si aucune ligne valide n’est construite.
    """
    line_items: List[Dict[str, Any]] = []
    for offre_id, qty in quantities.items():
        offer = offers_by_id.get(ofre_id := offre_id)
        if not offer or qty <= 0:
            continue

        price_id = offer.get("price_id")
        if price_id:
            line_items.append({"price": price_id, "quantity": qty})
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
    """
    Sérialise les métadonnées Stripe associées à la session.
    - user_id: identifiant de l’utilisateur propriétaire du panier.
    - quantities: dict agrégé {offre_id: qty}.
    - cart: JSON tronqué à ~4500 chars pour respecter les limites Stripe.
    """
    import json
    cart_meta = [{"id": oid, "quantity": qty} for oid, qty in quantities.items()]
    return {
        "user_id": user_id,
        "cart": json.dumps(cart_meta)[:4500],
    }