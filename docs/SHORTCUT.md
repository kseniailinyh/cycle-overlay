# iPhone Shortcut Setup

Use a GitHub personal access token (PAT) stored only on your device. Do not commit the token.

## Trigger GitHub Actions

Endpoint template:

```
https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/generate.yml/dispatches
```

Required headers:

```
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
Authorization: Bearer <YOUR_PAT>
```

Example JSON body:

```json
{
  "ref": "main",
  "inputs": { "cycle_start": "2026-01-17" }
}
```

## Open the dashboard

After triggering the workflow, open:

```
https://<username>.github.io/<repo>/app/
```

If data appears stale, wait a minute for GitHub Pages to update.
