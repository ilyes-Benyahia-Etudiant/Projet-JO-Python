from fastapi import FastAPI
from .lifespan import lifespan
from .middlewares import register_basic_middlewares, register_no_cache_middleware
from .static import mount_static_files
from .security import register_security_middleware
from .exceptions import register_exception_handlers
from .routes import register_routes
from .routers import register_routers
from backend.utils.csrf import register_csrf_middleware

def create_app() -> FastAPI:
    app = FastAPI(title="Projet JO Python", lifespan=lifespan)
    register_basic_middlewares(app)
    mount_static_files(app)
    register_csrf_middleware(app)
    register_security_middleware(app)
    register_no_cache_middleware(app)
    register_exception_handlers(app)
    register_routes(app)
    register_routers(app)
    return app