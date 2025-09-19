from datetime import date
import os, shutil
from tempfile import NamedTemporaryFile

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="CVA Scheduler API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # loosened for testing; restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def home():
    return {"message": "CVA Scheduler API is running. Open /docs for the API."}

class Window(BaseModel):
    start_date: date
    end_date: date

# --- Temporary test endpoints so you can see POST in /docs ---

@app.post("/solve")
def solve(window: Window):
    return {"status": "ok", "start_date": str(window.start_date), "end_date": str(window.end_date)}

@app.post("/schedules/export/xlsx")
def export_xlsx(window: Window):
    # copies your template so you can download it and confirm paths
    template_path = os.getenv(
        "TEMPLATE_PATH",
        "/workspaces/schedule-generator/backend/app/templates/2026 WORKBOOK TEMPLATE.xlsx"
    )
    if not os.path.exists(template_path):
        return {"error": f"Template not found at {template_path}"}
    tmp = NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()
    shutil.copyfile(template_path, tmp.name)
    fname = f"CVA_Schedule_Test_{window.start_date}_{window.end_date}.xlsx"
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=fname,
    )
