"""
Routes simples (hors routers) pour la page d’accueil et les alias.
- Sert / (et /index.html, /accueil) depuis public/index.html si présent, sinon redirige vers /public/index.html.
- /favicon.ico: pas de contenu (204) pour éviter des 404 dans les logs.
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse, Response
from starlette.status import HTTP_204_NO_CONTENT, HTTP_303_SEE_OTHER
from backend.config import PUBLIC_DIR

def register_routes(app: FastAPI) -> None:
    """
    Enregistre les routes racine et alias de l’accueil.
    - Laisse l’OpenAPI propre (include_in_schema=False).
    - Évite les 404 de favicon via une réponse 204.
    """
    @app.get("/", include_in_schema=False)
    def root_redirect():
        index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

    @app.get("/index.html", include_in_schema=False)
    def index_alias():
        index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

    @app.get("/accueil", include_in_schema=False)
    def accueil_alias():
        index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return RedirectResponse(url="/public/index.html", status_code=HTTP_303_SEE_OTHER)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(status_code=HTTP_204_NO_CONTENT)