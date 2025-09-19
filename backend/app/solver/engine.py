from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from app.config import load as load_rules
from app.core.config import settings
from app.db.session import InMemorySession
from app.models import Holiday, Provider, SiteHospital, SiteOffice, VacationRequest


@dataclass
class DayAssignment:
    date: date
    block: str
    site_code: str
    site_type: str
    providers: list[Provider]


@dataclass
class CallAssignment:
    date: date
    call_type: str
    label: str
    providers: list[Provider]


class ScheduleOutput:
    def __init__(self) -> None:
        self.assignments: list[DayAssignment] = []
        self.call_assignments: list[CallAssignment] = []
        self.vacations: dict[str, list[tuple[date, date, str]]] = defaultdict(list)
        self.icd_sites: dict[date, str] = {}

    def add_assignment(self, assignment: DayAssignment) -> None:
        self.assignments.append(assignment)

    def add_call(self, call: CallAssignment) -> None:
        self.call_assignments.append(call)


class ScheduleSolver:
    def __init__(self, session: InMemorySession) -> None:
        self.session = session
        self.providers: list[Provider] = session.all(Provider)
        self.providers_by_initials = {p.initials: p for p in self.providers}
        self.holidays = {h.date: h for h in session.all(Holiday)}
        self.offices = {o.code: o for o in session.all(SiteOffice)}
        self.hospitals = {h.code: h for h in session.all(SiteHospital)}
        self.rules = load_rules()
        self.vacations = self._build_vacation_lookup()
        self.output = ScheduleOutput()

    def _build_vacation_lookup(self) -> dict[int, set[date]]:
        lookup: dict[int, set[date]] = defaultdict(set)
        vacations = [v for v in self.session.all(VacationRequest) if v.status == "APPROVED"]
        for vacation in vacations:
            current = vacation.start_date
            while current <= vacation.end_date:
                lookup[vacation.provider_id].add(current)
                current += timedelta(days=1)
        return lookup

    # provider filters -------------------------------------------------
    def _eligible(self, provider: Provider, site_code: str, site_type: str, block: str, day: date) -> bool:
        if provider.initials == "MJK":
            return False
        if day in self.vacations.get(provider.id, set()):
            return False
        if site_type == "hospital":
            # weekend restrictions
            if provider.type == "MD":
                if provider.initials in {"RAC", "HAS", "DAS"}:
                    return False
                if provider.initials == "SMC" and site_code != "RMC":
                    return False
                if provider.initials == "SHF" and site_code not in {"ELH"}:
                    return False
                if provider.initials == "MCR" and site_code not in {"ELH"}:
                    return False
            else:
                if provider.initials == "AD" and site_code not in {"WTH", "CHH"}:
                    return False
                if provider.initials == "VJC" and site_code not in {"RMC"}:
                    return False
                if provider.initials == "JKT" and site_code not in {"RMC"}:
                    return False
                if provider.initials == "KC" and site_code not in {"COO"}:
                    return False
                if provider.initials == "ACS" and site_code not in {"WTH"}:
                    return False
                if provider.initials == "MB" and site_code not in {"COO", "WTH", "CHH"}:
                    return False
                if provider.initials == "AG" and site_code not in {"COO", "WTH"}:
                    return False
            privileges = provider.privileges_json.get("hospital", {})
        else:
            if provider.initials == "SMC" and site_code != "SVI":
                return False
            if provider.initials == "RAC" and site_code not in {"ELM", "SVI", "WT", "HH3", "HH"}:
                return False
            if provider.initials == "HAS" and site_code not in {"HH", "HH3", "SVI", "WT"}:
                return False
            if provider.initials == "SHF" and site_code not in {"ELM", "WT", "SVI", "HH3"}:
                return False
            if provider.initials == "DAS" and site_code not in {"WT", "MAR", "SVI", "HH"}:
                return False
            if provider.initials == "MCR" and site_code not in {"SVI", "ELM", "MAR"}:
                return False
            if provider.type == "APN":
                if provider.initials == "VJC" and site_code not in {"SVI", "ELM"}:
                    return False
                if provider.initials == "JKT" and site_code not in {"SVI", "ELM"}:
                    return False
                if provider.initials == "KC" and site_code not in {"VEIN", "PVD"}:
                    return False
                if provider.initials == "ACS" and site_code not in {"VEIN", "WT"}:
                    return False
                if provider.initials == "AD" and site_code not in {"VEIN"}:
                    return False
                if provider.initials == "MB":
                    return False
                if provider.initials == "AG" and site_code not in {"VEIN"}:
                    return False
            privileges = provider.privileges_json.get("office", {})

        allowed_roles = privileges.get(site_code)
        if allowed_roles is None:
            # allow derived special codes
            if site_code == "COO_OBL":
                allowed_roles = privileges.get("COO")
            elif site_code in {"VEIN", "PVD"}:
                allowed_roles = privileges.get("WT")
        return allowed_roles is not None

    def _md_candidates(self, site_code: str, block: str, day: date) -> list[Provider]:
        return [
            p
            for p in self.providers
            if p.type == "MD" and self._eligible(p, site_code, "hospital" if site_code in self.hospitals else "office", block, day)
        ]

    def _apn_candidates(self, site_code: str, block: str, day: date) -> list[Provider]:
        return [
            p
            for p in self.providers
            if p.type == "APN" and self._eligible(p, site_code, "hospital" if site_code in self.hospitals else "office", block, day)
        ]

    # solving ----------------------------------------------------------
    def solve(self, start_date: date, end_date: date) -> ScheduleOutput:
        self.output = ScheduleOutput()
        self._record_vacations()
        self._build_weekday_schedule(start_date, end_date)
        self._build_call_schedule(start_date, end_date)
        return self.output

    def _record_vacations(self) -> None:
        for provider in self.providers:
            days = sorted(self.vacations.get(provider.id, set()))
            if not days:
                continue
            start = end = days[0]
            for current in days[1:]:
                if current == end + timedelta(days=1):
                    end = current
                else:
                    self.output.vacations[provider.initials].append((start, end, "FULL"))
                    start = end = current
            self.output.vacations[provider.initials].append((start, end, "FULL"))

    def _iter_workdays(self, start: date, end: date) -> Iterable[date]:
        current = start
        while current <= end:
            if current.weekday() < 5:
                yield current
            current += timedelta(days=1)

    def _build_weekday_schedule(self, start: date, end: date) -> None:
        rotations = self.rules.get("rotations", {})
        wt_md_cycle = deque(self._providers_from_initials(rotations.get("wt_hospital_md", [])))
        wt_apn_cycle = deque(self._providers_from_initials(rotations.get("wt_hospital_apn", [])))
        rmc_md_cycle = deque(self._providers_from_initials(rotations.get("rmc_md", [])))
        rmc_apn_cycle = deque(self._providers_from_initials(rotations.get("rmc_apn", [])))
        obl_cycle = deque(self._providers_from_initials(self.rules.get("obl", {}).get("physicians", [])))

        for day in self._iter_workdays(start, end):
            holiday = self.holidays.get(day)
            is_holiday = bool(holiday and holiday.is_office_closed)
            md_assignments: dict[str, Provider] = {}
            apn_assignments: dict[str, list[Provider]] = defaultdict(list)

            if is_holiday and holiday and holiday.extend_weekend:
                # Skip weekday assignments; weekend handling later
                continue

            # WTH hospital
            if wt_md_cycle:
                md = self._advance_until(wt_md_cycle, lambda p: self._eligible(p, "WTH", "hospital", "AM", day))
                if md:
                    md_assignments["WTH"] = md
            for block in ("AM", "PM"):
                if "WTH" in md_assignments:
                    self.output.add_assignment(DayAssignment(day, block, "WTH", "hospital", [md_assignments["WTH"]]))
                apns: list[Provider] = []
                for _ in range(2):
                    apn = self._advance_until(
                        wt_apn_cycle,
                        lambda p: self._eligible(p, "WTH", "hospital", block, day)
                        and p not in apns,
                    )
                    if apn:
                        apns.append(apn)
                if apns:
                    apn_assignments[f"WTH_{block}"].extend(apns)
                    self.output.add_assignment(DayAssignment(day, block, "WTH_APN", "hospital", apns))

            # RMC hospital MD/APN pair
            for block in ("AM", "PM"):
                md = self._advance_until(rmc_md_cycle, lambda p: self._eligible(p, "RMC", "hospital", block, day))
                apn = self._advance_until(rmc_apn_cycle, lambda p: self._eligible(p, "RMC", "hospital", block, day))
                providers = [p for p in [md, apn] if p]
                if providers:
                    self.output.add_assignment(DayAssignment(day, block, "RMC", "hospital", providers))

            # Offices HH, HH3, SVI, WT
            office_codes = ["HH", "HH3", "SVI", "WT"]
            for office_code in office_codes:
                for block in ("AM", "PM"):
                    md = self._find_office_md(day, office_code, block, skip=list(md_assignments.values()))
                    if md:
                        self.output.add_assignment(DayAssignment(day, block, office_code, "office", [md]))

            # OBL on Wednesdays
            if day.weekday() == 2 and obl_cycle:
                for block in ("AM", "PM"):
                    physician = self._advance_until(obl_cycle, lambda p: self._eligible(p, "COO", "hospital", block, day))
                    if physician:
                        self.output.add_assignment(DayAssignment(day, block, "COO_OBL", "hospital", [physician]))

            # ICD clinic rotation (EP MD + two APNs)
            if self.rules.get("icd_clinic", {}).get("enabled"):
                site = "WT" if day.weekday() % 2 == 0 else "SVI"
                ep_md = self._pick_ep_md(day)
                ep_apns = self._pick_ep_apns(day)
                if ep_md and len(ep_apns) == 2:
                    self.output.icd_sites[day] = site
                    self.output.add_assignment(DayAssignment(day, "AM", f"ICD_{site}", "office", [ep_md] + ep_apns))
                    self.output.add_assignment(DayAssignment(day, "PM", f"ICD_{site}", "office", [ep_md] + ep_apns))

    def _build_call_schedule(self, start: date, end: date) -> None:
        # Weekend call rotation
        noninv_md_cycle = deque(
            [p for p in self.providers if p.type == "MD" and not p.is_invasive and not p.is_ep and p.initials not in {"HAS", "DAS"}]
        )
        inv_md_cycle = deque([p for p in self.providers if p.type == "MD" and p.is_invasive])

        current = start
        while current <= end:
            if current.weekday() == 0:
                # Build weekday call for this week (Mon-Fri)
                friday_label: str | None = None
                for offset in range(5):
                    day = current + timedelta(days=offset)
                    if day > end:
                        break
                    noninv_hh = self._advance_until(noninv_md_cycle, lambda p: day not in self.vacations.get(p.id, set()))
                    noninv_ch = self._advance_until(
                        noninv_md_cycle,
                        lambda p: day not in self.vacations.get(p.id, set()) and p != noninv_hh,
                    )
                    if noninv_hh and noninv_ch:
                        label = f"HH: {noninv_hh.initials} CH: {noninv_ch.initials}"
                        self.output.add_call(CallAssignment(day, "noninvasive_weekday", label, [noninv_hh, noninv_ch]))
                        if day.weekday() == 4:
                            friday_label = label
                    primary = self._advance_until(inv_md_cycle, lambda p: day not in self.vacations.get(p.id, set()))
                    backup = self._advance_until(inv_md_cycle, lambda p: day not in self.vacations.get(p.id, set()) and p != primary)
                    if primary and backup:
                        label = f"{primary.initials}. {backup.initials}."
                        self.output.add_call(CallAssignment(day, "interventional_weekday", label, [primary, backup]))

                # Weekend assignments (Fri-Sun)
                fri = current + timedelta(days=4)
                sat = fri + timedelta(days=1)
                sun = fri + timedelta(days=2)
                weekend_names: list[Provider] = []
                for wk_day in (fri, sat, sun):
                    provider = self._advance_until(noninv_md_cycle, lambda p: wk_day not in self.vacations.get(p.id, set()))
                    if provider:
                        weekend_names.append(provider)
                labels = [p.initials for p in weekend_names]
                if len(labels) == 3:
                    friday_text = friday_label or labels[0]
                    self.output.add_call(CallAssignment(fri, "weekend_noninv", friday_text, [weekend_names[0]]))
                    self.output.add_call(CallAssignment(sat, "weekend_noninv", labels[1], [weekend_names[1]]))
                    self.output.add_call(CallAssignment(sun, "weekend_noninv", labels[2], [weekend_names[2]]))
                    if weekend_names:
                        last_weekday = current + timedelta(days=4)
                        self.output.add_call(
                            CallAssignment(last_weekday, "interventional_weekend", weekend_names[-1].initials, [weekend_names[-1]])
                        )
            current += timedelta(days=1)

    # helper methods ---------------------------------------------------
    def _advance_until(self, pool: deque[Provider], predicate) -> Provider | None:
        if not pool:
            return None
        for _ in range(len(pool)):
            provider = pool[0]
            pool.rotate(-1)
            if predicate(provider):
                return provider
        return None

    def _providers_from_initials(self, initials_list: Iterable[str]) -> list[Provider]:
        return [self.providers_by_initials[i] for i in initials_list if i in self.providers_by_initials]

    def _find_office_md(self, day: date, office_code: str, block: str, skip: list[Provider]) -> Provider | None:
        candidates = [
            p
            for p in self.providers
            if p.type == "MD"
            and not p.is_invasive
            and self._eligible(p, office_code, "office", block, day)
            and p not in skip
            and day not in self.vacations.get(p.id, set())
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda p: (p.seniority or 0, p.initials))
        return candidates[0]

    def _pick_ep_md(self, day: date) -> Provider | None:
        pool = self._providers_from_initials(self.rules.get("icd_clinic", {}).get("ep_mds", []))
        for provider in pool:
            if day not in self.vacations.get(provider.id, set()):
                return provider
        return None

    def _pick_ep_apns(self, day: date) -> list[Provider]:
        pool = self._providers_from_initials(self.rules.get("icd_clinic", {}).get("ep_apns", []))
        selected: list[Provider] = []
        nmc_days = set(self.rules.get("icd_clinic", {}).get("nmc_days", []))
        for provider in pool:
            if provider.initials == "NMC" and day.weekday() not in nmc_days:
                continue
            if day in self.vacations.get(provider.id, set()):
                continue
            selected.append(provider)
        if len(selected) < 2:
            return []
        return selected[:2]


def solve_schedule(session: InMemorySession, start_date: date, end_date: date) -> ScheduleOutput:
    solver = ScheduleSolver(session)
    return solver.solve(start_date, end_date)