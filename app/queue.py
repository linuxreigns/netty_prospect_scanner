"""Cola Redis para jobs de pipeline. Fallback transparente a BackgroundTasks si Redis no está disponible."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.config import settings

log = logging.getLogger(__name__)

PIPELINE_QUEUE_KEY = "netty:pipeline:jobs"

_redis = None
_consumer_task: asyncio.Task | None = None


async def init_redis() -> None:
    global _redis
    if not settings.redis_url:
        log.info("REDIS_URL no configurado — BackgroundTasks como fallback")
        return
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        _redis = client
        log.info("Redis conectado: %s", settings.redis_url)
    except Exception as exc:
        log.warning("Redis no disponible (%s) — usando BackgroundTasks", exc)


async def close_redis() -> None:
    global _redis, _consumer_task
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
    if _redis:
        await _redis.aclose()
        _redis = None


def is_available() -> bool:
    return _redis is not None


async def enqueue_pipeline_job(job_id: str) -> bool:
    """Encola job_id en Redis. Retorna False si Redis no está disponible (usar BackgroundTasks)."""
    if _redis is None:
        return False
    await _redis.rpush(PIPELINE_QUEUE_KEY, job_id)
    return True


async def start_consumer(execute_job_fn: Callable[[str], Awaitable[None]]) -> None:
    """Inicia el consumer loop. Solo activo si Redis está disponible."""
    global _consumer_task
    if _redis is None:
        return

    async def _consume() -> None:
        log.info("Redis pipeline consumer iniciado (queue: %s)", PIPELINE_QUEUE_KEY)
        while True:
            try:
                result = await _redis.blpop(PIPELINE_QUEUE_KEY, timeout=5)
                if result:
                    _, job_id = result
                    asyncio.create_task(execute_job_fn(job_id))
            except asyncio.CancelledError:
                log.info("Redis consumer detenido")
                break
            except Exception as exc:
                log.error("Redis consumer error: %s", exc)
                await asyncio.sleep(2)

    _consumer_task = asyncio.create_task(_consume())
