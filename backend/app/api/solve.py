from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_session
from app.models import SolveRun
from app.schemas.common import SolveRequest, SolveResponse, SolveStatusRead
from app.services.seed import seed_all
from app.solver.engine import solve_schedule

router = APIRouter()


def _get_session():
    with get_session() as session:
        yield session


@router.post("", response_model=SolveResponse)
def solve(payload: SolveRequest, session=Depends(_get_session)) -> SolveResponse:
    seed_all(session)
    schedule = solve_schedule(session, payload.start_date, payload.end_date)
    solve_run = SolveRun(
        label=f"{payload.start_date}__{payload.end_date}",
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="SOLVED",
        objective_breakdown_json={"assignments": len(schedule.assignments)},
    )
    session.add(solve_run)
    session.commit()
    session.refresh(solve_run)
    return SolveResponse(solve_run_id=solve_run.id, status=solve_run.status)


@router.get("/{solve_run_id}", response_model=SolveStatusRead)
def get_status(solve_run_id: int, session=Depends(_get_session)) -> SolveRun:
    solve_run = session.get(SolveRun, solve_run_id)
    if not solve_run:
        raise HTTPException(status_code=404, detail="Solve run not found")
    return solve_run