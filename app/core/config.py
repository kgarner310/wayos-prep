import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://wayos:wayos@localhost:5432/wayos_prep")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Auth / JWT — MUST be set via env var in production
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-only-unsafe-key-override-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS
    CORS_ORIGINS: list[str] = [
        o.strip() for o in
        os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]

    # File upload
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10MB

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
