# module backend.validation.repository
from typing import Any, Dict, Optional
import logging
from supabase import create_client
from backend.config import SUPABASE_URL, SUPABASE_ANON
from backend.infra.supabase_client import get_service_supabase
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

def get_ticket_by_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Récupère une 'commande' (billet) par token.
    Lecture robuste: on évite les sélections imbriquées dépendantes de FKs et on fait des fetch séparés.
    """
    # Sécurisation: nettoyer guillemets et, si jamais un composite arrive, ne garder que la partie droite
    cleaned = (token or "").strip().strip('"').strip("'")
    if "." in cleaned:
        cleaned = cleaned.split(".", 1)[1].strip().strip('"').strip("'")

    try:
        base_res = (
            get_service_supabase()
            .table("commandes")
            .select("id, token, user_id, created_at, offre_id")
            .eq("token", cleaned)
            .single()
            .execute()
        )
        row = base_res.data or None
    except Exception as e:
        logger.exception("Erreur lors de la récupération de la commande par token: %s", e)
        return None

    if not row:
        return None

    result: Dict[str, Any] = {
        "id": row.get("id"),
        "token": row.get("token"),
        "user_id": row.get("user_id"),
        "created_at": row.get("created_at"),
        "offre_id": row.get("offre_id"),
    }

    # Optionnel: récupérer l'offre associée (retirer 'image' si la colonne n'existe pas)
    try:
        if row.get("offre_id"):
            offre_res = (
                get_service_supabase()
                .table("offres")
                .select("id, title, description")  # image retiré
                .eq("id", row["offre_id"])
                .single()
                .execute()
            )
            result["offres"] = offre_res.data or None
    except Exception as e:
        logger.warning("Impossible de récupérer l'offre associée: %s", e)
        result["offres"] = None

    # Optionnel: récupérer l'utilisateur associé (pour bio = user_key)
    try:
        if row.get("user_id"):
            user_res = (
                get_service_supabase()
                .table("users")
                .select("id, full_name, email, bio")
                .eq("id", row["user_id"])
                .single()
                .execute()
            )
            result["users"] = user_res.data or None
    except Exception as e:
        logger.warning("Impossible de récupérer l'utilisateur associé: %s", e)
        result["users"] = None

    return result

def get_last_validation(token: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la dernière validation enregistrée pour ce token.
    """
    try:
        res = (
            get_service_supabase()
            .table("ticket_validations")
            .select("id, token, commande_id, scanned_at, scanned_by, status")
            .eq("token", token)
            .order("scanned_at", desc=True)
            .limit(1)
            .execute()
        )
        data = (res.data or [])
        return data[0] if data else None
    except Exception:
        return None


def insert_validation(token: str, commande_id: str, admin_id: str, status: str = "validated", user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    # Utilise le client service-role pour éviter les problèmes RLS.
    # Retourne None en cas de doublon (23505), le service traitera 'already_validated'.
    payload = {
        "token": token,
        "commande_id": commande_id,
        "scanned_by": admin_id,
        "status": status,
    }

    client = get_service_supabase()
    try:
        res = client.table("ticket_validations").insert(payload).execute()
        data = res.data or []
        if isinstance(data, list):
            return data[0] if data else payload
        if isinstance(data, dict):
            return data
        return payload
    except APIError as e:
        code = None
        if e.args and isinstance(e.args[0], dict):
            code = e.args[0].get("code")
        if code == "23505":
            return None
        return None