from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests
from urllib.parse import quote

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def normalize_status_from_payload(payload: dict):
    # Retourne l'un de: "Invalid" | "Scanned" | "Validated" | "AlreadyValidated"
    if not payload:
        return "Invalid"

    # Cas explicite par code HTTP côté appelant (on laisse l'appelant décider)
    status = payload.get("status")
    ticket = payload.get("ticket")
    validation = payload.get("validation")

    # Si l'API renvoie 'validated'/'already_validated'
    if isinstance(status, str):
        s = status.lower()
        if s == "validated":
            return "Validated"
        if s == "already_validated":
            return "AlreadyValidated"

    # Si un ticket existe mais pas de validation => prêt à valider
    if ticket and not validation:
        return "Scanned"

    # Si un ticket et une validation existent => déjà validé
    if ticket and validation:
        return "AlreadyValidated"

    return "Invalid"

@router.get("/admin/scan", response_class=HTMLResponse)
def get_admin_scan(request: Request, token: str | None = Query(default=None)):
    context = {
        "request": request,
        "token": token or "",
        "status": None,
        "message": None,
        "ticket": None,
        "validation": None,
    }

    if not token:
        return templates.TemplateResponse("admin-scan.html", context)

    base_url = str(request.base_url).rstrip("/")
    safe_token = quote(token, safe="")
    url = f"{base_url}/api/v1/validation/ticket/{safe_token}"

    try:
        r = requests.get(url, cookies=request.cookies, timeout=10)
        if r.status_code == 404:
            context["status"] = "Invalid"
            context["message"] = "Billet inconnu"
            return templates.TemplateResponse("admin-scan.html", context)

        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    except Exception as e:
        context["status"] = "Invalid"
        context["message"] = f"Erreur réseau: {e}"
        return templates.TemplateResponse("admin-scan.html", context)

    context["ticket"] = data.get("ticket")
    context["validation"] = data.get("validation")
    context["message"] = data.get("message")
    context["status"] = normalize_status_from_payload(data)

    return templates.TemplateResponse("admin-scan.html", context)

@router.post("/admin/scan/validate")
def post_admin_validate(request: Request, token: str = Form(...)):
    base_url = str(request.base_url).rstrip("/")
    url = f"{base_url}/api/v1/validation/scan"

    headers = {"Content-Type": "application/json"}
    csrf = request.cookies.get("csrf_token") or request.cookies.get("csrftoken")
    if csrf:
        headers["X-CSRF-Token"] = csrf

    try:
        r = requests.post(url, json={"token": token}, cookies=request.cookies, headers=headers, timeout=10)
        # Redirige vers GET /admin/scan?token=... pour un rendu propre après POST (PRG)
        return RedirectResponse(url=f"/admin/scan?token={token}", status_code=303)
    except Exception:
        return RedirectResponse(url=f"/admin/scan?token={token}", status_code=303)