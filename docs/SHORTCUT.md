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

Example JSON body (multi-user):

```json
{
  "ref": "main",
  "inputs": {
    "token": "d3d0cd6b5f7e9372a731b29b1394c293713957c167cf1f07",
    "cycle_start": "2026-01-17"
  }
}
```

## Open dashboard

```
https://<username>.github.io/<repo>/app/?t=<token>
```

If data appears stale, wait a minute for GitHub Pages to update.
