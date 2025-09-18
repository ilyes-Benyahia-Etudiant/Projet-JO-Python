from typing import List, Optional, Dict, Any
from backend.offres import repository as offres_repository
from . import repository as admin_repository

def list_offres() -> List[dict]:
    return offres_repository.list_offres()

def get_offre_by_id(offre_id: str) -> Optional[dict]:
    return offres_repository.get_offre(offre_id)

def create_offre(data: Dict[str, Any]) -> Optional[dict]:
    # Place pour validations métier
    return offres_repository.create_offre(data)

def update_offre(offre_id: str, data: Dict[str, Any]) -> Optional[dict]:
    # Place pour validations métier
    return offres_repository.update_offre(offre_id, data)

def delete_offre(offre_id: str) -> bool:
    return offres_repository.delete_offre(offre_id)

def get_admin_commandes(limit: int = 100) -> List[dict]:
    return admin_repository.fetch_admin_commandes(limit=limit)

def list_users(limit: int = 100) -> List[dict]:
    return admin_repository.fetch_admin_users(limit=limit)

def update_user(user_id: str, data: Dict[str, Any]) -> Optional[dict]:
    return admin_repository.update_user(user_id, data)

def delete_user(user_id: str) -> bool:
    return admin_repository.delete_user(user_id)

def update_commande(commande_id: str, data: Dict[str, Any]) -> Optional[dict]:
    return admin_repository.update_commande(commande_id, data)

def delete_commande(commande_id: str) -> bool:
    return admin_repository.delete_commande(commande_id)

# Wrappers d'accès pour les formulaires d'édition
def get_commande_by_id(commande_id: str) -> Optional[dict]:
    return admin_repository.get_commande_by_id(commande_id)

def get_user_by_id(user_id: str) -> Optional[dict]:
    from backend.users.repository import get_user_by_id as _get_user_by_id
    return _get_user_by_id(user_id)