from fastapi import APIRouter
from fastapi.responses import JSONResponse
from urllib.parse import urlparse
import socket

from backend.utils.db import get_supabase
from backend.config import SUPABASE_URL

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_root():
    return {"ok": True}

def _check_table(client, name: str):
    try:
        res = client.table(name).select("*").limit(1).execute()
        cnt = len(res.data or [])
        return {"ok": True, "rows": cnt}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/supabase")
def health_supabase():
    effective_url = SUPABASE_URL
    parsed = urlparse(effective_url) if effective_url else None
    hostname = parsed.hostname if parsed else None
    dns_ok = None
    dns_error = None
    if hostname:
        try:
            socket.getaddrinfo(hostname, 443)
            dns_ok = True
        except Exception as e:
            dns_ok = False
            dns_error = str(e)

    info = {
        "supabase_url": effective_url,
        "hostname": hostname,
        "dns_ok": dns_ok,
        "dns_error": dns_error,
        "connect_ok": False,
        "error": None,
        "tables": {}
    }
    try:
        client = get_supabase()
        for t in ["users", "offres", "commandes"]:
            info["tables"][t] = _check_table(client, t)
        info["connect_ok"] = True
    except Exception as e:
        info["error"] = str(e)
    return JSONResponse(info)