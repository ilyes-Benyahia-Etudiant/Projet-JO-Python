"""
Pont de compatibilité: expose `app` pour les process managers / déploiements (ex: uvicorn backend.api:app).
Toute la configuration (CORS, static, templates, routers, Supabase, etc.) est centralisée dans backend.app.
"""

from backend.app import app

if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )



