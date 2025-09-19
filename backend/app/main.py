from __future__ import annotations

from fastapi import FastAPI

from app.api import router
from app.db.session import init_db_sync

app = FastAPI(title="Cardio Scheduler")


@app.on_event("startup")
def startup_event() -> None:
    init_db_sync()


app.include_router(router)