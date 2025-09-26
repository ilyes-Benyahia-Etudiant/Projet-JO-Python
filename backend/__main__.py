"""
Point d'entrée principal pour le backend FastAPI.

Usage:
    python -m backend

Ce mode lance uvicorn directement et lit quelques variables d'environnement:
- PORT: port d'écoute (par défaut 8000)
- UVICORN_RELOAD: active le reload auto en dev ("1"/"true"/"yes")
- LOG_LEVEL: niveau de logs uvicorn (ex: "info", "debug")
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Activer le reload uniquement si explicitement demandé (ex: en local)
    reload_flag = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    log_level = os.environ.get("LOG_LEVEL", "info")
    uvicorn.run(
        "backend.asgi:app",  # on réutilise l'ASGI app unique
        host="0.0.0.0",
        port=port,
        reload=reload_flag,
        log_level=log_level
    )