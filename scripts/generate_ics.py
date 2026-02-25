#!/usr/bin/env python3
import json
import os
from bisect import bisect_right
from datetime import date, datetime, timedelta
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
DATA_PATH = Path(__file__).resolve().parent.parent / "data.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "calendar.ics"
APP_DATA_PATH = Path(__file__).resolve().parent.parent / "docs" / "app" / "data.json"

HYPOTHETICAL_WINDOW_DAYS = 5


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_cycle_data(path: Path) -> tuple[date, list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing source-of-truth file: {path}")

    data = load_config(path)
    value = data.get("last_period_start")
    history = data.get("history", [])
    if not isinstance(value, str) or not value.strip():
        raise ValueError("data.json must define last_period_start as YYYY-MM-DD")

    history_list = []
    if isinstance(history, list):
        for item in history:
            if isinstance(item, str) and item.strip():
                history_list.append(item)

    return parse_date(value), history_list


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


def main() -> None:
    config = load_config(CONFIG_PATH)
    last_period_start, history = load_cycle_data(DATA_PATH)
    cycle_length = int(config.get("cycle_length", 28))
    period_length = int(config.get("period_length", 3))
    months_ahead = int(config.get("months_ahead", 12))
    calendar_name = str(config.get("calendar_name", "Cycle"))

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

    ics_text = build_ics(
        calendar_name,
        start_date,
        end_date,
        cycle_starts,
        last_known_start,
        cycle_length,
        period_length,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        f.write(ics_text)
    source = os.environ.get("STATUS_SOURCE", "schedule")
    status = compute_status(
        today=today,
        last_period_start=last_period_start,
        history=history,
        cycle_length=cycle_length,
        period_length=period_length,
        source=source,
    )
    APP_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with APP_DATA_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
