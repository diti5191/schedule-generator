from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class AuditModel(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class VacationRequestCreate(BaseModel):
    provider_id: int
    start_date: date
    end_date: date
    block: str


class VacationRequestUpdate(BaseModel):
    status: str
    approver_id: int | None = None
    audit_json: dict[str, Any] | None = None


class VacationRequestRead(VacationRequestCreate, AuditModel):
    id: int
    status: str
    approver_id: int | None = None
    audit_json: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class VacationAllowanceRead(BaseModel):
    provider_id: int
    year: int
    days_total: int
    days_used: int
    am_quota: int | None = None
    pm_quota: int | None = None

    class Config:
        from_attributes = True


class SolveRequest(BaseModel):
    start_date: date
    end_date: date
    weights_override: dict[str, float] | None = None
    lock_blocks: list[int] | None = None


class SolveResponse(BaseModel):
    solve_run_id: int
    status: str


class SolveStatusRead(BaseModel):
    id: int
    status: str
    label: str
    start_date: date
    end_date: date
    objective_breakdown_json: dict[str, Any] | None = None
    diagnostic_log: str | None = None

    class Config:
        from_attributes = True


class FairnessSummary(BaseModel):
    metric: str
    values: dict[str, Any]


class CoverageSummary(BaseModel):
    site: str
    coverage_gaps: list[str]