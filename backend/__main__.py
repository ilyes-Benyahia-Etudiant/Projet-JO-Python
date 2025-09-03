"""
Point d'entrée principal pour le backend FastAPI.
Usage: python -m backend
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Activer le reload uniquement si explicitement demandé (ex: en local)
    reload_flag = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    log_level = os.environ.get("LOG_LEVEL", "info")
    uvicorn.run(
        "backend.asgi:app",
        host="0.0.0.0",
        port=port,
        reload=reload_flag,
        log_level=log_level
    )