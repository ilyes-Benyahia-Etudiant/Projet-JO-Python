"""
Lifespan FastAPI: initialisation/arrêt des ressources partagées.
- Initialise FastAPILimiter (Redis) avec options de test (fakeredis).
- Variables d’environnement supportées:
  - DISABLE_FASTAPI_LIMITER_INIT_FOR_TESTS=1: désactive complètement (tests)
  - USE_FAKE_REDIS_FOR_TESTS=1: utilise fakeredis (tests)
  - LOCAL_RATE_LIMIT_FALLBACK=1: active un fallback local si l’init échoue
"""
import os
import logging
import redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

try:
    from fakeredis.aioredis import FakeRedis  # tests only
except Exception:
    FakeRedis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Configure le rate limiting et gère les fallbacks.
    - En cas d’échec de Redis et sans fallback, le rate limiting est désactivé proprement.
    - Les logs indiquent l’état effectif (enabled/disabled) pour observabilité.
    """
    logger = logging.getLogger("uvicorn.error")
    try:
        if os.getenv("DISABLE_FASTAPI_LIMITER_INIT_FOR_TESTS") == "1":
            app.state.rate_limit_enabled = False
            logger.info("Rate limiting disabled by DISABLE_FASTAPI_LIMITER_INIT_FOR_TESTS")
            yield
            return

        use_fake = os.getenv("USE_FAKE_REDIS_FOR_TESTS") == "1"
        if use_fake:
            if not FakeRedis:
                raise RuntimeError("USE_FAKE_REDIS_FOR_TESTS=1 mais fakeredis n'est pas installé.")
            r = FakeRedis(decode_responses=True)
        else:
            redis_url = os.getenv("RATE_LIMIT_REDIS_URL", "redis://127.0.0.1:6379/0")
            r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

        await FastAPILimiter.init(r)
        app.state.rate_limit_enabled = True
        logger.info("Rate limiting enabled")
    except Exception as e:
        if os.getenv("LOCAL_RATE_LIMIT_FALLBACK") == "1":
            app.state.rate_limit_enabled = True
            logger.warning(f"Rate limiting falling back to local in-memory due to init error: {e}")
        else:
            app.state.rate_limit_enabled = False
            logger.warning(f"Rate limiting disabled due to init error: {e}")

    yield