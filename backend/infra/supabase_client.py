from typing import Optional
from supabase import create_client, Client
from fastapi import HTTPException
from backend.config import SUPABASE_URL, SUPABASE_ANON, SUPABASE_SERVICE_KEY

_supabase: Optional[Client] = None
_service_supabase: Optional[Client] = None

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