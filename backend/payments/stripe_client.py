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

# module backend.payments.stripe_client
def require_stripe() -> stripe:
    """
    Prépare et retourne le module stripe prêt à l’emploi.
    - Configure stripe.api_key via STRIPE_SECRET_KEY si disponible.
    - En absence de clé, les appels Stripe échoueront côté SDK (ex: No API key provided).
    """
    # Exemple: stripe.api_key = os.getenv("STRIPE_API_KEY") or settings.STRIPE_API_KEY
    try:
        from backend.config import STRIPE_SECRET_KEY
        if STRIPE_SECRET_KEY:
            stripe.api_key = STRIPE_SECRET_KEY
    except Exception:
        # Pas de clé => les appels Stripe échoueront (ex: No API key provided)
        pass
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
    Crée une session Stripe Checkout.
    - line_items: lignes Stripe (price/quantity ou price_data)
    - mode: généralement "payment"
    - success_url / cancel_url: URLs de redirection
    - metadata: ex {"user_id": "...", "cart": "[...]"}
    Retour: dict session (ex: {"id": "cs_test_...", "url": "https://..."})
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
    """
    Récupère une session Stripe Checkout par son identifiant.
    Retour: dict session incluant "id", "payment_status", "metadata", etc.
    """
    require_stripe()
    session = stripe.checkout.Session.retrieve(session_id)
    return dict(session)

async def parse_event(request: Request):
    """
    Parse et valide un événement Stripe signé (webhook).
    - Lit le body brut + en-tête Stripe-Signature
    - Valide la signature via Webhook.construct_event (STRIPE_WEBHOOK_SECRET)
    Retour: l’objet event si la signature est valide.
    """
    require_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature") or request.headers.get("Stripe-Signature")
    event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET or "")
    return event