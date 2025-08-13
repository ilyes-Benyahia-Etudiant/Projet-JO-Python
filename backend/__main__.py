"""
Point d'entrée principal pour le backend FastAPI.
Usage: python -m backend
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )