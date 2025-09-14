from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.health.service import health_supabase_info

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_root():
    return {"ok": True}

@router.get("/supabase")
def health_supabase():
    return JSONResponse(health_supabase_info())