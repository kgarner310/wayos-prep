from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://wayos:wayos_dev_password@localhost:5432/wayos_prep"
    llm_provider: str = "none"  # openai | anthropic | none
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
