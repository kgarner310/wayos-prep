"""Triage Worker — background AI triage using arq.

Runs AI triage asynchronously after a service request is created.
Falls back to synchronous processing if arq/Redis is unavailable.
"""

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


async def triage_request_task(ctx: dict, triage_id: str):
    """arq task: run AI triage on a service request."""
    from app.db.session import get_engine
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        from app.services.triage_service import run_ai_triage
        result = run_ai_triage(db, UUID(triage_id))
        db.commit()
        logger.info("Triaged request %s → %s (%s)", triage_id, result.request_type, result.urgency)
        return {"triage_id": triage_id, "status": result.status, "request_type": result.request_type}
    except Exception:
        db.rollback()
        logger.exception("Failed to triage request %s", triage_id)
        return {"error": f"Failed to triage {triage_id}"}
    finally:
        db.close()


def enqueue_triage(triage_id: UUID) -> bool:
    """Enqueue triage processing. Falls back to sync if arq unavailable."""
    try:
        import arq
        from app.workers.settings import get_redis_settings

        async def _enqueue():
            pool = await arq.create_pool(get_redis_settings())
            await pool.enqueue_job("triage_request_task", str(triage_id))
            await pool.close()

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_enqueue())
            else:
                loop.run_until_complete(_enqueue())
        except RuntimeError:
            asyncio.run(_enqueue())

        logger.info("Enqueued triage for %s", triage_id)
        return True

    except (ImportError, Exception):
        logger.info("arq unavailable — triage will be synchronous")
        return False
