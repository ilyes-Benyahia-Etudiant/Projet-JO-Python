"""
Montage des fichiers statiques.
Expose:
- /public -> tout le répertoire public
- /static -> alias pour compatibilité
- /js -> accès direct aux scripts JS/TS compilés
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.config import PUBLIC_DIR

def mount_static_files(app: FastAPI) -> None:
    """
    Monte les répertoires statiques sur des préfixes stables.
    - Utilisé par la factory pour servir les assets sans passer par un serveur externe.
    """
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")
    app.mount("/js", StaticFiles(directory=str(PUBLIC_DIR / "js")), name="js")