from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from backend.utils.security import require_user
from backend.utils.rate_limit import optional_rate_limit
# Module-level (imports)
from backend.payments.stripe_client import parse_event
from backend.commandes import service as commandes_service
# from backend.models import offres as offres_model
from backend.offres import repository as offres_model

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/commandes", tags=["Commandes API"])


@router.post("/create-checkout-session", dependencies=[Depends(optional_rate_limit(times=10, seconds=60))])
async def api_create_checkout_session(request: Request, user: dict = Depends(require_user)):
    """
    Crée une session de paiement Stripe pour une offre.
    """
    try:
        data = await request.json()
        offre_id = data.get("offre_id")
        offre = offres_model.get_offre(offre_id)

        if not offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")

        user_id = user.get("id")
        success_url = str(request.url_for("mes_billets_page"))
        cancel_url = str(request.url_for("billeterie_page"))

        checkout_session = commandes_service.create_checkout_session_for_offre(
            offre, user_id, success_url, cancel_url
        )
        return JSONResponse({"sessionId": checkout_session.get("id")})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur api_create_checkout_session")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/stripe", include_in_schema=False)
async def webhook_stripe(request: Request):
    """
    Webhook Stripe: confirme la commande lorsque checkout.session.completed est reçu.
    """
    try:
        event = await parse_event(request)
        result = commandes_service.webhook_handle_event(event)
        return result
    except Exception as e:
        logger.exception("Erreur webhook_stripe")
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook payload")


@router.get("/confirm")
async def confirm_checkout(session_id: str):
    """
    Alternative sans webhook: vérifie la session Stripe et confirme la commande via metadata.commande_token
    """
    try:
        return commandes_service.confirm_checkout(session_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Erreur confirm_checkout")
        raise HTTPException(status_code=400, detail="Session introuvable ou invalide")
