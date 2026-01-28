from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    ENV: str = "local"
    DEBUG: int = 1

    # CONSTANTS
    NWS_API_BASE: str = "https://api.weather.gov"
    USER_AGENT: str = "weather-app/1.0"


settings = Settings()
