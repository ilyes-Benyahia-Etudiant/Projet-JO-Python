from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
import os
import time
import hashlib
try:
    from backend.utils.security import COOKIE_NAME
except Exception:
    COOKIE_NAME = "sb_access"

def optional_rate_limit(times: int, seconds: int):
    async def _dep(request: Request):
        def _user_key_from_request(req: Request) -> str:
            # Priorité: session cookie (hashé) puis IP
            token = req.cookies.get(COOKIE_NAME)
            path = req.url.path
            if token:
                h = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
                return f"user:{h}:{path}"
            ip = req.client.host if req.client else "local"
            return f"ip:{ip}:{path}"

        # Forcer le fallback mémoire en DEV si demandé
        if os.getenv("LOCAL_RATE_LIMIT_FALLBACK") == "1":
            now = time.time()
            key = _user_key_from_request(request)
            store = getattr(request.app.state, "_rl_store", {})
            hits = [t for t in store.get(key, []) if now - t < seconds]
            if len(hits) >= times:
                raise HTTPException(status_code=429, detail="Too Many Requests")
            hits.append(now)
            store[key] = hits
            request.app.state._rl_store = store
            return

        # Respecter le flag global
        disabled_flag = getattr(request.app.state, "rate_limit_enabled", None) is False
        if disabled_flag:
            return

        # Utiliser fastapi-limiter si dispo
        try:
            from fastapi_limiter.depends import RateLimiter
            async def _identifier(req: Request) -> str:
                return _user_key_from_request(req)
            return await RateLimiter(times=times, seconds=seconds, identifier=_identifier)(request)
        except Exception:
            # Si fastapi-limiter échoue (ex: SCRIPT non supporté), pas de 429 en prod;
            # en dev, activer LOCAL_RATE_LIMIT_FALLBACK=1
            return
    return _dep

def rate_limit_health_info(request: Request) -> Dict[str, Any]:
    enabled = getattr(request.app.state, "rate_limit_enabled", None)

    limiter_ready = False
    backend = None
    try:
        from fastapi_limiter import FastAPILimiter
        limiter_ready = getattr(FastAPILimiter, "redis", None) is not None
        backend = "redis" if limiter_ready else None
    except Exception:
        limiter_ready = False
        backend = None

    info: Dict[str, Any] = {
        "enabled": (bool(enabled) if enabled is not None else None),
        "ready": limiter_ready,
        "backend": backend,
    }

    if backend == "redis":
        try:
            from urllib.parse import urlparse
            redis_url = os.getenv("RATE_LIMIT_REDIS_URL")
            if redis_url:
                p = urlparse(redis_url)
                info["redis"] = {
                    "scheme": p.scheme,
                    "host": p.hostname,
                    "port": p.port,
                }
        except Exception:
            pass

    return info