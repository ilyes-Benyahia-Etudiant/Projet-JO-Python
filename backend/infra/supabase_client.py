from typing import Optional
from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_ANON, SUPABASE_SERVICE_KEY

_supabase: Optional[Client] = None
_service_supabase: Optional[Client] = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON)
    return _supabase

def get_service_supabase() -> Client:
    global _service_supabase
    if not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_KEY manquant pour get_service_supabase()")
    if _service_supabase is None:
        _service_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _service_supabase

def get_user_supabase(user_token: str) -> Client:
    """
    Client Supabase 'anon' avec auth utilisateur (RLS actif).
    À utiliser pour opérer au nom d'un utilisateur sans polluer l'instance globale.
    """
    if not user_token:
        raise ValueError("user_token is required")
    client = create_client(SUPABASE_URL, SUPABASE_ANON)
    client.postgrest.auth(user_token)
    return client