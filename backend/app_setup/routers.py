"""
Registre central des routers (web, API v1, admin, health).
- Web: users_web_router, auth_web_router, validate_web_router
- API v1: auth_api_router, commandes, tickets, validation, payments, users, evenements
- Admin: admin_router
- Health: health_router
"""
from fastapi import FastAPI
from backend.users.views import web_router as users_web_router, api_router as users_api_router
from backend.auth.views import web_router as auth_web_router, api_router as auth_api_router
from backend.validation.views import web_router as validate_web_router
from backend.commandes import views as commandes_views
from backend.tickets import views as tickets_views
from backend.validation import views as validation_views
from backend.payments import views as payments_views
from backend.admin.views import router as admin_router
from backend.health.router import router as health_router
from backend.evenements import views as evenements_views

def register_routers(app: FastAPI) -> None:
    """
    Agrège tous les routers de l’application.
    - Permet une vision d’ensemble des points d’entrée et une configuration modulaire.
    - L’ordre n’a pas d’impact sauf conflits de chemins (évités par préfixes).
    """
    # Pages web (HTML)
    app.include_router(users_web_router)
    app.include_router(auth_web_router)
    app.include_router(validate_web_router)
    # API v1
    app.include_router(auth_api_router)
    app.include_router(commandes_views.router)
    app.include_router(tickets_views.router)
    app.include_router(validation_views.router)
    app.include_router(payments_views.router)
    app.include_router(users_api_router)
    app.include_router(evenements_views.router)
    # Admin
    app.include_router(admin_router)
    # Health & monitoring
    app.include_router(health_router)