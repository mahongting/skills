#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_AUTH_PATH = str(Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json")
DEFAULT_ENDPOINT = "https://chatgpt.com/backend-api/wham/usage"


def fmt_ts(ms):
    if not ms:
        return "n/a"
    try:
        return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc).isoformat()
    except Exception:
        return "n/a"


def fmt_expiry(raw):
    if not raw:
        return "n/a"
    ts = float(raw)
    if ts > 10_000_000_000:
        ts = ts / 1000.0
    now = dt.datetime.now(dt.timezone.utc)
    exp = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
    delta = exp - now
    sign = "-" if delta.total_seconds() < 0 else "+"
    mins = int(abs(delta.total_seconds()) // 60)
    return f"{exp.isoformat()} ({sign}{mins}m)"


def load_store(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_codex_profiles(store):
    profiles = store.get("profiles", {})
    ids = []
    for pid, cred in profiles.items():
        if cred.get("provider") == "openai-codex":
            ids.append(pid)
    return sorted(ids)


def resolve_targets(store, selector):
    codex_ids = list_codex_profiles(store)
    if not codex_ids:
        return []

    selector = (selector or "all").strip()
    if selector in ("all", "both"):
        return codex_ids

    if selector == "default":
        if "openai-codex:default" in codex_ids:
            return ["openai-codex:default"]
        return [codex_ids[0]]

    if selector in codex_ids:
        return [selector]

    if not selector.startswith("openai-codex:"):
        expanded = f"openai-codex:{selector}"
        if expanded in codex_ids:
            return [expanded]

    return []


def call_remote_usage(endpoint, token, account_id=None, timeout_sec=20, retries=1):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "CodexBar",
    }
    if account_id:
        headers["ChatGPT-Account-Id"] = str(account_id)

    last_err = None
    for attempt in range(1, retries + 2):
        start = time.time()
        req = urllib.request.Request(endpoint, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                elapsed_ms = int((time.time() - start) * 1000)
                try:
                    payload = json.loads(body)
                except Exception:
                    payload = {"raw": body[:2000]}
                return {
                    "ok": True,
                    "status": int(resp.status),
                    "payload": payload,
                    "attempt": attempt,
                    "elapsed_ms": elapsed_ms,
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            elapsed_ms = int((time.time() - start) * 1000)
            try:
                payload = json.loads(body)
            except Exception:
                payload = {"raw": body[:2000]}
            if e.code >= 500 and attempt <= retries + 1:
                last_err = {
                    "ok": False,
                    "status": int(e.code),
                    "error": "server_error",
                    "payload": payload,
                    "attempt": attempt,
                    "elapsed_ms": elapsed_ms,
                }
                time.sleep(min(1.5 * attempt, 4))
                continue
            return {
                "ok": False,
                "status": int(e.code),
                "error": "http_error",
                "payload": payload,
                "attempt": attempt,
                "elapsed_ms": elapsed_ms,
            }
        except socket.timeout:
            elapsed_ms = int((time.time() - start) * 1000)
            last_err = {
                "ok": False,
                "status": None,
                "error": "timeout",
                "attempt": attempt,
                "elapsed_ms": elapsed_ms,
            }
            if attempt <= retries + 1:
                time.sleep(min(1.5 * attempt, 4))
                continue
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            last_err = {
                "ok": False,
                "status": None,
                "error": "request_exception",
                "message": str(e),
                "attempt": attempt,
                "elapsed_ms": elapsed_ms,
            }
            if attempt <= retries + 1:
                time.sleep(min(1.5 * attempt, 4))
                continue

    return last_err or {"ok": False, "error": "unknown"}


def format_reset_in(seconds):
    if not isinstance(seconds, (int, float)):
        return "n/a"
    total = int(max(0, seconds))
    if total < 3600:
        mins = max(1, total // 60)
        return f"{mins} minutes"
    hours = total // 3600
    mins = (total % 3600) // 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def format_reset_at(ts):
    if not isinstance(ts, (int, float)):
        return "n/a"
    d = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).astimezone()
    return d.strftime("%Y-%m-%d, %I:%M %p %Z")


def parse_codex_usage(payload):
    rl = (payload or {}).get("rate_limit") or {}
    pw = rl.get("primary_window") or {}
    sw = rl.get("secondary_window") or {}

    def win(obj, fallback_label):
        if not obj:
            return None
        secs = obj.get("limit_window_seconds")
        reset = obj.get("reset_at")
        reset_after = obj.get("reset_after_seconds")
        label = fallback_label
        try:
            if isinstance(secs, (int, float)) and secs > 0:
                hours = round(float(secs) / 3600)
                label = f"{hours}h" if hours < 24 else ("Week" if hours >= 168 else "Day")
        except Exception:
            pass
        used = obj.get("used_percent")
        remaining = None
        if isinstance(used, (int, float)):
            remaining = max(0, 100 - float(used))
        return {
            "label": label,
            "used_percent": used,
            "remaining_percent": remaining,
            "reset_in": format_reset_in(reset_after),
            "reset_at": format_reset_at(reset),
            "reset_after_seconds": reset_after,
        }

    windows = []
    p = win(pw, "5h")
    s = win(sw, "Week")
    if p:
        windows.append(p)
    if s:
        windows.append(s)

    plan = payload.get("plan_type") if isinstance(payload, dict) else None
    credits = None
    try:
        bal = payload.get("credits", {}).get("balance")
        if bal is not None:
            credits = float(bal)
    except Exception:
        credits = None

    return {
        "plan": plan,
        "credits_balance": credits,
        "allowed": rl.get("allowed"),
        "limit_reached": rl.get("limit_reached"),
        "windows": windows,
    }


def report_profile(store, profile_id, include_remote=False, endpoint=None, timeout_sec=20, retries=1, debug=False):
    profiles = store.get("profiles", {})
    usage_stats = store.get("usageStats", {})

    p = profiles.get(profile_id)
    if not p:
        return {"profile": profile_id, "status": "missing"}

    u = usage_stats.get(profile_id, {})

    result = {
        "profile": profile_id,
        "provider": p.get("provider"),
        "type": p.get("type"),
        "token_expiry": fmt_expiry(p.get("expires")),
        "last_used": fmt_ts(u.get("lastUsed")),
        "last_failure": fmt_ts(u.get("lastFailureAt")),
        "cooldown_until": fmt_ts(u.get("cooldownUntil")),
        "error_count": u.get("errorCount", 0),
        "failure_counts": u.get("failureCounts", {}),
    }

    if include_remote and endpoint:
        token = p.get("access")
        account_id = p.get("accountId")
        if token:
            remote = call_remote_usage(endpoint, token, account_id=account_id, timeout_sec=timeout_sec, retries=retries)
            result["remote_usage_ok"] = bool(remote.get("ok"))
            if remote.get("ok"):
                result["remote_usage"] = parse_codex_usage(remote.get("payload") or {})
            else:
                result["remote_error"] = remote.get("error") or "request_failed"
                if remote.get("status") is not None:
                    result["remote_status"] = remote.get("status")
            if debug:
                result["remote_debug"] = {
                    "attempt": remote.get("attempt"),
                    "elapsed_ms": remote.get("elapsed_ms"),
                    "status": remote.get("status"),
                    "endpoint": endpoint,
                }
        else:
            result["remote_usage_ok"] = False
            result["remote_error"] = "missing_access_token"

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="all", help="all|default|<profile-id>|<suffix>")
    ap.add_argument("--auth-path", default=DEFAULT_AUTH_PATH)
    ap.add_argument("--timeout-sec", type=int, default=20)
    ap.add_argument("--retries", type=int, default=1, help="number of retries after first attempt")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    try:
        store = load_store(args.auth_path)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"failed_to_read_auth_profiles: {e}"}))
        sys.exit(1)

    targets = resolve_targets(store, args.profile)
    if not targets:
        print(json.dumps({
            "ok": False,
            "error": "no_matching_codex_profiles",
            "available_profiles": list_codex_profiles(store),
            "hint": "Use --profile all/default/<profile-id>/<suffix>",
        }, indent=2))
        sys.exit(2)

    endpoint = os.getenv("CODEX_USAGE_ENDPOINT", DEFAULT_ENDPOINT).strip()
    include_remote = bool(endpoint)

    reports = []
    for pid in targets:
        reports.append(
            report_profile(
                store,
                pid,
                include_remote=include_remote,
                endpoint=endpoint,
                timeout_sec=max(5, args.timeout_sec),
                retries=max(0, args.retries),
                debug=args.debug,
            )
        )

    out = {
        "ok": True,
        "source": "auth-profiles",
        "remote_endpoint_configured": include_remote,
        "profiles": reports,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
