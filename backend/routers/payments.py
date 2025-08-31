# Haut du fichier (imports + router)
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from backend.utils.security import require_user, COOKIE_NAME
from backend.utils import cart as cart_utils
from backend.utils import stripe_client as stripe_utils

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

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

# _base_url reste local (pratique pour construire les URLs de retour)
def _base_url(request: Request) -> str:
    scheme = request.url.scheme
    host = request.headers.get("host") or request.url.netloc
    return f"{scheme}://{host}"

# Endpoint Checkout
@router.post("/checkout")
async def create_checkout_session(request: Request, user: dict = Depends(require_user)):
    """
    Body:
    { "items": [ { "id": "<offre_id>", "quantity": 2 }, ... ] }
    """
    stripe_utils.require_stripe()
    body = await request.json()
    quantities = cart_utils.aggregate_quantities(body.get("items") or [])
    offers_by_id = cart_utils.get_offers_map(quantities.keys())
    line_items = cart_utils.to_line_items(offers_by_id, quantities)
    metadata = cart_utils.make_metadata(user_id=user.get("id", ""), quantities=quantities)
    session = stripe_utils.create_session(_base_url(request), line_items, metadata)
    return JSONResponse({"url": session.url})

# Endpoint Webhook
@router.post("/webhook")
async def stripe_webhook(request: Request):
    stripe_utils.require_stripe()
    event: Dict[str, Any] = await stripe_utils.parse_event(request)
    if event.get("type") == "checkout.session.completed":
        user_id, cart_list = stripe_utils.extract_metadata(event)
        # Utiliser la clé service pour bypass RLS côté webhook (backend-initiated)
        created = cart_utils.process_cart_purchase(user_id, cart_list, use_service=True)
        logger.info("payments.webhook created=%s items=%s user_id=%s", created, len(cart_list or []), user_id)
        return JSONResponse({"status": "ok", "created": created})
    return JSONResponse({"status": "ignored"})

@router.get("/confirm")
async def confirm_checkout(request: Request, session_id: str, user: dict = Depends(require_user)):
    """
    Confirme une session Checkout sans webhook:
    - Récupère la session Stripe par session_id
    - Vérifie que le paiement est 'paid'
    - Lit le cart depuis metadata et crée les billets/commandes
    - Vérifie que la session appartient à l'utilisateur courant
    """
    stripe_utils.require_stripe()
    session = stripe_utils.get_session(session_id)

    payment_status = session.get("payment_status") or ""
    if payment_status != "paid":
        raise HTTPException(status_code=400, detail=f"Paiement non confirmé (payment_status={payment_status})")

    meta_user_id, cart_list = stripe_utils.extract_metadata_from_session(session)

    if meta_user_id and meta_user_id != user.get("id"):
        raise HTTPException(status_code=403, detail="Session appartenant à un autre utilisateur")

    # Récupère le JWT utilisateur depuis le cookie pour des INSERT compatibles RLS
    user_token = request.cookies.get(COOKIE_NAME)

    created = cart_utils.process_cart_purchase(user.get("id"), cart_list, user_token=user_token)
    logger.info("payments.confirm created=%s items=%s user_id=%s session_id=%s", created, len(cart_list or []), user.get("id"), session_id)
    return JSONResponse({"status": "ok", "created": created})

@router.post("/confirm")
async def confirm_checkout_post(request: Request, user: dict = Depends(require_user)):
    """
    Variante POST: accepte session_id en query ou en JSON body.
    """
    session_id = request.query_params.get("session_id")
    if not session_id:
        try:
            body = await request.json()
            session_id = (body or {}).get("session_id")
        except Exception:
            session_id = None
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id manquant")
    return await confirm_checkout(request, session_id=session_id, user=user)