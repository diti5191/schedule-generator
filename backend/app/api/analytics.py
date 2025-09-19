from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends

from app.db.session import get_session
from app.models import Assignment, Provider, ScheduleBlock
from app.schemas.common import CoverageSummary, FairnessSummary
from app.services.seed import seed_all
from app.solver.engine import solve_schedule

router = APIRouter()


def _get_session():
    with get_session() as session:
        yield session


@router.get("/fairness", response_model=list[FairnessSummary])
def fairness(session=Depends(_get_session)) -> list[FairnessSummary]:
    seed_all(session)
    start = date.fromisoformat("2026-01-05")
    end = date.fromisoformat("2026-03-27")
    schedule = solve_schedule(session, start, end)

    weekend_counts = Counter()
    for call in schedule.call_assignments:
        if call.call_type == "weekend_noninv":
            weekend_counts[call.providers[0].initials] += 1

    hospital_counts = Counter()
    for assignment in schedule.assignments:
        if assignment.site_type == "hospital":
            for provider in assignment.providers:
                hospital_counts[provider.initials] += 1

    return [
        FairnessSummary(metric="weekend_call", values=dict(weekend_counts)),
        FairnessSummary(metric="hospital_days", values=dict(hospital_counts)),
    ]


@router.get("/coverage", response_model=list[CoverageSummary])
def coverage(session=Depends(_get_session)) -> list[CoverageSummary]:
    seed_all(session)
    start = date.fromisoformat("2026-01-05")
    end = date.fromisoformat("2026-03-27")
    schedule = solve_schedule(session, start, end)

    gaps: dict[str, list[str]] = defaultdict(list)
    for assignment in schedule.assignments:
        if not assignment.providers:
            gaps[assignment.site_code].append(f"{assignment.date} {assignment.block}")
    return [CoverageSummary(site=site, coverage_gaps=blocks) for site, blocks in gaps.items()]