#!/usr/bin/env python3
import csv
import json
import os
from bisect import bisect_right
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
LEGACY_DATA_PATH = ROOT / "data.json"
USERS_CSV_PATH = ROOT / "docs" / "data" / "users.csv"
USERS_SOURCE_DIR = ROOT / "data" / "users"
CAL_OUTPUT_DIR = ROOT / "docs" / "cal"
APP_USERS_OUTPUT_DIR = ROOT / "docs" / "data" / "users"
LEGACY_CAL_OUTPUT_PATH = ROOT / "docs" / "calendar.ics"
LEGACY_APP_OUTPUT_PATH = ROOT / "docs" / "app" / "data.json"

HYPOTHETICAL_WINDOW_DAYS = 5


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def phase_for_day_short(day_in_cycle: int, cycle_length: int, period_length: int) -> tuple[str, str]:
    ovulation_day = cycle_length - 14
    if 1 <= day_in_cycle <= period_length:
        return "Men", "🩸"
    if day_in_cycle == ovulation_day:
        return "Ovl", "⭐"
    if day_in_cycle > ovulation_day:
        return "Lut", "🌙"
    return "Fol", "🌿"


def format_summary(day_in_cycle: int, phase_short: str, emoji: str) -> str:
    if phase_short == "Men":
        if day_in_cycle <= 3:
            return f"{day_in_cycle}{emoji}"
        return f"{day_in_cycle} {emoji}"
    return f"{day_in_cycle} {emoji} {phase_short}"


def format_hypothetical(day_in_cycle: int, emoji: str) -> str:
    return f"{day_in_cycle}{emoji}"


def cycle_start_for_date(current: date, starts: list[date]) -> date:
    if not starts:
        return current
    index = bisect_right(starts, current) - 1
    if index < 0:
        return starts[0]
    return starts[index]


def build_ics(
    calendar_name: str,
    start_date: date,
    end_date: date,
    cycle_starts: list[date],
    last_known_start: date,
    cycle_length: int,
    period_length: int,
) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//cycle-overlay//Cycle Calendar//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{calendar_name}",
    ]

    total_days = (end_date - start_date).days + 1
    next_cycle_start = last_known_start + timedelta(days=cycle_length)
    window_end = next_cycle_start + timedelta(days=HYPOTHETICAL_WINDOW_DAYS - 1)
    for offset in range(total_days):
        current = start_date + timedelta(days=offset)
        if next_cycle_start <= current <= window_end:
            hypothetical_day = (current - next_cycle_start).days + 1
            hypothetical_emoji = "🩸" if hypothetical_day <= period_length else "🌿"
            current_cycle_day = cycle_length + hypothetical_day
            summary = (
                f"{current_cycle_day} 🌙 Lut "
                f"({format_hypothetical(hypothetical_day, hypothetical_emoji)})"
            )
        else:
            cycle_start = cycle_start_for_date(current, cycle_starts)
            day_in_cycle = (current - cycle_start).days + 1
            phase_short, emoji = phase_for_day_short(day_in_cycle, cycle_length, period_length)
            summary = format_summary(day_in_cycle, phase_short, emoji)

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


def compute_status(
    today: date,
    last_period_start: date,
    history: list[str],
    cycle_length: int,
    period_length: int,
    source: str,
) -> dict:
    previous_period_start = history[-2] if len(history) >= 2 else None
    history_dates = []
    for item in history:
        try:
            history_dates.append(parse_date(item))
        except ValueError:
            continue

    last_cycle_length_days = None
    if previous_period_start:
        try:
            last_cycle_length_days = (last_period_start - parse_date(previous_period_start)).days
        except ValueError:
            last_cycle_length_days = None

    avg_cycle_length_days = cycle_length
    if len(history_dates) >= 3:
        diffs = []
        for index in range(1, len(history_dates)):
            diff = (history_dates[index] - history_dates[index - 1]).days
            if diff > 0:
                diffs.append(diff)
        if diffs:
            avg_cycle_length_days = int(round(sum(diffs) / len(diffs)))

    delta_days = (today - last_period_start).days
    cycle_day = delta_days + 1 if delta_days >= 0 else 0
    ovulation_day = avg_cycle_length_days - 14

    if 1 <= cycle_day <= period_length:
        phase_short = "Men"
        phase = "Menstruation"
        phase_emoji = "🩸"
    elif cycle_day == ovulation_day:
        phase_short = "Ovu"
        phase = "Ovulation"
        phase_emoji = "⭐"
    elif cycle_day > ovulation_day and cycle_day > 0:
        phase_short = "Lut"
        phase = "Luteal"
        phase_emoji = "🌙"
    else:
        phase_short = "Fol"
        phase = "Follicular"
        phase_emoji = "🌿"

    predicted_next_start = last_period_start + timedelta(days=avg_cycle_length_days)
    predicted_ovulation_day = predicted_next_start - timedelta(days=14)

    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    return {
        "cycleStart": last_period_start.isoformat(),
        "cycleLength": cycle_length,
        "generatedAt": generated_at,
        "source": source,
        "generated_at": generated_at,
        "today": today.isoformat(),
        "last_period_start": last_period_start.isoformat(),
        "previous_period_start": previous_period_start,
        "history": history,
        "cycle_day": cycle_day,
        "phase": phase,
        "phase_short": phase_short,
        "phase_emoji": phase_emoji,
        "last_cycle_length_days": last_cycle_length_days,
        "avg_cycle_length_days": avg_cycle_length_days,
        "predicted_next_start": predicted_next_start.isoformat(),
        "predicted_ovulation_day": predicted_ovulation_day.isoformat(),
        "note": "Predictions are approximate (±2–3 days).",
    }


def load_user_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            token = (row.get("token") or "").strip()
            start_date = (row.get("startDate") or "").strip()
            label = (row.get("label") or token).strip()
            cycle_length_raw = (row.get("cycleLength") or "").strip()
            cycle_length = None
            if cycle_length_raw.isdigit():
                cycle_length = int(cycle_length_raw)
            if token and start_date:
                rows.append(
                    {
                        "token": token,
                        "label": label,
                        "start_date": start_date,
                        "cycle_length": cycle_length,
                    }
                )
        return rows


def normalize_history(history: list[str], start_date: str) -> list[str]:
    values = []
    seen = set()
    for item in history:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if not value:
            continue
        try:
            parse_date(value)
        except ValueError:
            continue
        if value in seen:
            continue
        seen.add(value)
        values.append(value)
    if start_date not in seen:
        values.append(start_date)
    values.sort()
    return values


def ensure_user_source(path: Path, start_date: str, cycle_length: Optional[int]) -> dict:
    data = {}
    if path.exists():
        try:
            data = load_json(path)
        except json.JSONDecodeError:
            data = {}

    existing_start = data.get("last_period_start")
    if isinstance(existing_start, str) and existing_start.strip():
        start = existing_start.strip()
    else:
        start = start_date

    history = data.get("history")
    if not isinstance(history, list):
        history = []
    history = normalize_history(history, start)

    next_data = {
        "last_period_start": start,
        "history": history,
    }
    if isinstance(data.get("cycle_length"), int):
        next_data["cycle_length"] = data["cycle_length"]
    elif cycle_length is not None:
        next_data["cycle_length"] = cycle_length

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(next_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return next_data


def generate_one(
    token: str,
    label: str,
    cycle_data: dict,
    cycle_length: int,
    period_length: int,
    months_ahead: int,
    calendar_name: str,
    source: str,
) -> tuple[str, dict]:
    last_period_start = parse_date(cycle_data["last_period_start"])
    history_values = cycle_data.get("history", [])
    history = [item for item in history_values if isinstance(item, str) and item.strip()]

    today = datetime.utcnow().date()
    days_ahead = 365 if months_ahead == 12 else int(round(months_ahead * 30.5))
    end_date = today + timedelta(days=days_ahead)

    cycle_starts = [last_period_start]
    for item in history:
        try:
            cycle_starts.append(parse_date(item))
        except ValueError:
            continue
    cycle_starts = sorted(set(cycle_starts))
    start_date = cycle_starts[0]
    last_known_start = cycle_starts[-1]

    next_start = last_known_start + timedelta(days=cycle_length)
    while next_start <= end_date:
        cycle_starts.append(next_start)
        next_start += timedelta(days=cycle_length)

    calendar_title = f"{calendar_name} - {label}" if label else calendar_name
    ics_text = build_ics(
        calendar_title,
        start_date,
        end_date,
        cycle_starts,
        last_known_start,
        cycle_length,
        period_length,
    )

    status = compute_status(
        today=today,
        last_period_start=last_period_start,
        history=history,
        cycle_length=cycle_length,
        period_length=period_length,
        source=source,
    )
    status["token"] = token
    status["label"] = label

    return ics_text, status


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> None:
    config = load_json(CONFIG_PATH)
    cycle_length_default = int(config.get("cycle_length", 28))
    period_length = int(config.get("period_length", 3))
    months_ahead = int(config.get("months_ahead", 12))
    calendar_name = str(config.get("calendar_name", "Cycle"))
    source = os.environ.get("STATUS_SOURCE", "schedule")

    rows = load_user_rows(USERS_CSV_PATH)

    generated = []
    for row in rows:
        token = row["token"]
        label = row["label"]
        row_start = row["start_date"]
        row_cycle_length = row["cycle_length"]

        source_path = USERS_SOURCE_DIR / f"{token}.json"
        source_data = ensure_user_source(source_path, row_start, row_cycle_length)

        cycle_length = int(source_data.get("cycle_length") or row_cycle_length or cycle_length_default)
        ics_text, status = generate_one(
            token=token,
            label=label,
            cycle_data=source_data,
            cycle_length=cycle_length,
            period_length=period_length,
            months_ahead=months_ahead,
            calendar_name=calendar_name,
            source=source,
        )

        write_text(CAL_OUTPUT_DIR / f"{token}.ics", ics_text)
        write_json(APP_USERS_OUTPUT_DIR / f"{token}.json", status)
        generated.append({"token": token, "status": status, "ics": ics_text})

    # Backward compatibility for old single-user URLs.
    if generated:
        write_text(LEGACY_CAL_OUTPUT_PATH, generated[0]["ics"])
        write_json(LEGACY_APP_OUTPUT_PATH, generated[0]["status"])
    elif LEGACY_DATA_PATH.exists():
        legacy_data = load_json(LEGACY_DATA_PATH)
        legacy_cycle_length = int(legacy_data.get("cycle_length") or cycle_length_default)
        ics_text, status = generate_one(
            token="legacy",
            label="Legacy",
            cycle_data=legacy_data,
            cycle_length=legacy_cycle_length,
            period_length=period_length,
            months_ahead=months_ahead,
            calendar_name=calendar_name,
            source=source,
        )
        write_text(LEGACY_CAL_OUTPUT_PATH, ics_text)
        write_json(LEGACY_APP_OUTPUT_PATH, status)


if __name__ == "__main__":
    main()
