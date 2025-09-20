from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.utils.security import require_admin
from backend.evenements import repository as evenements_repository
from fastapi import APIRouter
from typing import List, Dict, Any
from backend.infra.supabase_client import get_supabase

router = APIRouter(prefix="/api/v1/evenements", tags=["Evenements API"])

@router.get("/")
def list_evenements():
    items = evenements_repository.list_evenements()
    return JSONResponse({"items": items})

@router.get("/{evenement_id}")
def get_evenement(evenement_id: str):
    item = evenements_repository.get_evenement(evenement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Evenement introuvable")
    return JSONResponse(item)

@router.post("/", dependencies=[Depends(require_admin)])
async def create_evenement(request: Request):
    body: Dict[str, Any] = await request.json()
    data = {
        "type_evenement": (body.get("type_evenement") or "").strip(),
        "nom_evenement": (body.get("nom_evenement") or "").strip(),
        "lieu": (body.get("lieu") or "").strip(),
        "date_evenement": (body.get("date_evenement") or "").strip(),
    }
    if not data["type_evenement"] or not data["nom_evenement"] or not data["lieu"] or not data["date_evenement"]:
        raise HTTPException(status_code=400, detail="Champs requis manquants")
    created = evenements_repository.create_evenement(data)
    if not created:
        raise HTTPException(status_code=400, detail="Echec de création")
    return JSONResponse(created)

@router.put("/{evenement_id}", dependencies=[Depends(require_admin)])
async def update_evenement(evenement_id: str, request: Request):
    body: Dict[str, Any] = await request.json()
    data: Dict[str, Any] = {}
    for k in ("type_evenement", "nom_evenement", "lieu", "date_evenement"):
        if k in body and body.get(k) is not None:
            data[k] = (body.get(k) or "").strip()
    if not data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    updated = evenements_repository.update_evenement(evenement_id, data)
    if not updated:
        raise HTTPException(status_code=400, detail="Echec de mise à jour")
    return JSONResponse(updated)

@router.delete("/{evenement_id}", dependencies=[Depends(require_admin)])
def delete_evenement(evenement_id: str):
    ok = evenements_repository.delete_evenement(evenement_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Echec de suppression")
    return JSONResponse({"ok": True})

router = APIRouter(prefix="/api/v1/evenements", tags=["evenements"])

@router.get("", response_model=list[dict])
def list_evenements() -> List[Dict[str, Any]]:
    """
    Liste publique des événements (pour vitrine Billetterie).
    """
    res = (
        get_supabase()
        .table("evenements")
        .select("id, title, date, lieu, description, image")
        .order("date", desc=False)
        .execute()
    )
    return res.data or []