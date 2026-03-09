"""arq worker settings for background job processing."""

import os


def get_redis_settings():
    """Get arq RedisSettings from environment."""
    try:
        from arq.connections import RedisSettings
        from urllib.parse import urlparse
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        parsed = urlparse(redis_url)
        return RedisSettings(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            database=int(parsed.path.lstrip("/") or 0),
            password=parsed.password,
        )
    except ImportError:
        return None


class WorkerSettings:
    """arq worker settings class."""

    functions = []
    redis_settings = None

    @classmethod
    def configure(cls):
        from app.workers.artifact_worker import (
            generate_artifact_task,
            generate_all_artifacts_task,
        )
        cls.functions = [generate_artifact_task, generate_all_artifacts_task]
        cls.redis_settings = get_redis_settings()
        return cls
