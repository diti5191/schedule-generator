from __future__ import annotations

import io
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET
import zipfile

import json

from app.core.config import settings
from app.solver.engine import ScheduleOutput

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"main": MAIN_NS}


ROW_OFFSETS = {
    0: {"AM": 11, "PM": 13},
    1: {"AM": 16, "PM": 18},
    2: {"AM": 21, "PM": 23},
    3: {"AM": 26, "PM": 28},
    4: {"AM": 31, "PM": 33},
}

WEEKDAY_LABELS = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}
VACATION_ABBREV = {0: "M", 1: "T", 2: "W", 3: "Th", 4: "F", 5: "Sa", 6: "Su"}


def load_mapping(path: Path | None = None) -> dict:
    target = path or settings.mapping_config_path
    with target.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _ensure_row(sheet_data: ET.Element, row_index: int) -> ET.Element:
    row_tag = f"{{{MAIN_NS}}}row"
    for row in sheet_data.findall(row_tag):
        if int(row.attrib.get("r", "0")) == row_index:
            return row
    row = ET.Element(row_tag, {"r": str(row_index)})
    sheet_data.append(row)
    return row


def _set_cell(row: ET.Element, cell_ref: str, value: str) -> None:
    cell_tag = f"{{{MAIN_NS}}}c"
    is_tag = f"{{{MAIN_NS}}}is"
    t_tag = f"{{{MAIN_NS}}}t"

    for cell in row.findall(cell_tag):
        if cell.attrib.get("r") == cell_ref:
            for child in list(cell):
                cell.remove(child)
            break
    else:
        cell = ET.SubElement(row, cell_tag, {"r": cell_ref, "t": "inlineStr"})

    cell.attrib["t"] = "inlineStr"
    is_element = ET.SubElement(cell, is_tag)
    t_element = ET.SubElement(is_element, t_tag)
    t_element.text = value


def _cell_ref(column: str, row_index: int) -> str:
    return f"{column}{row_index}"


def _format_wt_cell(md: str | None, apns: list[str]) -> str:
    values = [md] if md else []
    values.extend(apns)
    return " / ".join(values)


def _format_rmc_cell(md: str | None, apn: str | None) -> str:
    values = [v for v in [md, apn] if v]
    return "/".join(values)


def _format_vacation_span(start: date, end: date) -> str:
    days = []
    current = start
    while current <= end:
        days.append(VACATION_ABBREV[current.weekday()])
        current += timedelta(days=1)
    if not days:
        return ""
    if len(days) == 1:
        return days[0]
    return f"{days[0]}–{days[-1]}"


def export_week(schedule: ScheduleOutput, week_start: date, template_path: Path | None = None) -> bytes:
    template = template_path or settings.template_path
    mapping = load_mapping()

    week_days = [week_start + timedelta(days=i) for i in range(5)]
    assignments_by_day: dict[date, dict[str, dict[str, list[str]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for assignment in schedule.assignments:
        if assignment.date not in week_days:
            continue
        initials = [provider.initials for provider in assignment.providers]
        assignments_by_day[assignment.date][assignment.site_code][assignment.block].extend(initials)

    # Prepare call labels
    call_labels = defaultdict(str)
    for call in schedule.call_assignments:
        if call.date not in week_days:
            continue
        call_labels[(call.call_type, call.date.weekday())] = call.label
        if call.call_type == "weekend_noninv":
            if call.date.weekday() == 4:
                call_labels[("weekend_noninv", "friday")] = call.label
            elif call.date.weekday() == 5:
                call_labels[("weekend_noninv", "saturday")] = call.label
            elif call.date.weekday() == 6:
                call_labels[("weekend_noninv", "sunday")] = call.label
        if call.call_type == "interventional_weekend":
            call_labels[("weekend_interv", "summary")] = call.label

    friday_label = call_labels.get(("noninvasive_weekday", 4))
    if friday_label:
        call_labels[("weekend_noninv", "friday")] = friday_label

    vacation_entries: list[str] = []
    for provider, ranges in schedule.vacations.items():
        for start, end, _ in ranges:
            if end < week_start or start > week_start + timedelta(days=6):
                continue
            span_start = max(start, week_start)
            span_end = min(end, week_start + timedelta(days=6))
            vacation_entries.append(f"{provider} — {_format_vacation_span(span_start, span_end)}")

    buffer = io.BytesIO()
    with zipfile.ZipFile(template, "r") as zf:
        with zipfile.ZipFile(buffer, "w") as output_zip:
            for item in zf.infolist():
                data = zf.read(item.filename)
                if item.filename == "xl/worksheets/sheet1.xml":
                    data = _populate_sheet(
                        data,
                        mapping,
                        week_start,
                        assignments_by_day,
                        call_labels,
                        vacation_entries,
                    )
                output_zip.writestr(item, data)
    return buffer.getvalue()


def _populate_sheet(
    xml_bytes: bytes,
    mapping: dict,
    week_start: date,
    assignments_by_day: dict,
    call_labels: dict,
    vacation_entries: list[str],
) -> bytes:
    tree = ET.fromstring(xml_bytes)
    sheet_data = tree.find("main:sheetData", NS)
    if sheet_data is None:
        raise ValueError("Invalid template: missing sheetData")

    # Weekday placements
    for idx, day in enumerate(range(5)):
        day_date = week_start + timedelta(days=idx)
        day_assignments = assignments_by_day.get(day_date, {})
        for office_code, cell_map in mapping["cells"].get("offices", {}).items():
            block_row = ROW_OFFSETS[idx]
            for block, row_index in block_row.items():
                column_ref = cell_map.get(block)
                if not column_ref:
                    continue
                initials = day_assignments.get(office_code, {}).get(block, [])
                if not initials:
                    continue
                column = ''.join(filter(str.isalpha, column_ref))
                target_ref = _cell_ref(column, row_index)
                row = _ensure_row(sheet_data, row_index)
                _set_cell(row, target_ref, "/".join(initials))

    # WT hospital
    for idx, block_row in ROW_OFFSETS.items():
        day_date = week_start + timedelta(days=idx)
        day_assignments = assignments_by_day.get(day_date, {})
        for block, row_index in block_row.items():
            column_ref = mapping["cells"]["hospitals"]["WTH"].get(block)
            column = ''.join(filter(str.isalpha, column_ref))
            md = day_assignments.get("WTH", {}).get(block, [])
            apn = day_assignments.get("WTH_APN", {}).get(block, [])
            text = _format_wt_cell(md[0] if md else None, apn)
            if text:
                row = _ensure_row(sheet_data, row_index)
                _set_cell(row, _cell_ref(column, row_index), text)

    # RMC pairs
    for idx, block_row in ROW_OFFSETS.items():
        day_date = week_start + timedelta(days=idx)
        day_assignments = assignments_by_day.get(day_date, {})
        for block, row_index in block_row.items():
            column_ref = mapping["cells"]["hospitals"]["RMC"].get(block)
            column = ''.join(filter(str.isalpha, column_ref))
            pair = day_assignments.get("RMC", {}).get(block, [])
            text = _format_rmc_cell(pair[0] if pair else None, pair[1] if len(pair) > 1 else None)
            if text:
                row = _ensure_row(sheet_data, row_index)
                _set_cell(row, _cell_ref(column, row_index), text)

    # OBL
    for idx, block_row in ROW_OFFSETS.items():
        if idx != 2:
            continue
        day_date = week_start + timedelta(days=idx)
        day_assignments = assignments_by_day.get(day_date, {})
        for block, row_index in block_row.items():
            column_ref = mapping["cells"]["hospitals"]["COO_OBL"].get(block)
            column = ''.join(filter(str.isalpha, column_ref))
            initials = day_assignments.get("COO_OBL", {}).get(block, [])
            text = initials[0] if initials else ""
            if text:
                row = _ensure_row(sheet_data, row_index)
                _set_cell(row, _cell_ref(column, row_index), text)

    # Call cells
    for call_type, cells in mapping.get("call_cells", {}).items():
        if call_type == "noninvasive_weekday":
            for weekday, cell_ref in cells.items():
                key = int(weekday)
                value = call_labels.get(("noninvasive_weekday", key), "")
                if value:
                    row_index = int(''.join(filter(str.isdigit, cell_ref)))
                    column = ''.join(filter(str.isalpha, cell_ref))
                    row = _ensure_row(sheet_data, row_index)
                    _set_cell(row, _cell_ref(column, row_index), value)
        elif call_type == "interventional_weekday":
            for weekday, cell_ref in cells.items():
                key = int(weekday)
                value = call_labels.get(("interventional_weekday", key), "")
                if value:
                    row_index = int(''.join(filter(str.isdigit, cell_ref)))
                    column = ''.join(filter(str.isalpha, cell_ref))
                    row = _ensure_row(sheet_data, row_index)
                    _set_cell(row, _cell_ref(column, row_index), value)
        elif call_type == "weekend_noninv":
            for key, cell_ref in cells.items():
                value = call_labels.get(("weekend_noninv", key), "")
                if value:
                    row_index = int(''.join(filter(str.isdigit, cell_ref)))
                    column = ''.join(filter(str.isalpha, cell_ref))
                    row = _ensure_row(sheet_data, row_index)
                    _set_cell(row, _cell_ref(column, row_index), value)
        elif call_type == "weekend_interv":
            cell_ref = cells.get("summary")
            value = call_labels.get(("weekend_interv", "summary"), "")
            if value and cell_ref:
                row_index = int(''.join(filter(str.isdigit, cell_ref)))
                column = ''.join(filter(str.isalpha, cell_ref))
                row = _ensure_row(sheet_data, row_index)
                _set_cell(row, _cell_ref(column, row_index), value)

    # Vacations header
    headers = mapping.get("vacation_headers", {}).get("order", [])
    pointer = 0
    for entry in vacation_entries:
        if pointer >= len(headers) * 7:
            break
        column = headers[pointer // 7]
        row_index = (pointer % 7) + 1
        row = _ensure_row(sheet_data, row_index)
        _set_cell(row, _cell_ref(column, row_index), entry)
        pointer += 1

    return ET.tostring(tree, encoding="utf-8", xml_declaration=True)