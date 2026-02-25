# Start New Cycle Persistence Notes

## Source of truth
- Canonical cycle start source is `data.json` at repo root.
- `docs/app/data.json` and `docs/calendar.ics` are generated outputs from `scripts/generate_ics.py`.
- `config.json` now contains only generation settings (`cycle_length`, `period_length`, `months_ahead`, `calendar_name`).

## Start new cycle button behavior (static site)
- The app is hosted on GitHub Pages and has no backend token service.
- Button updates local UI + `localStorage` only.
- App now explicitly tells the user this is device-only and links to:
  - edit `data.json`
  - run `Generate Calendar` workflow

## Manual global update flow
1. Edit `data.json` (`last_period_start` and `history`).
2. Run GitHub Actions workflow: `.github/workflows/generate.yml`.
3. Wait for Pages deploy; then all devices/incognito and subscribed ICS reflect the new date.
