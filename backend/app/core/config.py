from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    app_name: str = "Cardio Scheduler"
    database_url: str = "memory://"
    sync_database_url: str = "memory://"
    template_path: Path = BASE_DIR / "templates/2026_WORKBOOK_TEMPLATE.xlsx"
    rules_config_path: Path = BASE_DIR / "config/rules_config.yaml"
    mapping_config_path: Path = BASE_DIR / "config/mapping.yaml"
    seed_window_start: str = "2026-01-05"
    seed_window_end: str = "2026-03-27"


@lru_cache
def get_settings(**overrides: Any) -> Settings:
    base = Settings()
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


settings = get_settings()