"""Application configuration loaded from environment variables / app.env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Values come from the environment or an app.env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Application ---
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "INFO"

    # --- Storage ---
    data_dir: str = "/var/lib/raspi-audio-scheduler"
    database_url: str = ""

    # --- NTP ---
    ntp_primary: str = "ntp.nict.jp"
    ntp_secondary: str = "time.cloudflare.com"
    ntp_tertiary: str = "time.google.com"
    ntp_interval: int = 300
    ntp_timeout: int = 5

    # --- VOICEVOX ---
    voicevox_url: str = "http://127.0.0.1:50021"
    voicevox_timeout: int = 10
    voice_prefetch_seconds: int = 600
    voice_prefetch_retries: str = "600,300,120,30"

    # --- Audio Agent ---
    audio_agent_url: str = "http://127.0.0.1:8031"

    # --- Development ---
    mock_audio: bool = False

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = Path(self.data_dir) / "database" / "app.db"
        return f"sqlite:///{db_path}"

    @property
    def audio_dir(self) -> Path:
        return Path(self.data_dir) / "audio"

    @property
    def voice_cache_dir(self) -> Path:
        return Path(self.data_dir) / "voice-cache"

    @property
    def database_dir(self) -> Path:
        return Path(self.data_dir) / "database"

    @property
    def backup_dir(self) -> Path:
        return Path(self.data_dir) / "backups"

    @property
    def prefetch_retry_offsets(self) -> list[int]:
        return [int(x) for x in self.voice_prefetch_retries.split(",") if x.strip().isdigit()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
