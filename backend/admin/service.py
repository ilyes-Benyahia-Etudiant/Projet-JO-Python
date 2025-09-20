# module backend.admin.service

from typing import List, Optional, Dict, Any
from backend.admin import repository as admin_repository
import logging

logger = logging.getLogger(__name__)

def fetch_admin_commandes(limit: int = 100) -> List[dict]:
    return admin_repository.fetch_admin_commandes(limit=limit)

def list_users(limit: int = 100) -> List[dict]:
    return admin_repository.fetch_admin_users(limit=limit)

def update_user(user_id: str, data: Dict[str, Any]) -> Optional[dict]:
    role = (data.get("role") or "").strip()
    if role:
        try:
            admin_repository.set_auth_user_role(user_id, role)
        except Exception:
            logger.exception("admin.service.update_user: failed to update auth user metadata role")
    data_db = dict(data)
    return admin_repository.update_user(user_id, data_db)

def delete_user(user_id: str) -> bool:
    return admin_repository.delete_user(user_id)

def update_commande(commande_id: str, data: Dict[str, Any]) -> Optional[dict]:
    return admin_repository.update_commande(commande_id, data)

def delete_commande(commande_id: str) -> bool:
    return admin_repository.delete_commande(commande_id)

# Wrappers d'accès pour les formulaires d'édition
def get_commande_by_id(commande_id: str) -> Optional[dict]:
    return admin_repository.get_commande_by_id(commande_id)

# Alias attendu par admin/views.py
def get_admin_commandes(limit: int = 100) -> List[dict]:
    return fetch_admin_commandes(limit=limit)

# Wrappers Offres attendus par admin/views.py et validation/views.py
def get_offre_by_id(offre_id: str) -> Optional[dict]:
    from backend.offres.repository import get_offre as _get_offre
    return _get_offre(offre_id)

def update_offre(offre_id: str, data: Dict[str, Any]) -> Optional[dict]:
    from backend.offres.repository import update_offre as _update_offre
    return _update_offre(offre_id, data)

def list_offres(limit: int = 100) -> List[dict]:
    from backend.offres.repository import list_offres as _list_offres
    # Le repo ne gère pas 'limit' pour l’instant, on renvoie tout
    return _list_offres()

def create_offre(data: Dict[str, Any]) -> Optional[dict]:
    from backend.offres.repository import create_offre as _create_offre
    return _create_offre(data)

def delete_offre(offre_id: str) -> bool:
    from backend.offres.repository import delete_offre as _delete_offre
    return _delete_offre(offre_id)

def get_user_by_id(user_id: str) -> Optional[dict]:
    from backend.users.repository import get_user_by_id as _get_user_by_id
    return _get_user_by_id(user_id)

def list_evenements() -> List[dict]:
    from backend.evenements.repository import list_evenements as _list_evenements
    return _list_evenements()

def get_evenement_by_id(evenement_id: str) -> Optional[dict]:
    from backend.evenements.repository import get_evenement as _get_evenement
    return _get_evenement(evenement_id)

def create_evenement(data: Dict[str, Any]) -> Optional[dict]:
    from backend.evenements.repository import create_evenement as _create_evenement
    return _create_evenement(data)

def update_evenement(evenement_id: str, data: Dict[str, Any]) -> Optional[dict]:
    from backend.evenements.repository import update_evenement as _update_evenement
    return _update_evenement(evenement_id, data)

def delete_evenement(evenement_id: str) -> bool:
    from backend.evenements.repository import delete_evenement as _delete_evenement
    return _delete_evenement(evenement_id)