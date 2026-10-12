from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    warehouse_path: Path = Path("data/warehouse")
    metadata_path: Path = Path("data/lakehouse/_metadata/run_metrics.json")


settings = Settings()
