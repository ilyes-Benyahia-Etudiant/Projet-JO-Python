from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.config import PUBLIC_DIR

def mount_static_files(app: FastAPI) -> None:
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")
    app.mount("/js", StaticFiles(directory=str(PUBLIC_DIR / "js")), name="js")