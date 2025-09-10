"""
Adaptateur Stripe: centralise les appels et la configuration Stripe.
"""
import stripe
from typing import Any, Dict, List
from fastapi import Request
try:
    from backend.config import STRIPE_WEBHOOK_SECRET as WEBHOOK_SECRET
except Exception:
    WEBHOOK_SECRET = ""

def require_stripe() -> stripe:
    """
    Retourne le module stripe prêt à l'emploi.
    Si tu dois configurer une clé, tu peux le faire ici via stripe.api_key.
    """
    # Exemple: stripe.api_key = os.getenv("STRIPE_API_KEY") or settings.STRIPE_API_KEY
    return stripe

def create_session(
    *,
    line_items: List[Dict[str, Any]],
    mode: str,
    success_url: str,
    cancel_url: str,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Crée une session de paiement Stripe Checkout et retourne l'objet session (dict-like).
    """
    require_stripe()
    session = stripe.checkout.Session.create(
        line_items=line_items,
        mode=mode,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
        payment_method_types=["card"],
    )
    # stripe retourne un objet; on le traite comme dict-compatible
    return dict(session)

def get_session(session_id: str) -> Dict[str, Any]:
    require_stripe()
    session = stripe.checkout.Session.retrieve(session_id)
    return dict(session)

async def parse_event(request: Request):
    """
    Version attendue par la vue: lit le payload et l'en-tête de signature depuis la requête.
    """
    require_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature") or request.headers.get("Stripe-Signature")
    event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET or "")
    return event