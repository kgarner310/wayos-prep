"""arq worker settings for background job processing."""

import os


def get_redis_settings():
    """Get arq RedisSettings from environment."""
    try:
        from arq.connections import RedisSettings
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        # Parse redis URL
        if redis_url.startswith("redis://"):
            parts = redis_url.replace("redis://", "").split("/")
            host_port = parts[0]
            database = int(parts[1]) if len(parts) > 1 else 0
            if ":" in host_port:
                host, port = host_port.split(":")
                port = int(port)
            else:
                host = host_port
                port = 6379
            return RedisSettings(host=host, port=port, database=database)
        return RedisSettings()
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
