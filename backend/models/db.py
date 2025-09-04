# imports et init
# backend/models/db.py
from typing import Optional, List, Any
from supabase import create_client, Client
from fastapi import HTTPException
from backend.config import SUPABASE_URL, SUPABASE_ANON, SUPABASE_SERVICE_KEY, SUPABASE_KEY
import logging

_supabase: Optional[Client] = None
_service_supabase: Optional[Client] = None
logger = logging.getLogger(__name__)

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_ANON:
            raise HTTPException(status_code=500, detail="SUPABASE_URL/SUPABASE_ANON_KEY manquants")
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON)
    return _supabase

def get_service_supabase() -> Client:
    global _service_supabase
    if _service_supabase is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise HTTPException(status_code=500, detail="SUPABASE_SERVICE_KEY manquant pour les opérations service")
        _service_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _service_supabase

def fetch_offres() -> List[dict]:
    try:
        res = get_supabase().table("offres").select("*").execute()
        return res.data or []
    except Exception:
        return []

def get_user_by_email(email: str) -> Optional[dict]:
    try:
        res = get_supabase().table("users").select("*").eq("email", email).single().execute()
        return res.data or None
    except Exception:
        return None

def fetch_admin_commandes(limit: int = 100) -> List[dict]:
    """
    Commandes pour l'admin, avec jointures sur users et offres
    """
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, price_paid, created_at, users(email), offres(title, price)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def fetch_user_commandes(user_id: str, limit: int = 50) -> List[dict]:
    """
    Commandes de l'utilisateur connecté (jointure offre)
    """
    if not user_id:
        return []
    try:
        res = (
            get_supabase()
            .table("commandes")
            .select("id, token, price_paid, created_at, offres(title, price)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def fetch_offres_by_ids(ids: List[str]) -> List[dict]:
    """
    Récupère les offres par leurs IDs.
    """
    if not ids:
        return []
    try:
        res = (
            get_supabase()
            .table("offres")
            .select("*")
            .in_("id", ids)
            .execute()
        )
        return res.data or []
    except Exception:
        return []

def insert_commande(user_id: str, offre_id: str, token: str, price_paid: str) -> Optional[dict]:
    """
    Insère une commande (un billet) et retourne un dict truthy en cas de succès.
    price_paid attendu comme string '60.00'
    """
    try:
        (
            get_supabase()
            .table("commandes")
            .insert({"user_id": user_id, "offre_id": offre_id, "token": token, "price_paid": price_paid})
            .execute()
        )
        # Certaines versions de supabase-py ne renvoient pas la ligne. On retourne un dict truthy pour signaler le succès.
        return {"status": "ok"}
    except Exception:
        logger.exception("insert_commande failed (user_id=%s, offre_id=%s, price_paid=%s)", user_id, offre_id, price_paid)
        return None

def insert_commande_with_token(user_id: str, offre_id: str, token: str, price_paid: str, user_token: str) -> Optional[dict]:
    """
    Insert avec le token utilisateur (respecte RLS). À utiliser côté API.
    """
    try:
        client = create_client(SUPABASE_URL, SUPABASE_ANON)  # Utiliser SUPABASE_ANON au lieu de SUPABASE_SERVICE_KEY
        client.postgrest.auth(user_token)
        (
            client
            .table("commandes")
            .insert({"user_id": user_id, "offre_id": offre_id, "token": token, "price_paid": price_paid})
            .execute()
        )
        return {"status": "ok"}
    except Exception:
        logger.exception("insert_commande_with_token failed (user_id=%s, offre_id=%s, price_paid=%s)", user_id, offre_id, price_paid)
        return None

def insert_commande_service(user_id: str, offre_id: str, token: str, price_paid: str) -> Optional[dict]:
    """
    Insert via service-role (bypass RLS). À utiliser côté webhook Stripe.
    """
    try:
        res = (
            get_service_supabase()
            .table("commandes")
            .insert({"user_id": user_id, "offre_id": offre_id, "token": token, "price_paid": price_paid})
            .select("*")
            .execute()
        )
        rows = res.data or []
        return rows[0] if isinstance(rows, list) and rows else res.data or None
    except Exception:
        logger.exception("insert_commande_service failed (user_id=%s, offre_id=%s, price_paid=%s)", user_id, offre_id, price_paid)
        return None