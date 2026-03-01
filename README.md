# Cycle Overlay Calendar

This repository generates per-user iCalendar (`.ics`) files and per-user dashboard status JSON files.

## Data model

- Source of truth per user: `data/users/<token>.json`
- User registry: `docs/data/users.csv` (`token`, `startDate`, `cycleLength`, links)
- Generated calendar per user: `docs/cal/<token>.ics`
- Generated app status per user: `docs/data/users/<token>.json`

## Configure

1. Add/update user row in `docs/data/users.csv`.
   - `startDate` is required for brand-new users.
   - For existing users with `data/users/<token>.json`, `startDate` can be left empty.
2. Ensure `data/users/<token>.json` exists for that token.

User source file format:

```json
{
  "last_period_start": "2026-02-03",
  "history": ["2026-02-03"],
  "cycle_length": 28
}
```

Global defaults are in `config.json`:

- `cycle_length`
- `period_length`
- `months_ahead`
- `calendar_name`

## Dashboard URL

Open dashboard with token:

```text
https://<username>.github.io/<repo>/app/?t=<token>
```

Optional explicit API override:

```text
https://<username>.github.io/<repo>/app/?t=<token>&api=https://<worker-domain>
```

## Local generation

```bash
python3 scripts/generate_ics.py
```

## GitHub Actions

Workflow `.github/workflows/generate.yml` regenerates all users on:

- push affecting `data/**`, `docs/data/users.csv`, generation code
- manual `workflow_dispatch` with `token` + `cycle_start`
