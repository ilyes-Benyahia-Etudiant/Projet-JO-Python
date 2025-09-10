# Haut du fichier (imports + router)
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from backend.utils.security import require_user, COOKIE_NAME
from backend import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])

def _base_url(request: Request) -> str:
    # Construit la base d'URL (ex: http://testserver) sans slash final
    return str(request.base_url).rstrip("/")

@router.post("/checkout")
async def create_checkout_session(request: Request, user: dict = Depends(require_user)):
    """
    Body:
    { "items": [ { "id": "<offre_id>", "quantity": 2 }, ... ] }
    """
    models.require_stripe()
    body = await request.json()
    quantities = models.aggregate_quantities(body.get("items") or [])
    offers_by_id = models.get_offers_map(quantities.keys())
    line_items = models.to_line_items(offers_by_id, quantities)
    meta = models.make_metadata(user_id=user.get("id", ""), quantities=quantities)
    session = models.create_session(_base_url(request), line_items, meta)
    return JSONResponse({"url": session.url})

@router.post("/webhook")
async def stripe_webhook(request: Request):
    models.require_stripe()
    event: Dict[str, Any] = await models.parse_event(request)
    if event.get("type") == "checkout.session.completed":
        user_id, cart_list = models.extract_metadata(event)
        created = models.process_cart_purchase(user_id, cart_list)
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
    models.require_stripe()
    user_token = request.cookies.get(COOKIE_NAME)
    created = models.confirm_session_by_id(session_id, user.get("id"), user_token)
    logger.info("payments.confirm created=%s user_id=%s session_id=%s", created, user.get("id"), session_id)
    return JSONResponse({"status": "ok", "created": created})

# Assure-toi que ce décorateur n’est PAS indenté (colonne 0)
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