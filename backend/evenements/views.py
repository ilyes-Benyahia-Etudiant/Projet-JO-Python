# Imports (début du fichier)
"""Endpoints API pour la gestion des événements.
- CRUD admin: création, mise à jour, suppression (protégés par require_admin).
- Listing: un endpoint interne (/) et un endpoint public ("") pour la billetterie, avec normalisation du schéma.
- Gestion d'erreurs: 404 quand introuvable, 400 pour validations, 500 en cas d'échec Supabase.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.utils.security import require_admin
from backend.evenements import repository as evenements_repository
from backend.infra.supabase_client import get_supabase
from postgrest.exceptions import APIError

router = APIRouter(prefix="/api/v1/evenements", tags=["Evenements API"])

@router.get("/")
def list_evenements():
    """Liste interne des événements (non normalisée).
    Retourne directement le résultat du repository (toutes colonnes).
    """
    items = evenements_repository.list_evenements()
    return JSONResponse({"items": items})

@router.get("/{evenement_id}")
def get_evenement(evenement_id: str):
    """Récupère un événement par son identifiant.
    - 404 si introuvable.
    """
    item = evenements_repository.get_evenement(evenement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Evenement introuvable")
    return JSONResponse(item)

@router.post("/", dependencies=[Depends(require_admin)])
async def create_evenement(request: Request):
    """Crée un événement (admin uniquement).
    - Valide les champs requis.
    - En cas d’échec repository: 400.
    """
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
    """Met à jour un événement (admin uniquement).
    - Accepte les champs présents seulement.
    - 400 si aucune donnée fournie ou si échec repository.
    """
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
    """Supprime un événement (admin uniquement).
    - 400 si l’opération échoue dans le repository.
    """
    ok = evenements_repository.delete_evenement(evenement_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Echec de suppression")
    return JSONResponse({"ok": True})

# Endpoint public: liste pour la Billetterie
@router.get("", response_model=list[dict])
def list_evenements_public() -> List[Dict[str, Any]]:
    """
    Liste publique des événements (pour vitrine Billetterie).
    Normalise le schéma {id, title, date, lieu, description, image} à partir des colonnes
    réelles {nom_evenement, date_evenement, ...} présentes en DB.
    """
    try:
        res = (
            get_supabase()
            .table("evenements")
            .select("id, nom_evenement, type_evenement, date_evenement, lieu")
            .order("date_evenement", desc=False)
            .execute()
        )
    except APIError:
        # On renvoie une 500 claire si Supabase échoue
        raise HTTPException(status_code=500, detail="Erreur de lecture des événements")

    rows = res.data or []
    normalized: List[Dict[str, Any]] = []
    for r in rows:
        normalized.append({
            "id": r.get("id"),
            "title": r.get("nom_evenement") or "",
            "date": r.get("date_evenement") or "",
            "lieu": r.get("lieu"),
            "type_evenement": r.get("type_evenement"),
            "description": r.get("description") or "",  # vide si absent en DB
            "image": r.get("image") or "",              # vide si absent en DB
        })
    return normalized