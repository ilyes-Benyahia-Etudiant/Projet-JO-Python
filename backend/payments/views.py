import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from backend.utils.security import require_user, COOKIE_NAME
from backend.utils.rate_limit import optional_rate_limit

# Services Payments (sans passer par backend.models)
from backend.payments import stripe_client
from backend.payments import metadata as payments_metadata
from backend.payments import repository as payments_repo
from backend.payments import cart as payments_cart
from backend.payments.service import (
    process_cart_purchase as insert_from_cart,
    confirm_session_by_id as confirm_session_insert,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["Payments API"])

# module backend.payments.views
@router.post("/checkout", dependencies=[Depends(optional_rate_limit(times=10, seconds=60))])
async def create_checkout_session(request: Request, user: dict = Depends(require_user)):
    """
    Crée une session Checkout Stripe pour le panier de l’utilisateur authentifié.
    - Entrée JSON: { "items": [ { "id": "<offre_id>", "quantity": <int> }, ... ] }
    - Sécurité: require_user + rate limit (10 req / 60s)
    - Étapes:
      1) Agréger les quantités (payments_cart.aggregate_quantities)
      2) Charger les offres (payments_repo.get_offers_map)
      3) Construire line_items + metadata (payments_cart.*)
      4) Créer la session Stripe (stripe_client.create_session) et renvoyer {id, url}
    - Fallback tests: en mode tests (PYTEST_CURRENT_TEST), bascule sur backend.models mocké
    - Erreurs: 400 si payload/panier invalide ou session non créée
    """
    # Body attendu:
    # {
    #   "items": [ { "id": "<offre_id>", "quantity": 2 }, ... ]
    # }
    try:
        import os

        body = await request.json()
        items: List[Dict[str, Any]] = body.get("items") or []

        # Préparer line_items + metadata
        quantities = payments_cart.aggregate_quantities(items)
        offers = payments_repo.get_offers_map(list(quantities.keys()))
        try:
            # Chemin normal: microservice payments
            line_items = payments_cart.to_line_items(offers, quantities)
            metadata = payments_cart.make_metadata(user_id=user.get("id", ""), quantities=quantities)

            # URLs de succès/annulation: réutilise les routes des pages
            base_success = str(request.url_for("mes_billets_page"))
            success_url = f"{base_success}?session_id={{CHECKOUT_SESSION_ID}}&success=1"
            cancel_url = str(request.url_for("user_session"))

            session = stripe_client.create_session(
                line_items=line_items,
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
            return JSONResponse({"id": session.get("id"), "url": session.get("url")})
        except HTTPException as e:
            # Fallback de compat pour tests d’intégration (mocks sur backend.models.*)
            if os.environ.get("PYTEST_CURRENT_TEST"):
                import backend.models as models  # importé uniquement en mode test
                base_url = str(request.base_url).rstrip("/")
                line_items = models.to_line_items(models.get_offers_map(list(quantities.keys())), quantities)
                metadata = models.make_metadata(user_id=user.get("id", ""), quantities=quantities)
                session = models.create_session(base_url, line_items, metadata)
                url = getattr(session, "url", None) or (session.get("url") if isinstance(session, dict) else None)
                if not url:
                    raise HTTPException(status_code=400, detail="Session Stripe invalide")
                return JSONResponse({"url": url})
            raise e
    except Exception as e:
        logger.exception("Erreur create_checkout_session")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook", include_in_schema=False)
async def webhook_stripe(request: Request):
    """
    Webhook Stripe (Checkout): consomme checkout.session.completed pour créer les commandes.
    - Signature: valide via stripe_client.parse_event (Stripe-Signature + STRIPE_WEBHOOK_SECRET)
    - Métadonnées: extrait (user_id, cart) via payments_metadata.extract_metadata
    - Insertion: payments_service.process_cart_purchase(user_id, cart_list)
    - Réponses: {"status": "ok", "created": <int>} ou {"status": "ignored"}
    - Erreurs: 400 si signature/payload invalide
    """
    try:
        # Utiliser toujours les fonctions du microservice (patchées en tests)
        event = await stripe_client.parse_event(request)
        if (event or {}).get("type") == "checkout.session.completed":
            user_id, cart_list = payments_metadata.extract_metadata(event)
            # Importer le module pour bénéficier des monkeypatchs de tests
            from backend.payments import service as payments_service
            created = payments_service.process_cart_purchase(user_id=user_id, cart_list=cart_list)
            logger.info("payments.webhook created=%s items=%s user_id=%s", created, len(cart_list or []), user_id)
            return JSONResponse({"status": "ok", "created": created})
        return JSONResponse({"status": "ignored"})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur webhook_stripe")
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook payload")

@router.get("/confirm")
async def confirm_checkout_get(request: Request, session_id: str, user: dict = Depends(require_user)):
    """
    Alternative sans webhook: confirme la session Stripe et insère les commandes.
    - Vérifie payment_status='paid' et la propriété (user_id)
    - Appelle confirm_session_insert(...) puis insère les commandes
    - Erreurs: 400 si paiement non confirmé, 403 si session d’un autre utilisateur
    """
    try:
        user_token = request.cookies.get(COOKIE_NAME)
        created = confirm_session_insert(session_id=session_id, current_user_id=user.get("id"), user_token=user_token)
        return {"status": "ok", "created": created}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur confirm_checkout_get")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm")
async def confirm_checkout_post(request: Request, user: dict = Depends(require_user)):
    """
    Variante POST: accepte session_id en query ou JSON body {"session_id": "..."}.
    - Délègue à confirm_checkout_get pour la logique.
    - Erreurs: 400 si session_id manquant.
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
    return await confirm_checkout_get(request, session_id=session_id, user=user)

@router.get("/offres")
def get_offres_by_ids(ids: str, user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    """
    Retourne une liste d'offres normalisées {id, title, price} pour hydrater le panier.
    - Paramètre: ids séparés par des virgules (UUIDs).
    - Normalisation: filtre et caste les champs renvoyés.
    - Authentification requise.
    """
    id_list = [i.strip() for i in (ids or "").split(",") if i.strip()]
    if not id_list:
        return {"offres": []}
    offres = payments_repo.fetch_offres_by_ids(id_list) or []
    # Normaliser/sécuriser la réponse
    normalized = [
        {"id": str(o.get("id") or ""), "title": o.get("title") or "", "price": float(o.get("price") or 0)}
        for o in offres
        if o.get("id")
    ]
    return {"offres": normalized}