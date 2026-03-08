---
name: openclaw-dx
description: Diagnose and fix openclaw gateway issues. Use when the gateway is stuck, not starting, crash-looping, or rejecting connections. Covers main and --profile vesper gateways. Runs triage, applies fixes, writes incident report to ~/clawd/inbox.
---

# OpenClaw Gateway DX

Diagnose, fix, and document openclaw gateway issues. Covers both main (port 18789) and vesper profile (port 18999) gateways.

## When to Use

- Gateway not starting or crash-looping
- TUI/CLI can't connect (pairing required, password mismatch, device token mismatch)
- Gateway unresponsive or high memory
- After openclaw version upgrades
- User says "openclaw is stuck" or similar

## Triage Protocol

Run these in parallel to assess state:

```bash
# 1. What's listening?
lsof -i :18789 -i :18999 2>/dev/null | grep LISTEN

# 2. Process health (memory, CPU, uptime)
ps -o pid,rss,pcpu,lstart,etime -p $(lsof -i :18789 -t 2>/dev/null | head -1)

# 3. Recent errors
tail -30 ~/.openclaw/logs/gateway.err.log

# 4. Recent activity
tail -20 ~/.openclaw/logs/gateway.log

# 5. Channel status
openclaw channels status

# 6. Version
openclaw --version

# 7. Pending device pairings
openclaw devices list --json | head -20

# 8. Model config + fallback chain (use affected profile's config dir)
# Main: ~/.openclaw/openclaw.json | Vesper: ~/.openclaw-vesper/openclaw.json
cat ~/.openclaw/openclaw.json | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['agents']['defaults']['model'], indent=2))"

# 9. Per-agent auth token status + expiry check
# Main: ~/.openclaw/agents/main/agent/auth-profiles.json
# Vesper: ~/.openclaw-vesper/agents/main/agent/auth-profiles.json
python3 -c "
import sys,json,time
data=json.load(open('$HOME/.openclaw/agents/main/agent/auth-profiles.json'))
now=time.time()*1000
for k,v in data.get('profiles',{}).items():
    exp=v.get('expires',0)
    expired='EXPIRED' if exp and exp<now else 'valid'
    has_token='yes' if v.get('access') or v.get('token') else 'NO'
    print(f'{k}: type={v.get(\"type\",\"?\")} token={has_token} expires={expired}')
"

# 10. Memory search / QMD (use --profile if vesper)
openclaw memory status
```

## Common Failure Modes

### 0. Failover Cascade (All Providers Down)
**Symptom:** `All models failed (N):` followed by per-provider errors. May also appear as "The model has crashed without additional information. (Exit code: null)"
**Diagnosis:** Check the full error chain — each attempt cycles primary → fallback1 → fallback2. All must fail for the user to see an error. Common error signatures per provider:
- Anthropic: `The AI service is temporarily overloaded` (transient, or stale token)
- OpenAI Codex: `OAuth token refresh failed for openai-codex` or `refresh_token_reused` (expired access token + consumed refresh token)
- Google/Gemini: `No API key found for provider "google"` (provider never configured in auth-profiles.json)
- LM Studio: Python errors like `AttributeError: 'list' object has no attribute 'swapaxes'` (model inference bug)
**Fix:** Identify which providers are broken and fix each:
```bash
# Check fallback config (use affected profile's config dir)
cat ~/.openclaw/openclaw.json | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['agents']['defaults']['model'], indent=2))"
# Check per-agent auth tokens + expiry
python3 -c "
import sys,json,time
data=json.load(open('$HOME/.openclaw/agents/main/agent/auth-profiles.json'))
now=time.time()*1000
for k,v in data.get('profiles',{}).items():
    exp=v.get('expires',0)
    expired='EXPIRED' if exp and exp<now else 'valid'
    has_token='yes' if v.get('access') or v.get('token') else 'NO'
    print(f'{k}: type={v.get(\"type\",\"?\")} token={has_token} expires={expired}')
"
```
**For OAuth expiry (OpenAI Codex):** `openclaw configure` (interactive re-auth). Add `--profile vesper` if vesper.
**For missing provider keys (Google etc.):** `openclaw agents add <provider>` or remove unconfigured providers from fallback chain.
**Prevention:** Ensure all providers in the fallback chain are actually configured. Use same-provider fallbacks (e.g. different Anthropic models) instead of cross-provider for predictable failure modes.

### 1. Expired Channel Token (Slack xoxe.xoxb-)
**Symptom:** Crash loop with `Unhandled promise rejection: Error: An API error occurred: token_expired`
**Fix:**
```bash
# Disable the channel
# Edit ~/.openclaw/openclaw.json: channels.slack.enabled → false AND plugins.entries.slack.enabled → false
openclaw gateway start
# Then rotate token at api.slack.com and re-enable
```

### 2. Config Wiped by Upgrade
**Symptom:** `Gateway start blocked: set gateway.mode=local (current: unset)`
**Fix:** Restore from backup:
```bash
ls -la ~/.openclaw/openclaw.json.bak*
# Find the largest/most recent backup with full config
cp ~/.openclaw/openclaw.json.bak-XXXX ~/.openclaw/openclaw.json
openclaw doctor --fix
openclaw gateway start
```

### 3. Stale Lock File
**Symptom:** Gateway won't start, references old PID
**Fix:**
```bash
ls ~/.openclaw/gateway.*.lock
cat ~/.openclaw/gateway.*.lock  # check PID
kill -0 <pid>  # verify dead
rm ~/.openclaw/gateway.*.lock
openclaw gateway start
```

### 4. Device Token Mismatch / Pairing Required
**Symptom:** `unauthorized: device token mismatch` or `pairing required`
**Fix:**
```bash
openclaw devices list --json  # check for pending requests
openclaw devices approve "<requestId>" --password "$OPENCLAW_GATEWAY_PASSWORD"
# Or rotate existing device:
openclaw devices rotate --device <id> --role operator --password "$OPENCLAW_GATEWAY_PASSWORD"
```

### 5. Password Mismatch (multi-profile)
**Symptom:** `unauthorized: gateway password mismatch`
**Fix:** Sync passwords across profiles. All profiles should use `$OPENCLAW_GATEWAY_PASSWORD` to match the env var in shell rc (`~/.bashrc` or `~/.zshrc`).

### 6. Memory Bloat / Unresponsive
**Symptom:** Gateway listening but not responding, RSS exceeds Critical threshold (see Memory Thresholds)
**Fix:**
```bash
openclaw gateway stop
sleep 2
kill -9 <pid>  # if still lingering
launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

### 7. Invalid Plugin Entry
**Symptom:** `Config invalid: plugins.entries.X: plugin not found`
**Fix:** Remove the stale plugin entry from `~/.openclaw/openclaw.json`, then `openclaw gateway start`.

### 8. Port Conflict / Orphan Processes
**Symptom:** `Port 18789 is already in use` or multiple gateway PIDs
**Fix:**
```bash
ps aux | grep openclaw-gateway | grep -v grep
kill <orphan-pids>
openclaw gateway start
```

### 9. Custom Plugin Missing configSchema
**Symptom:** Crash loop with `plugins: plugin: plugin manifest requires configSchema`
**Diagnosis:** A plugin in `~/.openclaw/extensions/` (auto-discovered) or `plugins.load.paths` has an `openclaw.plugin.json` without the required `configSchema` field. Run `openclaw doctor --fix` — the "Plugin diagnostics" section names the offending manifest.
**Fix:** Add empty configSchema to the plugin manifest:
```json
"configSchema": {
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```
Then restart: `launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.openclaw.gateway.plist`
**Prevention:** All plugin manifests require `configSchema` in 2026.3.2+, even if empty. Run `openclaw doctor` after creating custom plugins before restarting.

### 10. Invalid JSON in Config (Hand-Edit Damage)
**Symptom:** CLI commands fail with `json.decoder.JSONDecodeError` or `Unexpected token`. Gateway may still run (it was started before the edit) but CLI/TUI can't parse the config to connect.
**Diagnosis:** Someone hand-edited `openclaw.json` and introduced unquoted keys, trailing commas, or other invalid JSON.
**Fix:** Validate and fix the JSON:
```bash
python3 -c "import json; json.load(open('$HOME/.openclaw/openclaw.json'))"
# Fix the reported line — common issues: unquoted keys, trailing commas
```
**Prevention:** Use `openclaw configure` or a JSON-aware editor. After manual edits, validate with the python one-liner above.

### 11. Missing gateway.remote.token (Token Auth Mode)
**Symptom:** CLI/TUI fails with `gateway token missing (set gateway.remote.token to match gateway.auth.token)`
**Diagnosis:** The gateway uses `gateway.auth.mode: "token"` but `gateway.remote.token` is not set. The CLI reads `remote.token` to authenticate — without it, all connections are rejected.
**Fix:** Add `gateway.remote.token` matching `gateway.auth.token`:
```bash
# In openclaw.json, inside the "gateway" section:
"remote": {
  "token": "<same value as gateway.auth.token>"
}
```
Then restart the gateway.
**Note:** Any profile using `gateway.auth.mode: "token"` needs `gateway.remote.token` set. Profiles using password auth (`$OPENCLAW_GATEWAY_PASSWORD`) are not affected.

### 12. Config Patch Restart Cascade (LaunchAgent Left Unloaded)
**Symptom:** Gateway down, port not listening, `launchctl print` says service not found. Error log shows `config change requires gateway restart` followed by restart failure.
**Diagnosis:** Multiple `config.patch` calls (e.g., from an agent using the gateway tool) changed `gateway.auth.*` or other restart-requiring keys. Each patch triggers a deferred restart. The restart mechanism fails with one of:
- `spawnSync launchctl ETIMEDOUT`
- `Bootstrap failed: 5: Input/output error`

The gateway falls back to in-process restart, becomes unstable, eventually receives SIGTERM, and the LaunchAgent is left unloaded.
**Fix:**
```bash
launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```
**Prevention:**
- **Batch config changes** that touch `gateway.auth.*` into a single `config.patch` call to minimize restart triggers
- This is a recurring upstream bug in openclaw 2026.3.x — the LaunchAgent restart mechanism is unreliable across multiple error modes
- Consider a watchdog or `KeepAlive` with `ThrottleInterval=30` in the plist
- If using the gateway tool's `config.patch` action, combine auth + plugin + compaction changes into one call

## Memory Thresholds

| RSS | Status | Action |
|-----|--------|--------|
| < 500MB | Healthy | None |
| 500MB-1.5GB | Elevated | Monitor |
| 1.5GB-2.5GB | High | Schedule restart |
| > 2.5GB | Critical | Restart now |

## Node Heap Tuning

The gateway runs on Node.js and defaults to ~4GB max old space. For long-running gateways or heavy plugin loads, increase via `--max-old-space-size` in the LaunchAgent plist's `ProgramArguments`:

```xml
<string>--max-old-space-size=16384</string>
```

Insert after the `node` binary path, before the entry JS file. Current state:
- **vesper**: `--max-old-space-size=16384` (16GB) — set to handle QMD/memory-search workloads
- **main**: not set (Node default ~4GB)

To add or change, edit the plist directly and reload:
```bash
# Edit the plist
nano ~/Library/LaunchAgents/ai.openclaw.gateway.plist
# Reload
launchctl bootout gui/501/ai.openclaw.gateway && launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```

If the gateway OOMs before hitting the RSS thresholds above, this is likely the fix.

## Config Paths

| Profile | Config | State | Port |
|---------|--------|-------|------|
| main | `~/.openclaw/openclaw.json` | `~/.openclaw/` | 18789 |
| vesper | `~/.openclaw-vesper/openclaw.json` | `~/.openclaw-vesper/` | 18999 |

**Plugin auto-discovery paths** (scanned on startup, no config entry needed):
- `~/.openclaw/extensions/<plugin-id>/` — per-profile custom plugins
- Paths listed in `plugins.load.paths` — explicitly loaded extensions

## Auth

- Gateway password: `$OPENCLAW_GATEWAY_PASSWORD` (env var in shell rc — `~/.zshrc` on macOS default, `~/.bashrc` if using bash)
- `gateway.controlUi.dangerouslyDisableDeviceAuth: true` — only bypasses Control UI, not CLI/TUI
- CLI/TUI always requires device pairing in 2026.2.25+

### API Token Locations (v2026.3.1+)
Top-level `openclaw.json` auth.profiles declares profile type/mode only — **no tokens**.
Actual tokens live in per-agent auth profile files:
```
# Main profile
~/.openclaw/agents/main/agent/auth-profiles.json
~/.openclaw/agents/codex/agent/auth-profiles.json

# Vesper profile
~/.openclaw-vesper/agents/main/agent/auth-profiles.json
~/.openclaw-vesper/agents/codex/agent/auth-profiles.json
```
Each has `profiles.<provider>:default` with `access`/`refresh`/`expires` for OAuth, or `token` for API keys.
The `expires` field is epoch milliseconds — compare to `Date.now()` or `time.time()*1000` to check expiry.

Fresh Anthropic setup tokens: `~/clawd/inbox/2026-03-03-anthropic-setup-tokens`

### doctor --fix Token Migration (v2026.3.1)
`openclaw doctor --fix` removes `token` fields from top-level `auth.profiles` in `openclaw.json` (schema change). This does NOT affect per-agent auth profiles — those still use `token` as the field name. If doctor runs and removes tokens from the top-level config, the gateway still works because it reads from per-agent files at runtime.

### OpenAI Codex OAuth Refresh
**Symptom:** `OAuth token refresh failed for openai-codex` or `refresh_token_reused` — the access token expired and the refresh token is single-use/already consumed.
**Diagnosis:** Check `expires` field in `auth-profiles.json` — if epoch ms is in the past, access token is expired. If refresh also fails, full re-auth needed.
**Fix:** Interactive re-auth: `openclaw configure` (add `--profile vesper` if vesper profile).

### Unconfigured Fallback Provider
**Symptom:** `No API key found for provider "<provider>"` with auth store path shown.
**Diagnosis:** The model fallback chain references a provider that was never set up in auth-profiles.json.
**Fix:** Either configure the provider (`openclaw agents add <provider>`) or remove it from the fallback chain in `openclaw.json` → `agents.defaults.model.fallbacks`.

## Memory Search / QMD

Check memory search status as part of triage when the agent isn't responding correctly:
```bash
openclaw --profile vesper memory status
```
Key config: `agents.defaults.memorySearch.enabled` in `openclaw.json` — if `false`, the `memory_search`/`memory_get` tools won't register even if listed in `tools.alsoAllow`.

Enabling requires a gateway restart (hot-reload picks up the config but tool registration needs restart).

## Gateway Restart (by profile)

| Profile | LaunchAgent plist | Stop + Start |
|---------|-------------------|--------------|
| main | `~/Library/LaunchAgents/ai.openclaw.gateway.plist` | `openclaw gateway stop && launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.openclaw.gateway.plist` |
| vesper | `~/Library/LaunchAgents/ai.openclaw.vesper.plist` | `openclaw --profile vesper gateway stop && launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.openclaw.vesper.plist` |

If `gateway start` says "Gateway service not loaded", use `launchctl bootstrap` directly.

## Post-Fix Protocol

After fixing any issue:
1. Verify: `openclaw channels status` — all channels should show "running"
2. Check memory: `ps -o pid,rss,pcpu,etime -p $(lsof -i :18789 -t | head -1)`
3. Write incident report to `~/clawd/inbox/YYYY-MM-DD-<description>.md`

## Incident Report Template

```markdown
# Incident: <Title> — YYYY-MM-DD

## Summary
<1-2 sentences>

## Symptoms
- <what the user saw>

## Root Cause
<what went wrong and why>

## Fix
<what was done>

## Config Changes
| File | Change |
|------|--------|

## Prevention
<how to avoid next time>
```

## Post-Upgrade Checklist

Run after any openclaw version bump:
```bash
openclaw --version
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.pre-upgrade
openclaw doctor --fix
openclaw devices list --json | jq '.pending'
# Approve any pending pairings
openclaw channels status
```

## Vesper Profile Commands

Prefix all commands with `--profile vesper`:
```bash
openclaw --profile vesper channels status
openclaw --profile vesper gateway start
openclaw --profile vesper doctor --fix
```
