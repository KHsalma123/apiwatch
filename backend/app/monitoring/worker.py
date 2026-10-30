"""Monitoring worker: a separate process from the API server.

Run with:  python -m app.monitoring.worker

How it avoids double checks (even if 2 workers run by accident):
  every tick it ATOMICALLY "claims" due monitors with find_one_and_update, pushing
  next_check_at forward in the same operation. MongoDB guarantees only one worker wins.
"""
import asyncio
import logging
import signal

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.database import mongo
from app.monitoring.checker import check_monitor, new_client
from app.services.common import utcnow

logger = logging.getLogger("apiwatch.worker")


async def claim_due_monitors(db, limit: int) -> list[dict]:
    claimed = []
    for _ in range(limit):
        doc = await db.monitors.find_one_and_update(
            {"is_active": True, "next_check_at": {"$lte": utcnow()}},
            [{"$set": {"next_check_at": {"$dateAdd": {"startDate": "$$NOW", "unit": "second", "amount": "$interval_seconds"}}}}],
            sort=[("next_check_at", 1)],
        )
        if doc is None:
            break
        claimed.append(doc)
    return claimed


async def run_tick(db, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> int:
    monitors = await claim_due_monitors(db, get_settings().worker_batch_size)

    async def one(m: dict):
        async with semaphore:
            try:
                await check_monitor(db, m, client)
            except Exception:
                logger.exception("Check failed for monitor %s", m.get("_id"))

    await asyncio.gather(*(one(m) for m in monitors))
    return len(monitors)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    db = await mongo.connect()
    client = new_client()
    semaphore = asyncio.Semaphore(settings.worker_concurrency)

    async def tick():
        try:
            n = await run_tick(db, client, semaphore)
            if n:
                logger.info("Checked %d monitor(s)", n)
        except Exception:
            logger.exception("Tick failed")

    scheduler = AsyncIOScheduler()
    # ONE job, ticking every few seconds. max_instances=1 + coalesce: ticks never overlap or pile up.
    scheduler.add_job(tick, "interval", seconds=settings.worker_tick_seconds, max_instances=1, coalesce=True)
    scheduler.start()
    logger.info("Worker started (tick every %ss)", settings.worker_tick_seconds)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows
            pass
    await stop.wait()

    logger.info("Shutting down")
    scheduler.shutdown(wait=False)
    await client.aclose()
    await mongo.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
