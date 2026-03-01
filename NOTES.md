# Start New Cycle Persistence Notes

## Source of truth

- Canonical source per user: `data/users/<token>.json`.
- `docs/data/users/<token>.json` and `docs/cal/<token>.ics` are generated outputs.
- `config.json` contains global generation defaults.

## Start new cycle flow

- App reads token `t` from URL and loads `docs/data/users/<token>.json`.
- Button calls Cloudflare Worker `/start?date=YYYY-MM-DD&t=<token>`.
- Worker updates `data/users/<token>.json` in GitHub.
- Push triggers workflow `.github/workflows/generate.yml`.
- Workflow regenerates per-user JSON + ICS and commits generated files.
