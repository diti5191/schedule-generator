from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import settings

router = APIRouter()


@router.post("/rules")
def upload_rules_config(content: dict) -> dict:
    path = settings.rules_config_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("""# auto-uploaded\n""" + content.get("raw", ""))
    return {"status": "ok", "path": str(path)}


@router.get("/rules/history")
def get_rules_history() -> dict:
    path = settings.rules_config_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="No history")
    return {"path": str(path), "content": path.read_text()[:4096]}