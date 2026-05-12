"""Redis client helpers for application caches."""

import logging
from typing import Any

from src.config import Settings

try:
    from redis.asyncio import Redis
except ImportError: 
    Redis = None


settings = Settings()
logger = logging.getLogger(__name__)

_redis_client: Any | None = None


async def get_redis() -> Any | None:
    """Return a shared Redis client, or None when Redis support is unavailable."""
    global _redis_client

    if Redis is None:
        logger.warning("Redis package is not installed; user cache is disabled")
        return None

    if _redis_client is None:
        client_options = {
            "encoding": "utf-8",
            "decode_responses": True,
        }

        if settings.redis.url:
            _redis_client = Redis.from_url(settings.redis.url, **client_options)
        else:
            _redis_client = Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                username=settings.redis.username,
                password=settings.redis.password,
                db=settings.redis.db,
                ssl=settings.redis.ssl,
                **client_options,
            )

    return _redis_client


async def close_redis() -> None:
    """Close the shared Redis client if it was initialized."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
