# Cycle Overlay Calendar

This repository generates an iCalendar (.ics) file with daily all-day events that show cycle day and phase for the next 12 months. The calendar is served via GitHub Pages from the `docs/` folder.

## How it works

- Update `config.json` with your most recent cycle start date.
- A GitHub Actions workflow regenerates `docs/calendar.ics` on push and daily.
- GitHub Pages serves the calendar file for Apple Calendar subscription.

## Configure

Edit `config.json`:

- `last_period_start`: ISO date string `YYYY-MM-DD`
- `cycle_length`: integer (default 28)
- `period_length`: integer (default 3)
- `months_ahead`: integer (default 12)
- `calendar_name`: string (default `Cycle`)

Commit and push the change to `main`.

## GitHub Pages setup

This repo uses GitHub Pages from the `/docs` folder on the `main` branch.

1. Go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Select **Branch: main** and **Folder: /docs**.
4. Save.

After Pages is enabled, your subscription URL will be:

```
https://<your-username>.github.io/<your-repo>/calendar.ics
```

## Subscribe in Apple Calendar

1. Open Apple Calendar.
2. **File → New Calendar Subscription…**
3. Paste the URL above.

Apple may take hours to refresh subscribed calendars. To force a refresh, remove and re-add the subscription.

## Local generation (optional)

```
python3 scripts/generate_ics.py
```

The output is written to `docs/calendar.ics`.
