from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse, FileResponse
from starlette.status import HTTP_303_SEE_OTHER, HTTP_204_NO_CONTENT
from backend.config import PUBLIC_DIR

def register_routes(app: FastAPI) -> None:
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