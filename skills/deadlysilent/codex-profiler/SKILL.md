---
name: codex-profiler
description: Combined Codex profile operations skill: usage checks + OAuth auth refresh for OpenAI Codex profiles via Telegram commands /codex_usage and /codex_auth.
---

This skill consolidates both scripts:
- `scripts/codex_usage.py` (usage/limits)
- `scripts/codex_auth.py` (OAuth start/finish + queued safe apply)

## Commands
### Usage
- `/codex_usage` → selector (default / kyle / mine / all)
- `/codex_usage <profile>`

### Auth
- `/codex_auth` → selector (profiles)
- `/codex_auth <profile>`
- `/codex_auth finish <profile> <callback_url>`

## UX requirement (Telegram)
For `/codex_usage`, send an immediate progress message first:
- "Running Codex usage checks now…"

For queued auth apply, warn before restart behavior:
- "Gateway restart will be performed by background apply job. Avoid long-running tasks."

## How to run
```bash
python3 skills/codex-profiler/scripts/codex_usage.py --profile all --timeout-sec 25 --retries 1 --debug
python3 skills/codex-profiler/scripts/codex_auth.py start --profile default
python3 skills/codex-profiler/scripts/codex_auth.py finish --profile default --callback-url "http://localhost:1455/auth/callback?code=...&state=..." --queue-apply
python3 skills/codex-profiler/scripts/codex_auth.py status
```

## Notes
- Uses auth profiles at `~/.openclaw/agents/main/agent/auth-profiles.json` by default.
- Codex usage endpoint: `https://chatgpt.com/backend-api/wham/usage`.
- OAuth flow: OpenAI auth endpoints + localhost callback on port 1455.
