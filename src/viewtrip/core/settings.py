from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tfnsw_api_key: str
    data_dir: Path = Path.home() / ".viewtrip"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "trips.db"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"
