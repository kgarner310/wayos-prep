"""Artifact Worker — background artifact generation using arq.

Generates artifacts asynchronously after account creation or on demand.
Falls back to synchronous generation if arq/Redis is unavailable.
"""

import logging
import os
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


async def generate_artifact_task(ctx: dict, account_id: str, artifact_type: str):
    """arq task: generate a single artifact for an account."""
    from app.db.session import get_engine
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        from app.services.artifact_engine import generate_artifact
        result = generate_artifact(UUID(account_id), artifact_type, db)
        db.commit()
        logger.info("Generated %s artifact for account %s", artifact_type, account_id)
        return {"artifact_id": str(result.id), "status": result.status}
    except Exception:
        db.rollback()
        logger.exception("Failed to generate %s for %s", artifact_type, account_id)
        return {"error": f"Failed to generate {artifact_type}"}
    finally:
        db.close()


async def generate_all_artifacts_task(ctx: dict, account_id: str):
    """arq task: generate all artifacts for an account in priority order."""
    from app.db.session import get_engine
    from app.schemas.artifact_schemas import ARTIFACT_PRIORITY
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        from app.services.artifact_engine import generate_all_artifacts
        results = generate_all_artifacts(UUID(account_id), db)
        db.commit()
        logger.info("Generated %d artifacts for account %s", len(results), account_id)
        return {"count": len(results), "account_id": account_id}
    except Exception:
        db.rollback()
        logger.exception("Failed to generate artifacts for %s", account_id)
        return {"error": "Failed to generate artifacts"}
    finally:
        db.close()


def enqueue_artifact_generation(account_id: UUID, artifact_type: Optional[str] = None):
    """Enqueue artifact generation. Falls back to sync if arq unavailable."""
    try:
        import arq
        from app.workers.settings import get_redis_settings

        async def _enqueue():
            pool = await arq.create_pool(get_redis_settings())
            if artifact_type:
                await pool.enqueue_job(
                    "generate_artifact_task",
                    str(account_id),
                    artifact_type,
                )
            else:
                await pool.enqueue_job(
                    "generate_all_artifacts_task",
                    str(account_id),
                )
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

        logger.info("Enqueued artifact generation for %s", account_id)
        return True

    except (ImportError, Exception):
        logger.info("arq unavailable — artifact generation will be synchronous")
        return False
