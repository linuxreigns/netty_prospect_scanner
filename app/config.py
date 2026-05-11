from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Netty Prospect Scanner"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # SQLite por defecto para MVP; permite migrar a PostgreSQL cambiando env var
    database_url: str = "sqlite:///./data/netty_scanner.db"

    # Crawling ético
    user_agent: str = "NettyProspectScanner/1.0 (+contacto: comercial@netty.example)"
    request_timeout_seconds: int = 20
    max_concurrency: int = 5
    delay_seconds: float = 1.2
    respect_robots_txt: bool = True

    # Playwright fallback
    playwright_timeout_ms: int = 15000
    enable_playwright_fallback: bool = True

    # IA opcional
    ai_provider: str = "none"  # none|openai|deepseek
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_base_url: str | None = None  # OpenAI compatible endpoint

    # Discovery autónomo via DuckDuckGo
    enable_duckduckgo_discovery: bool = False
    duckduckgo_results_per_query: int = 10

    # Cola comercial desacoplada (Etapa 4)
    redis_url: str | None = None

    # Auth — set API_KEY env var para proteger endpoints sensibles
    api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
