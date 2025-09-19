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

def get_user_by_id(user_id: str) -> Optional[dict]:
    from backend.users.repository import get_user_by_id as _get_user_by_id
    return _get_user_by_id(user_id)