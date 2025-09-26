"""
Routes web pour l'interface Admin de scan/validation.
- GET /admin/scan: page HTML avec caméra, saisie token, et état unifié du billet.
- POST /admin/scan/validate: valide un billet et renvoie une réponse JSON.
- Normalisation d’état (UI): Invalid | Scanned | Validated | AlreadyValidated | Error.
"""
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import requests
from urllib.parse import quote
from backend.utils.csrf import get_csrf_token
from backend.utils.jinja import templates
from backend.validation.schemas import normalize_status_from_payload
from backend.validation.services import validate_ticket_service
from backend.validation.schemas import TicketStatus, TicketValidationRequest, TicketValidationResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def normalize_status_from_payload(payload: dict):
    """
    Convertit la réponse API en statut UI unifié.
    - Entrée: payload JSON renvoyé par l'API de validation
    - Sorties: "Invalid" | "Scanned" | "Validated" | "AlreadyValidated"
    - Logique:
      - status == validated => Validated
      - status == already_validated => AlreadyValidated
      - ticket présent sans validation => Scanned
      - sinon => Invalid
    """
    # Retourne l'un de: "Invalid" | "Scanned" | "Validated" | "AlreadyValidated"
    if not payload:
        return "Invalid"
    status = payload.get("status")
    ticket = payload.get("ticket")
    validation = payload.get("validation")
    if isinstance(status, str):
        s = status.lower()
        if s == "validated":
            return "Validated"
        if s == "already_validated":
            return "AlreadyValidated"
    if ticket and not validation:
        return "Scanned"
    if ticket and validation:
        return "AlreadyValidated"
    return "Invalid"

@router.get("/admin/scan", response_class=HTMLResponse)
async def get_admin_scan(request: Request, token: str | None = Query(default=None)):
    """
    Affiche la page de scan Admin.
    - Si token est fourni, interroge l’API pour déterminer l’état du billet et prépare le contexte.
    - Gère les erreurs réseau en affichant "Erreur de communication API.".
    - Ajoute le jeton CSRF au contexte et désactive le cache.
    """
    csrf_token_value = get_csrf_token(request)
    context = {
        "request": request, "csrf_token": csrf_token_value, "token": token or "",
        "status": None, "message": None, "ticket": None,
    }

    if token:
        try:
            api_url = request.url_for("get_ticket_by_token_api", token=token)
            r = requests.get(str(api_url), cookies=request.cookies, headers={"Accept": "application/json"}, timeout=5)
            data = r.json() if r.status_code == 200 else {}
            status = normalize_status_from_payload(data)
            ticket = data.get("ticket")
            message = data.get("message")

            # Messages explicites selon le statut
            if status == "Scanned":
                message = "Prêt à valider"
            elif status == "AlreadyValidated":
                message = "Déjà validé"
            elif status == "Invalid":
                message = "Billet introuvable"

            context.update({"ticket": ticket, "status": status, "message": message})
        except requests.RequestException:
            context.update({"status": "Error", "message": "Erreur de communication API."})

    resp = templates.TemplateResponse("admin-scan.html", context=context)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

@router.post("/admin/scan/validate")
async def post_admin_validate(request: Request, token: str = Form(...)):
    """
    Valide un billet côté Admin et renvoie une réponse JSON.
    - Utilise validate_ticket_service(...).
    - Réponses:
      - 200: {"status": "validated", "message": "..."} si succès
      - 400: {"status": "error", "message": "..."} si non validé
      - 500: {"status": "error", "message": "Erreur interne du serveur: ..."} en cas d'exception
    """
    try:
        validation_payload = TicketValidationRequest(token=token)
        response_data = await validate_ticket_service(validation_payload)
        if response_data.status == TicketStatus.VALIDATED:
            return JSONResponse(content={"status": "validated", "message": "Billet Validé avec succès !"})
        else:
            return JSONResponse(status_code=400, content={"status": "error", "message": response_data.message})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Erreur interne du serveur: {e}"})