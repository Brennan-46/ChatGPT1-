from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Business Agent"
    app_env: str = "dev"
    log_level: str = "INFO"

    model_name: str = "gpt-4.1-mini"

    chroma_path: str = "./data/chroma"
    memory_collection: str = "business_agent_memory"

    max_iterations: int = 8
    max_tool_calls_per_run: int = 20
    max_runtime_seconds: int = 90
    agent_kill_switch: bool = False
    database_url: str = "sqlite:///./data/agent.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
