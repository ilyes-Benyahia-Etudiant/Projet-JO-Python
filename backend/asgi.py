"""
ASGI entrypoint: expose `app` for process managers / deployments.
All FastAPI configuration is centralized in backend.app.
"""
from backend.app import app

if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run(
        "backend.asgi:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )