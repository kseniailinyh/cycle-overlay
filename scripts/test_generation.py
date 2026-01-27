#!/usr/bin/env python3
from datetime import date, timedelta

from generate_ics import build_ics


def parse_events(ics_text: str) -> dict[str, str]:
    events = {}
    for block in ics_text.split("BEGIN:VEVENT")[1:]:
        dtstart = None
        summary = None
        for line in block.splitlines():
            if line.startswith("DTSTART;VALUE=DATE:"):
                dtstart = line.split(":", 1)[1].strip()
            if line.startswith("SUMMARY:"):
                summary = line.split(":", 1)[1].strip()
        if dtstart and summary:
            events[dtstart] = summary
    return events


def main() -> None:
    start_date = date(2026, 1, 1)
    end_date = start_date + timedelta(days=40)
    cycle_length = 28
    period_length = 3

    cycle_starts = [start_date]
    next_start = start_date + timedelta(days=cycle_length)
    while next_start <= end_date:
        cycle_starts.append(next_start)
        next_start += timedelta(days=cycle_length)

    ics_text = build_ics(
        "Cycle",
        start_date,
        end_date,
        cycle_starts,
        start_date,
        cycle_length,
        period_length,
    )
    events = parse_events(ics_text)

    expected_count = (end_date - start_date).days + 1
    if len(events) != expected_count:
        raise SystemExit(f"Expected {expected_count} events, got {len(events)}")

    if any(" Men" in summary for summary in events.values()):
        raise SystemExit("Found forbidden 'Men' label in summary")
    if any(summary.startswith("0") for summary in events.values()):
        raise SystemExit("Found leading zero in summary")
    if any(" Ovu" in summary for summary in events.values()):
        raise SystemExit("Found 'Ovu' label in summary")

    day_28 = (start_date + timedelta(days=27)).strftime("%Y%m%d")
    day_29 = (start_date + timedelta(days=28)).strftime("%Y%m%d")
    day_33 = (start_date + timedelta(days=32)).strftime("%Y%m%d")
    day_34 = (start_date + timedelta(days=33)).strftime("%Y%m%d")
    day_14 = (start_date + timedelta(days=13)).strftime("%Y%m%d")

    if events[day_28] != "28 🌙 Lut":
        raise SystemExit(f"Unexpected day 28 summary: {events[day_28]}")
    if events[day_29] != "🌙 Lut (1🩸)":
        raise SystemExit(f"Unexpected day 29 summary: {events[day_29]}")
    if events[day_33] != "🌙 Lut (5🌿)":
        raise SystemExit(f"Unexpected day 33 summary: {events[day_33]}")
    if events[day_34] != "6 🌿 Fol":
        raise SystemExit(f"Unexpected day 34 summary: {events[day_34]}")
    if events[day_14] != "14 ⭐ Ovl":
        raise SystemExit(f"Unexpected ovulation label: {events[day_14]}")

    print("OK")


if __name__ == "__main__":
    main()
