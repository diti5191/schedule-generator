# CVA USA Scheduling Platform

Monorepo housing the backend (FastAPI + solver) and the frontend modules for the CVA USA / The Heart House scheduling platform. The project manages vacation intake, rules ingestion, and CP-SAT scheduling for 34 MDs and 10 APNs across 7 hospitals and 7 offices.

## Structure

- `backend/` – FastAPI application with in-memory data session, CP-style solver stub, exporter, seeds, and pytest suite.
- `frontend/` – Dependency-light JavaScript modules plus static server, Node-based unit tests, and Dockerfile.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
PYTHONPATH=. pytest
```

The backend uses an in-memory session and JSON-backed configuration. See `backend/README.md` for seed data, API endpoints, and template mapping details.

### Frontend

```bash
cd frontend
npm test
npm start  # serves http://localhost:4173
```

The frontend exposes framework-agnostic modules that can be embedded into SPAs or server-rendered templates. Tests leverage Node's built-in runner (`node --test`).

## Deployment

- Backend: container image builds via `backend/Dockerfile`. Deploy to Cloud Run with `gcloud run deploy backend --source backend` (see backend README for environment variables and template paths).
- Frontend: container image builds via `frontend/Dockerfile`. Deploy to Cloud Run or any static host. Ensure `PORT` is propagated (defaults to 4173 locally).

## Golden Assets

A workbook template (`backend/app/templates/2026_WORKBOOK_TEMPLATE.xlsx`) and golden export (`backend/tests/data/golden_week1.xlsx`) are checked in to validate solver→exporter fidelity.