#!/usr/bin/env python3
import json
from datetime import date, datetime, timedelta
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "calendar.ics"


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def phase_for_day(day_in_cycle: int, cycle_length: int, period_length: int) -> tuple[str, str]:
    ovulation_day = cycle_length - 14
    if 1 <= day_in_cycle <= period_length:
        return "Men", "🩸"
    if day_in_cycle == ovulation_day:
        return "Ovu", "⭐"
    if day_in_cycle > ovulation_day:
        return "Lut", "🌙"
    return "Fol", "🌿"


def build_ics(calendar_name: str, start_date: date, days: int, cycle_length: int, period_length: int) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//cycle-overlay//Cycle Calendar//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{calendar_name}",
    ]

    for offset in range(days):
        current = start_date + timedelta(days=offset)
        day_in_cycle = (offset % cycle_length) + 1
        phase, emoji = phase_for_day(day_in_cycle, cycle_length, period_length)
        summary = f"{day_in_cycle:02d} {emoji} {phase}"

        dtstart = current.strftime("%Y%m%d")
        dtend = (current + timedelta(days=1)).strftime("%Y%m%d")
        uid = f"{dtstart}-cycle-overlay"

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTART;VALUE=DATE:{dtstart}",
                f"DTEND;VALUE=DATE:{dtend}",
                f"SUMMARY:{summary}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main() -> None:
    config = load_config(CONFIG_PATH)
    last_period_start = parse_date(config["last_period_start"])
    cycle_length = int(config.get("cycle_length", 28))
    period_length = int(config.get("period_length", 3))
    months_ahead = int(config.get("months_ahead", 12))
    calendar_name = str(config.get("calendar_name", "Cycle"))

    days = 365 if months_ahead == 12 else int(round(months_ahead * 30.5))
    ics_text = build_ics(calendar_name, last_period_start, days, cycle_length, period_length)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        f.write(ics_text)


if __name__ == "__main__":
    main()
