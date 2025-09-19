from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional


@dataclass
class Provider:
    id: int = 0
    initials: str = ""
    full_name: str = ""
    type: str = "MD"
    specialty: Optional[str] = None
    is_invasive: bool = False
    is_ep: bool = False
    seniority: Optional[int] = None
    employment_status: Optional[str] = None
    home_office_id: Optional[int] = None
    privileges_json: Dict[str, Any] = field(default_factory=dict)
    weekend_team_eligible: bool = True
    max_sessions_per_day: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class SiteOffice:
    id: int = 0
    code: str = ""
    name: str = ""


@dataclass
class SiteHospital:
    id: int = 0
    code: str = ""
    name: str = ""


@dataclass
class Holiday:
    id: int = 0
    date: date = date.today()
    name: str = ""
    is_office_closed: bool = True
    extend_weekend: bool = True


@dataclass
class VacationAllowance:
    id: int = 0
    provider_id: int = 0
    year: int = 0
    days_total: int = 0
    days_used: int = 0
    am_quota: Optional[int] = None
    pm_quota: Optional[int] = None


@dataclass
class VacationRequest:
    id: int = 0
    provider_id: int = 0
    start_date: date = date.today()
    end_date: date = date.today()
    block: str = "FULLDAY"
    status: str = "DRAFT"
    approver_id: Optional[int] = None
    audit_json: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CoverageRequirement:
    id: int = 0
    site_type: str = "office"
    site_id: int = 0
    day_of_week: int = 0
    block: str = "AM"
    min_md: int = 0
    min_apn: int = 0
    roles_json: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallRule:
    id: int = 0
    rule_json: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FairnessTarget:
    id: int = 0
    metric: str = ""
    window_days: int = 0
    target_value: float = 0.0


@dataclass
class ScheduleBlock:
    id: int = 0
    date: date = date.today()
    block: str = "AM"
    site_type: str = "office"
    site_id: int = 0
    role: str = ""
    locked: bool = False


@dataclass
class Assignment:
    id: int = 0
    schedule_block_id: int = 0
    provider_id: int = 0
    is_call: bool = False
    is_weekend: bool = False
    source: str = "solver"
    penalty_cost: Optional[int] = None
    reason: Optional[str] = None


@dataclass
class SolveRun:
    id: int = 0
    label: str = ""
    start_date: date = date.today()
    end_date: date = date.today()
    status: str = "PENDING"
    config_json: Dict[str, Any] = field(default_factory=dict)
    objective_breakdown_json: Optional[Dict[str, Any]] = None
    diagnostic_log: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)