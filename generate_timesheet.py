import argparse
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path
from string import Template


def load_timesheet(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_hours(value) -> str:
    if value in ("", None):
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    try:
        return f"{Decimal(str(value)):.2f}"
    except (InvalidOperation, ValueError):
        return str(value)


def wrap_editable_value(value: str, extra_attrs: str = "") -> str:
    if not value:
        return f'<span data-editable="true"{extra_attrs}></span>'
    return f'<span data-editable="true"{extra_attrs}>{value}</span>'


def wrap_editable_lines(values, extra_attrs: str = "") -> str:
    if not values:
        return wrap_editable_value("", extra_attrs)
    return "<br>".join(
        wrap_editable_value(val, extra_attrs) for val in values if val is not None
    )


def build_title_payload(single, multiple=None) -> tuple[str, str]:
    def normalize(values):
        normalized = []
        for value in values:
            text = str(value).strip()
            if text and text not in normalized:
                normalized.append(text)
        return normalized

    collected = []
    if multiple:
        if isinstance(multiple, (list, tuple)):
            collected.extend(multiple)
        else:
            collected.append(multiple)
    titles = normalize(collected)
    if not titles:
        if isinstance(single, (list, tuple)):
            titles = normalize(single)
        else:
            titles = normalize([single])
    if not titles:
        return ("--", "")

    display = "<br>".join(escape(title) for title in titles)
    values = "|".join(titles)
    return display, values


def to_24h(value: str) -> str:
    if not value:
        return ""
    cleaned = value.strip().upper().replace(" ", "")
    for fmt in ("%I:%M%p", "%H:%M"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.strftime("%H:%M")
        except ValueError:
            continue
    return ""


def to_display_time(value: str) -> str:
    if not value:
        return "--"
    try:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.strftime("%I:%M%p")
    except ValueError:
        return value


def parse_decimal(value) -> Decimal | None:
    if value in ("", None):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def hours_from_span(raw_start: str, raw_end: str) -> Decimal:
    def to_minutes(value: str) -> int | None:
        if not value:
            return None
        parts = value.split(":")
        if len(parts) != 2:
            return None
        try:
            hours, minutes = int(parts[0]), int(parts[1])
        except ValueError:
            return None
        return hours * 60 + minutes

    start_minutes = to_minutes(raw_start)
    end_minutes = to_minutes(raw_end)
    if start_minutes is None or end_minutes is None:
        return Decimal("0")
    if end_minutes < start_minutes:
        end_minutes += 24 * 60
    elapsed = max(end_minutes - start_minutes, 0)
    return Decimal(elapsed) / Decimal(60)


def build_rows(entries):
    rows = []
    total = Decimal("0")

    for index, entry in enumerate(entries):
        day = escape(entry.get("day", ""))
        date = escape(entry.get("date", ""))
        shifts = entry.get("shifts") or []

        start_entries = []
        end_entries = []
        day_total = Decimal("0")

        if not shifts:
            shifts = [{}]

        for shift_index, shift in enumerate(shifts):
            raw_start = to_24h(str(shift.get("start", "")))
            raw_end = to_24h(str(shift.get("end", "")))
            display_start = escape(to_display_time(raw_start))
            display_end = escape(to_display_time(raw_end))

            hours_value = parse_decimal(shift.get("hours"))
            if hours_value is None:
                hours_value = hours_from_span(raw_start, raw_end)
            day_total += hours_value

            start_entries.append(
                "<div class=\"shift-entry\" "
                f"data-day-index=\"{index}\" data-shift-index=\"{shift_index}\">"
                f"<span data-shift-display=\"start\" data-day-index=\"{index}\" "
                f"data-shift-index=\"{shift_index}\" data-raw-value=\"{raw_start}\">"
                f"{display_start}</span>"
                f"<input class=\"time-input\" type=\"time\" data-shift-input=\"start\" "
                f"data-day-index=\"{index}\" data-shift-index=\"{shift_index}\" "
                f"value=\"{raw_start}\">"
                "<button type=\"button\" class=\"shift-remove\" "
                f"data-day-index=\"{index}\" data-shift-index=\"{shift_index}\">&times;</button>"
                "</div>"
            )

            end_entries.append(
                "<div class=\"shift-entry\" "
                f"data-day-index=\"{index}\" data-shift-index=\"{shift_index}\">"
                f"<span data-shift-display=\"end\" data-day-index=\"{index}\" "
                f"data-shift-index=\"{shift_index}\" data-raw-value=\"{raw_end}\">"
                f"{display_end}</span>"
                f"<input class=\"time-input\" type=\"time\" data-shift-input=\"end\" "
                f"data-day-index=\"{index}\" data-shift-index=\"{shift_index}\" "
                f"value=\"{raw_end}\">"
                "</div>"
            )

        total += day_total
        hours_display = format_hours(day_total) if day_total else "0.00"

        rows.append(
            "<tr>"
            f"<td>{wrap_editable_value(day)}</td>"
            f"<td>{wrap_editable_value(date, f' data-date-cell=\"true\" data-day-offset=\"{index}\"')}</td>"
            f"<td>"
            f"<div class=\"shift-list\" data-day-index=\"{index}\" data-shift-side=\"start\">"
            f"{''.join(start_entries)}"
            "</div>"
            f"<button type=\"button\" class=\"shift-add\" data-day-index=\"{index}\">+ Add Shift</button>"
            "</td>"
            f"<td>"
            f"<div class=\"shift-list\" data-day-index=\"{index}\" data-shift-side=\"end\">"
            f"{''.join(end_entries)}"
            "</div>"
            "</td>"
            f"<td class=\"hours\"><span data-day-hours=\"true\" data-hours-cell=\"true\" "
            f"data-day-index=\"{index}\">{hours_display}</span></td>"
            "</tr>"
        )

    return "\n          ".join(rows), format_hours(total)


def render(template_path: Path, data: dict) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    rows, total_hours = build_rows(data.get("entries", []))
    title_display, title_values = build_title_payload(
        data.get("employee_title", ""), data.get("employee_titles")
    )
    payload = {
        "client_name": escape(data.get("client_name", "")),
        "employee_name": escape(data.get("employee_name", "")),
        "employee_title_display": title_display,
        "employee_title_values": escape(title_values),
        "employee_phone": escape(data.get("employee_phone", "")),
        "employee_email": escape(data.get("employee_email", "")),
        "week_start": escape(data.get("week_start", "")),
        "week_end": escape(data.get("week_end", "")),
        "rows": rows,
        "total_hours": total_hours,
    }

    signatures = data.get("signatures", {})
    payload.update(
        {
            "employee_signature": escape(signatures.get("employee_signature", "")),
            "employee_signature_date": escape(
                signatures.get("employee_signature_date", "")
            ),
            "supervisor_signature": escape(
                signatures.get("supervisor_signature", "")
            ),
            "supervisor_signature_date": escape(
                signatures.get("supervisor_signature_date", "")
            ),
        }
    )

    return template.safe_substitute(payload)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an HTML timesheet from JSON data."
    )
    parser.add_argument("data", type=Path, help="Path to timesheet JSON file.")
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        default=Path("timesheet_template (1).html"),
        help="Path to the HTML template file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("timesheet.html"),
        help="Where to write the rendered HTML.",
    )

    args = parser.parse_args()

    data = load_timesheet(args.data)
    html = render(args.template, data)
    args.output.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
