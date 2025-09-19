from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from app.db.session import InMemorySession
from app.models import (
    CoverageRequirement,
    Holiday,
    Provider,
    SiteHospital,
    SiteOffice,
    VacationAllowance,
    VacationRequest,
)


@dataclass
class ProviderSeed:
    initials: str
    full_name: str
    type: str
    specialty: str
    is_invasive: bool
    is_ep: bool
    home_office_code: str
    privileges: dict
    weekend_team_eligible: bool = True
    notes: str | None = None


OFFICES = [
    ("HH", "Haddon Heights Office"),
    ("HH3", "Haddon Heights 3"),
    ("SVI", "South Jersey Vein Institute"),
    ("WT", "Washington Township Office"),
    ("ELM", "Elmer Office"),
    ("MAR", "Marlton Office"),
    ("VOR", "Voorhees Office"),
]

HOSPITALS = [
    ("COO", "Cooper Clinical"),
    ("VMA", "Virtua Marlton"),
    ("VVO", "Virtua Voorhees"),
    ("STR", "Jeff Stratford Hospital"),
    ("CHH", "Jeff Cherry Hill Hospital"),
    ("RMC", "Regional Medical Center"),
    ("ELH", "Elmer Hospital"),
    ("WTH", "Washington Township Hospital"),
]

FEDERAL_HOLIDAYS_2026 = [
    (date(2026, 1, 1), "New Year's Day"),
    (date(2026, 1, 19), "MLK Day"),
    (date(2026, 2, 16), "Presidents Day"),
    (date(2026, 5, 25), "Memorial Day"),
    (date(2026, 7, 3), "Independence Day Observed"),
    (date(2026, 9, 7), "Labor Day"),
    (date(2026, 11, 26), "Thanksgiving"),
    (date(2026, 12, 25), "Christmas"),
]


MD_SEEDS: list[ProviderSeed] = []
APN_SEEDS: list[ProviderSeed] = []


def _build_provider_seeds() -> None:
    if MD_SEEDS:
        return

    md_privileges_template = {
        "hospital": {
            "COO": ["INT", "EP"],
            "VMA": ["NONINV"],
            "VVO": ["NONINV"],
            "STR": ["NONINV"],
            "CHH": ["NONINV"],
            "RMC": ["NONINV"],
            "ELH": ["NONINV"],
            "WTH": ["NONINV"],
        },
        "office": {code: ["GENERAL"] for code, _ in OFFICES},
    }

    invasive_pool = [
        ("DPR", "Derek Porter", True, False),
        ("APZ", "Alex Perez", True, False),
        ("AML", "Amelia Lang", True, False),
        ("VKV", "Vikram Verma", True, False),
        ("ZZR", "Zara Ruiz", True, False),
    ]

    ep_pool = [
        ("EKT", "Elliot Trent", False, True),
        ("JWW", "Jordan Wells", False, True),
        ("NMC", "Nora McCarthy", False, True),
        ("JKT", "Jamie Kato", False, True),
    ]

    noninv_pool = [
        ("JOO", "Joon Oh", False, False),
        ("RAM", "Ramon Ahn", False, False),
        ("LMS", "Liam Singh", False, False),
        ("KSG", "Katie Sung", False, False),
        ("DJT", "Danielle Truitt", False, False),
        ("RAC", "Rae Chen", False, False),
        ("HAS", "Hannah Shah", False, False),
        ("SHF", "Sharon Fields", False, False),
        ("SMC", "Samir Chawla", False, False),
        ("MCR", "Miles Carr", False, False),
        ("DAS", "Deepa Singh", False, False),
        ("BWL", "Brian Lee", False, False),
        ("CLN", "Carla Nunez", False, False),
        ("FRG", "Frances Grant", False, False),
        ("GHM", "Graham Hill", False, False),
        ("HLN", "Helen Lin", False, False),
        ("IVY", "Ivy Young", False, False),
        ("JLC", "Julia Cho", False, False),
        ("KRN", "Karen Novak", False, False),
        ("LHN", "Lena Han", False, False),
        ("MTN", "Martin Noon", False, False),
        ("NLS", "Niels Sato", False, False),
        ("OPR", "Olivia Park", False, False),
        ("PRS", "Priya Shah", False, False),
        ("QLM", "Quinn Lam", False, False),
        ("RHD", "Richard Doe", False, False),
        ("SAL", "Sasha Lee", False, False),
        ("TOM", "Tomas Ortega", False, False),
        ("UGO", "Uma Gomez", False, False),
        ("VIN", "Vince Nolan", False, False),
        ("WES", "Wes Stone", False, False),
        ("XAV", "Xavier Pace", False, False),
        ("YUK", "Yuki Chan", False, False),
        ("ZED", "Zed Duran", False, False),
    ]

    for init, name, inv, ep in invasive_pool + ep_pool + noninv_pool:
        privileges = md_privileges_template.copy()
        is_ep = ep
        is_inv = inv
        if ep:
            privileges = {
                **md_privileges_template,
                "hospital": {**md_privileges_template["hospital"], "COO": ["EP"], "RMC": ["EP"]},
            }
        if inv:
            privileges = {
                **md_privileges_template,
                "hospital": {**md_privileges_template["hospital"], "COO": ["INT"], "RMC": ["INT"], "WTH": ["INT"]},
            }
        MD_SEEDS.append(
            ProviderSeed(
                initials=init,
                full_name=name,
                type="MD",
                specialty="Cardiology",
                is_invasive=is_inv,
                is_ep=is_ep,
                home_office_code="HH",
                privileges=privileges,
            )
        )

    apn_privileges = {
        "hospital": {
            "RMC": ["APN"],
            "WTH": ["APN"],
            "COO": ["APN"],
            "CHH": ["APN"],
        },
        "office": {code: ["APN"] for code, _ in OFFICES},
    }

    apn_pool = [
        ("VJC", "Valerie Cruz", "APN", False, False),
        ("JKT", "Jenna Kurt", "APN", False, True),
        ("NMC", "Nora McCarthy", "APN", False, True),
        ("MB", "Mara Blake", "APN", False, False),
        ("AG", "Ariel Grant", "APN", False, False),
        ("KC", "Kayla Choi", "APN", False, False),
        ("ACS", "Alan Chen", "APN", False, False),
        ("AD", "Alice Dwyer", "APN", False, False),
        ("MJK", "Mia Keller", "APN", False, False),
        ("RAM", "Rita Monroe", "APN", False, False),
    ]

    for init, name, typ, inv, ep in apn_pool:
        weekend = init not in {"MJK"}
        APN_SEEDS.append(
            ProviderSeed(
                initials=init,
                full_name=name,
                type=typ,
                specialty="APN",
                is_invasive=inv,
                is_ep=ep,
                home_office_code="HH",
                privileges=apn_privileges,
                weekend_team_eligible=weekend,
            )
        )


def seed_core(session: InMemorySession) -> None:
    _build_provider_seeds()

    office_lookup = {}
    for code, name in OFFICES:
        office = SiteOffice(code=code, name=name)
        session.add(office)
        office_lookup[code] = office

    hospital_lookup = {}
    for code, name in HOSPITALS:
        hospital = SiteHospital(code=code, name=name)
        session.add(hospital)
        hospital_lookup[code] = hospital

    session.flush()

    for provider_seed in MD_SEEDS + APN_SEEDS:
        provider = Provider(
            initials=provider_seed.initials,
            full_name=provider_seed.full_name,
            type=provider_seed.type,
            specialty=provider_seed.specialty,
            is_invasive=provider_seed.is_invasive,
            is_ep=provider_seed.is_ep,
            home_office_id=office_lookup[provider_seed.home_office_code].id,
            privileges_json=provider_seed.privileges,
            weekend_team_eligible=provider_seed.weekend_team_eligible,
            notes=provider_seed.notes,
        )
        session.add(provider)

    for holiday_date, name in FEDERAL_HOLIDAYS_2026:
        session.add(Holiday(date=holiday_date, name=name, is_office_closed=True, extend_weekend=True))

    for provider in session.all(Provider):
        session.add(
            VacationAllowance(
                provider_id=provider.id,
                year=2026,
                days_total=30 if provider.type == "MD" else 25,
                days_used=0,
                am_quota=10,
                pm_quota=10,
            )
        )

    session.commit()


def seed_vacations(session: InMemorySession) -> None:
    targets = {"JOO", "APZ"}
    for provider in session.all(Provider):
        if provider.initials not in targets:
            continue
        session.add(
            VacationRequest(
                provider_id=provider.id,
                start_date=date(2026, 2, 2),
                end_date=date(2026, 2, 6),
                block="FULLWEEK",
                status="APPROVED",
            )
        )
    session.commit()


def seed_coverage(session: InMemorySession) -> None:
    # Minimal coverage requirements for tests
    hospitals = {h.code: h.id for h in session.all(SiteHospital)}
    offices = {o.code: o.id for o in session.all(SiteOffice)}

    def add_req(site_type: str, site_code: str, dow: int, block: str, min_md: int, min_apn: int, roles: dict | None = None) -> None:
        session.add(
            CoverageRequirement(
                site_type=site_type,
                site_id=(hospitals if site_type == "hospital" else offices)[site_code],
                day_of_week=dow,
                block=block,
                min_md=min_md,
                min_apn=min_apn,
                roles_json=roles or {},
            )
        )

    for dow in range(5):
        add_req("office", "HH", dow, "AM", 1, 0)
        add_req("office", "HH", dow, "PM", 1, 0)
        add_req("office", "SVI", dow, "AM", 1, 0)
        add_req("office", "SVI", dow, "PM", 1, 0)
        add_req("office", "WT", dow, "AM", 1, 0)
        add_req("office", "WT", dow, "PM", 1, 0)
        add_req("office", "HH3", dow, "AM", 1, 0)
        add_req("office", "HH3", dow, "PM", 1, 0)

    # WT hospital requirement 1 MD + 2 APNs
    for dow in range(5):
        add_req("hospital", "WTH", dow, "AM", 1, 2, roles={"md": 1, "apn": 2})
        add_req("hospital", "WTH", dow, "PM", 1, 2, roles={"md": 1, "apn": 2})

    # RMC pairing
    for dow in range(5):
        add_req("hospital", "RMC", dow, "AM", 1, 1, roles={"pair": True})
        add_req("hospital", "RMC", dow, "PM", 1, 1, roles={"pair": True})

    # OBL only Wednesday
    add_req("hospital", "COO", 2, "AM", 1, 0, roles={"obl": True})
    add_req("hospital", "COO", 2, "PM", 1, 0, roles={"obl": True})

    session.commit()


def seed_all(session: Session) -> None:
    seed_core(session)
    seed_vacations(session)
    seed_coverage(session)