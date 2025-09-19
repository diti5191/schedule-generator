from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import settings


@lru_cache
def load(path: Path | None = None) -> dict:
    target = path or settings.rules_config_path
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as fh:
        return json.load(fh)