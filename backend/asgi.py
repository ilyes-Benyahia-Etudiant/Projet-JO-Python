"""
ASGI entrypoint: expose `app` for process managers / deployments.

- En production, un process manager (ex: gunicorn/uvicorn-workers, hypercorn) importe `backend.asgi:app`
  pour servir l’application FastAPI en mode ASGI.
- Toute la configuration de FastAPI (routes, middlewares, sécurité, static, etc.) est centralisée
  dans backend.app, ce fichier ne fait qu’exposer l’instance `app`.
"""

from backend.app import app

if __name__ == "__main__":
    # Exécution directe utile en développement local (uvicorn standalone).
    # En production, préférez un gestionnaire de processus (ex: gunicorn -k uvicorn.workers.UvicornWorker).
    import os
    import uvicorn
    uvicorn.run(
        "backend.asgi:app",
        host="0.0.0.0",  # écoute toutes interfaces (Docker/VM)
        port=int(os.getenv("PORT", "8000")),
        reload=True,     # rechargement automatique en dev
    )