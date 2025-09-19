from __future__ import annotations

from datetime import date, timedelta

from app.models import Holiday
from app.services.seed import seed_all
from app.solver.engine import solve_schedule


START = date(2026, 1, 5)
END = date(2026, 3, 27)


def _weekdays(start: date, end: date):
    current = start
    while current <= end:
        if current.weekday() < 5:
            yield current
        current += timedelta(days=1)


def test_feasible_schedule(session):
    seed_all(session)
    schedule = solve_schedule(session, START, END)
    holiday_days = {h.date for h in session.all(Holiday) if h.is_office_closed}

    # WT hospital coverage 1 MD + 2 APNs per block
    for day in _weekdays(START, END):
        if day in holiday_days:
            continue
        for block in ("AM", "PM"):
            assignments = [
                a for a in schedule.assignments if a.site_code in {"WTH", "WTH_APN"} and a.date == day and a.block == block
            ]
            md = [p for a in assignments if a.site_code == "WTH" for p in a.providers]
            apn = [p for a in assignments if a.site_code == "WTH_APN" for p in a.providers]
            assert len(md) == 1, f"Missing WT MD on {day} {block}"
            assert len(apn) == 2, f"Missing WT APNs on {day} {block}"
            assert apn[0].initials != apn[1].initials

    # RMC pair coverage
    for day in _weekdays(START, END):
        if day in holiday_days:
            continue
        for block in ("AM", "PM"):
            assignments = [a for a in schedule.assignments if a.site_code == "RMC" and a.date == day and a.block == block]
            pair = [p for a in assignments for p in a.providers]
            assert len(pair) == 2
            types = {p.type for p in pair}
            assert types == {"MD", "APN"}

    # Offices HH, HH3, SVI, WT at least one MD per block
    for day in _weekdays(START, END):
        if day in holiday_days:
            continue
        for site in ("HH", "HH3", "SVI", "WT"):
            for block in ("AM", "PM"):
                assignments = [
                    a for a in schedule.assignments if a.site_code == site and a.date == day and a.block == block
                ]
                assert assignments, f"Missing office assignment for {site} {day} {block}"
                for provider in assignments[0].providers:
                    assert provider.type == "MD"

    # OBL only on Wednesdays
    for assignment in schedule.assignments:
        if assignment.site_code == "COO_OBL":
            assert assignment.date.weekday() == 2
            assert assignment.providers[0].initials in {"DPR", "APZ", "AML", "VKV", "ZZR"}

    # ICD clinic staffed with EP MD + two EP APNs, and NMC only Mon/Tue
    for assignment in schedule.assignments:
        if assignment.site_code.startswith("ICD_"):
            initials = [p.initials for p in assignment.providers]
            assert any(p.initials in {"EKT", "JWW", "JKT"} for p in assignment.providers if p.type == "MD")
            apns = [p for p in assignment.providers if p.type == "APN"]
            assert len(apns) == 2
            if any(p.initials == "NMC" for p in apns):
                assert assignment.date.weekday() in {0, 1}

    # Vacation blocking
    vacation_week = {date(2026, 2, 2) + timedelta(days=i) for i in range(5)}
    for assignment in schedule.assignments:
        if assignment.date in vacation_week:
            for provider in assignment.providers:
                assert provider.initials not in {"JOO", "APZ"}

    # Weekend call fairness mapping: Friday mirrored to weekend Friday cell
    friday_call = next(
        call.label for call in schedule.call_assignments if call.call_type == "noninvasive_weekday" and call.date.weekday() == 4
    )
    weekend_friday = next(
        call.label for call in schedule.call_assignments if call.call_type == "weekend_noninv" and call.date.weekday() == 4
    )
    assert friday_call == weekend_friday

    # Holiday coverage skipped for MLK Day
    mlk_day = date(2026, 1, 19)
    assert all(assignment.date != mlk_day for assignment in schedule.assignments)