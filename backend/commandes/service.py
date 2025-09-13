from typing import Dict, Any
import logging
from backend.commandes import repository
from backend.commandes.stripe_client import create_session, get_session

logger = logging.getLogger(__name__)

def create_checkout_session_for_offre(offre: Dict[str, Any], user_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
    """
    Crée une commande 'pending' puis une session Stripe pour l'offre donnée.
    """
    pending_commande = repository.create_pending_commande(str(offre["id"]), user_id, float(offre["price"]))
    if not pending_commande:
        raise RuntimeError("Impossible de créer la commande")

    checkout_session = create_session(
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": offre["name"],
                    },
                    "unit_amount": int(float(offre["price"]) * 100),  # centimes
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"commande_token": pending_commande["token"]},
    )
    return checkout_session

def webhook_handle_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Traite l'événement Stripe pour compléter la commande en cas de checkout.session.completed.
    """
    try:
        if (event or {}).get("type") == "checkout.session.completed":
            session = ((event or {}).get("data") or {}).get("object") or {}
            meta = session.get("metadata") or {}
            token = meta.get("commande_token")
            session_id = session.get("id") or ""
            if token:
                repository.fulfill_commande(token, session_id)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("Erreur webhook_handle_event")
        raise

def confirm_checkout(session_id: str) -> Dict[str, Any]:
    """
    Alternative sans webhook: vérifie la session Stripe et confirme la commande via metadata.commande_token
    """
    session = get_session(session_id)
    if (session or {}).get("payment_status") != "paid":
        raise RuntimeError("Paiement non confirmé")
    meta = (session or {}).get("metadata") or {}
    token = meta.get("commande_token")
    if not token:
        raise RuntimeError("Metadata commande_token manquant")
    ok = repository.fulfill_commande(token, session_id)
    return {"status": "ok" if ok else "noop"}