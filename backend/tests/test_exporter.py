from __future__ import annotations

import hashlib
import io
from datetime import date
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from app.services.seed import seed_all
from app.solver import export_week
from app.solver.engine import solve_schedule

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


START = date(2026, 1, 5)
END = date(2026, 3, 27)


def test_export_matches_golden(session, tmp_path):
    seed_all(session)
    schedule = solve_schedule(session, START, END)
    data = export_week(schedule, START)

    export_path = tmp_path / "export.xlsx"
    export_path.write_bytes(data)

    from pathlib import Path

    golden_path = Path(__file__).parent / "data" / "golden_week1.xlsx"
    golden = golden_path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == hashlib.sha256(golden).hexdigest()

    with ZipFile(io.BytesIO(data)) as zf:
        sheet_xml = zf.read("xl/worksheets/sheet1.xml")
    root = ET.fromstring(sheet_xml)
    for cell in root.findall('.//main:c', namespaces=NS):
        ref = cell.attrib.get("r", "")
        assert not ref.startswith("O")
        assert not ref.startswith("S")
        assert not ref.startswith("T")