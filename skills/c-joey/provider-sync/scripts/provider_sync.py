#!/usr/bin/env python3
import argparse
import copy
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Tuple


def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def split_path(path: str) -> List[str]:
    if not path:
        return []
    return [p for p in path.split(".") if p]


def get_path(data: Any, path: str) -> Any:
    cur = data
    for part in split_path(path):
        if isinstance(cur, list):
            idx = int(part)
            cur = cur[idx]
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def set_path(data: Any, path: str, value: Any):
    parts = split_path(path)
    if not parts:
        raise ValueError("empty target path")

    cur = data
    for i, part in enumerate(parts[:-1]):
        nxt = parts[i + 1]
        want_list = nxt.isdigit()

        if isinstance(cur, dict):
            if part not in cur or cur[part] is None:
                cur[part] = [] if want_list else {}
            cur = cur[part]
        elif isinstance(cur, list):
            idx = int(part)
            while len(cur) <= idx:
                cur.append({})
            if cur[idx] is None:
                cur[idx] = [] if want_list else {}
            cur = cur[idx]
        else:
            raise ValueError(f"invalid path segment at {part}")

    last = parts[-1]
    if isinstance(cur, dict):
        cur[last] = value
    elif isinstance(cur, list):
        idx = int(last)
        while len(cur) <= idx:
            cur.append(None)
        cur[idx] = value
    else:
        raise ValueError(f"cannot set value at {path}")


def append_unique(target: Any, incoming: Any) -> Any:
    base = target if isinstance(target, list) else []
    src = incoming if isinstance(incoming, list) else [incoming]
    out = list(base)
    for item in src:
        if item not in out:
            out.append(item)
    return out


def fetch_json(endpoint: str, method: str, headers: Dict[str, str], body: Any) -> Any:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(endpoint, data=data, method=method.upper())
    for k, v in headers.items():
        req.add_header(k, v)

    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def parse_headers(pairs: List[str]) -> Dict[str, str]:
    out = {}
    for p in pairs:
        if ":" not in p:
            die(f"invalid header format: {p}, expected 'Key:Value'")
        k, v = p.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def resolve_dst_path(dst_path: str, provider_root: str, provider_id: str) -> str:
    provider_base = f"{provider_root}.{provider_id}"
    if dst_path.startswith("."):
        return provider_base + dst_path

    return (
        dst_path
        .replace("{provider_root}", provider_root)
        .replace("{provider_id}", provider_id)
        .replace("{provider_base}", provider_base)
    )


def pick(d: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def print_md_table(headers: List[str], rows: List[List[Any]]):
    if not rows:
        return
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        cells = [str(x).replace("\n", " ").replace("|", "\\|") if x is not None else "" for x in r]
        print("| " + " | ".join(cells) + " |")


def to_int(v: Any, default: int) -> int:
    try:
        return int(v)
    except Exception:
        return default


def expand_list_args(values: List[str]) -> List[str]:
    out = []
    for value in values or []:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def filter_models(models: Any, include_ids: List[str], exclude_ids: List[str]) -> Any:
    if not isinstance(models, list):
        return models

    include_set = set(include_ids)
    exclude_set = set(exclude_ids)
    out = []
    for item in models:
        if not isinstance(item, dict):
            continue
        mid = pick(item, ["id", "model", "name"])
        if include_set and mid not in include_set:
            continue
        if mid in exclude_set:
            continue
        out.append(item)
    return out


def sort_models_by_id(models: Any) -> Any:
    if not isinstance(models, list):
        return models
    if not all(isinstance(item, dict) and pick(item, ["id", "model", "name"]) for item in models):
        return models
    return sorted(models, key=lambda item: str(pick(item, ["id", "model", "name"]) or ""))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def short_value(value: Any, max_len: int = 60) -> str:
    if isinstance(value, list):
        rendered = ",".join(str(x) for x in value)
    elif isinstance(value, dict):
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    elif value is None:
        rendered = "null"
    else:
        rendered = str(value)
    return rendered if len(rendered) <= max_len else rendered[: max_len - 3] + "..."


def summarize_model_delta(old_models: Any, new_models: Any) -> Dict[str, Any]:
    if not isinstance(old_models, list) or not isinstance(new_models, list):
        return {
            "added": [],
            "removed": [],
            "kept": 0,
            "orderOnly": False,
            "changed": [],
            "changedCount": 0,
        }

    def to_map(items: List[Any]) -> Dict[str, Any]:
        out = {}
        for item in items:
            if isinstance(item, dict):
                mid = pick(item, ["id", "model", "name"])
                if mid:
                    out[str(mid)] = item
        return out

    old_map = to_map(old_models)
    new_map = to_map(new_models)
    old_ids = set(old_map.keys())
    new_ids = set(new_map.keys())
    common = old_ids & new_ids

    order_only = False
    if old_ids == new_ids and len(old_map) == len(old_models) and len(new_map) == len(new_models):
        old_sorted = [old_map[mid] for mid in sorted(old_ids)]
        new_sorted = [new_map[mid] for mid in sorted(new_ids)]
        order_only = canonical_json(old_sorted) == canonical_json(new_sorted) and canonical_json(old_models) != canonical_json(new_models)

    tracked_fields = ["name", "api", "input", "reasoning", "contextWindow", "maxTokens", "cost"]
    changed = []
    for mid in sorted(common):
        before = old_map[mid]
        after = new_map[mid]
        field_changes = []
        for field in tracked_fields:
            if canonical_json(before.get(field)) != canonical_json(after.get(field)):
                field_changes.append(field)
        if field_changes:
            changed.append({
                "id": mid,
                "fields": field_changes,
                "before": {field: before.get(field) for field in field_changes},
                "after": {field: after.get(field) for field in field_changes},
                "fieldDiffs": [
                    {
                        "field": field,
                        "before": before.get(field),
                        "after": after.get(field),
                        "beforeText": short_value(before.get(field)),
                        "afterText": short_value(after.get(field)),
                    }
                    for field in field_changes
                ],
            })

    return {
        "added": sorted(new_ids - old_ids),
        "removed": sorted(old_ids - new_ids),
        "kept": len(common),
        "orderOnly": order_only,
        "changed": changed,
        "changedCount": len(changed),
    }


def infer_gemini_reasoning(raw: Dict[str, Any], model_id: str) -> bool:
    explicit = pick(raw, ["reasoning", "supports_reasoning", "thinking"])
    if explicit is not None:
        return bool(explicit)

    lower_id = (model_id or "").lower()
    name = str(pick(raw, ["name", "display_name", "title"], "")).lower()
    tokens = lower_id + " " + name
    return any(key in tokens for key in ["thinking", "reasoning"])


def infer_gemini_input(raw: Dict[str, Any], model_id: str) -> List[str]:
    input_modes = pick(raw, ["input", "modalities", "capabilities", "supportedGenerationMethods"])
    out = []
    if isinstance(input_modes, list):
        for x in input_modes:
            s = str(x).lower()
            if s in ("vision", "image"):
                out.append("image")
            elif "audio" in s:
                out.append("audio")
            elif "video" in s:
                out.append("video")
            elif s:
                out.append("text" if s in ("generatecontent", "generatecontentstream") else s)
    if not out:
        lower_id = (model_id or "").lower()
        out = ["text", "image"] if "gemini" in lower_id else ["text"]
    return sorted(set(out))


def normalize_model(raw: Dict[str, Any], provider_api: str, default_ctx: int, default_max: int, normalize_profile: str = "generic") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    mid = pick(raw, ["id", "model", "name"]) or "unknown"
    name = pick(raw, ["name", "display_name", "title"], mid)

    if normalize_profile == "gemini":
        reasoning = infer_gemini_reasoning(raw, mid)
        ctx = to_int(pick(raw, ["contextWindow", "context_window", "context", "max_context_tokens", "inputTokenLimit", "input_token_limit"]), default_ctx)
        max_tokens = to_int(pick(raw, ["maxTokens", "max_tokens", "max_output_tokens", "output_tokens", "outputTokenLimit", "output_token_limit"]), default_max)
        input_list = infer_gemini_input(raw, mid)
    else:
        reasoning = bool(pick(raw, ["reasoning", "supports_reasoning", "thinking"], False))
        ctx = to_int(pick(raw, ["contextWindow", "context_window", "context", "max_context_tokens"]), default_ctx)
        max_tokens = to_int(pick(raw, ["maxTokens", "max_tokens", "max_output_tokens", "output_tokens"]), default_max)

        input_modes = pick(raw, ["input", "modalities", "capabilities"])
        if isinstance(input_modes, list):
            input_list = ["image" if str(x).lower() in ("vision", "image") else str(x).lower() for x in input_modes]
            input_list = sorted(set(input_list))
        else:
            input_list = ["text"]

    api = pick(raw, ["api"], provider_api)

    model = {
        "id": mid,
        "name": name,
        "api": api,
        "reasoning": reasoning,
        "input": input_list,
        "cost": {
            "input": 0,
            "output": 0,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
        "contextWindow": ctx,
        "maxTokens": max_tokens,
    }

    note = {
        "id": mid,
        "reasoning": reasoning,
        "input": input_list,
        "contextWindow": ctx,
        "maxTokens": max_tokens,
    }
    return model, note



def normalize_models(models: Any, provider_api: str, default_ctx: int, default_max: int, normalize_profile: str = "generic") -> Tuple[Any, List[Dict[str, Any]]]:
    if not isinstance(models, list):
        return models, []
    out = []
    notes = []
    for raw in models:
        if not isinstance(raw, dict):
            continue
        m, n = normalize_model(raw, provider_api, default_ctx, default_max, normalize_profile=normalize_profile)
        out.append(m)
        notes.append(n)
    return out, notes


def merge_with_existing_models(new_models: Any, existing_models: Any) -> Any:
    if not isinstance(new_models, list):
        return new_models
    if not isinstance(existing_models, list):
        return new_models

    by_id = {}
    for m in existing_models:
        if isinstance(m, dict) and m.get("id"):
            by_id[m["id"]] = m

    keep_fields = ["name", "api", "reasoning", "input", "contextWindow", "maxTokens", "cost"]
    merged = []
    for nm in new_models:
        if not isinstance(nm, dict):
            continue
        mid = nm.get("id")
        em = by_id.get(mid)
        if isinstance(em, dict):
            mm = dict(nm)
            for f in keep_fields:
                if f in em and em[f] is not None:
                    mm[f] = em[f]
            merged.append(mm)
        else:
            merged.append(nm)
    return merged


def to_base_v1_url(endpoint: str) -> str:
    u = endpoint.rstrip("/")
    if u.endswith("/models"):
        return u[: -len("/models")]
    return u


def probe_mode(base_url: str, mode: str, model_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
    mode = mode.strip()
    if mode == "openai-responses":
        path = "/responses"
        payload = {"model": model_id, "input": "ping", "max_output_tokens": 1}
    elif mode == "openai-completions":
        path = "/chat/completions"
        payload = {"model": model_id, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}
    else:
        return {"mode": mode, "supported": False, "status": None, "detail": "unsupported probe mode"}

    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"mode": mode, "supported": True, "status": resp.status, "detail": "ok"}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        supported = e.code not in (404, 405)
        detail = body[:200].replace("\n", " ") if body else e.reason
        return {"mode": mode, "supported": supported, "status": e.code, "detail": detail}
    except Exception as e:
        return {"mode": mode, "supported": False, "status": None, "detail": str(e)}


def build_summary(
    changes: List[Dict[str, Any]],
    current_models: Any,
    probe_results: List[Dict[str, Any]],
    picked_mode: Any,
    dry_run: bool,
    check_only: bool,
    preserve_existing_model_fields: bool,
    normalize_profile: str,
    model_delta: Dict[str, Any] = None,
    backup: str = None,
    updated: str = None,
) -> Dict[str, Any]:
    model_summary = []
    if isinstance(current_models, list):
        for m in current_models:
            if not isinstance(m, dict):
                continue
            model_summary.append(
                {
                    "id": m.get("id", ""),
                    "input": m.get("input", []) if isinstance(m.get("input"), list) else ["text"],
                    "reasoning": bool(m.get("reasoning")),
                    "contextWindow": m.get("contextWindow"),
                    "maxTokens": m.get("maxTokens"),
                }
            )

    return {
        "changed": bool(changes),
        "changeCount": len(changes),
        "changes": changes,
        "models": model_summary,
        "modelCount": len(model_summary),
        "probeResults": probe_results,
        "recommendedProviderApi": picked_mode,
        "dryRun": dry_run,
        "checkOnly": check_only,
        "preserveExistingModelFields": preserve_existing_model_fields,
        "normalizeProfile": normalize_profile,
        "modelDelta": model_delta or {"added": [], "removed": [], "kept": 0, "orderOnly": False, "changed": [], "changedCount": 0},
        "backup": backup,
        "updated": updated,
    }


def print_summary(summary: Dict[str, Any]):
    changes = summary.get("changes") or []
    if not changes:
        print("No changes.")
        return

    print(f"Planned changes: {summary.get('changeCount', len(changes))}")
    change_rows = [[c.get("to", ""), c.get("from", ""), c.get("mode", "")] for c in changes]
    print_md_table(["target", "source", "mode"], change_rows)

    model_delta = summary.get("modelDelta") or {}
    added = model_delta.get("added") or []
    removed = model_delta.get("removed") or []
    kept = model_delta.get("kept", 0)
    changed = model_delta.get("changed") or []
    if added or removed or kept or changed:
        print(f"\nModel delta: +{len(added)} / -{len(removed)} / ={kept} / ~{len(changed)}")
        if model_delta.get("orderOnly"):
            print("Only model order changed after canonical comparison.")
        if added:
            print("Added: " + ", ".join(added[:10]) + (" ..." if len(added) > 10 else ""))
        if removed:
            print("Removed: " + ", ".join(removed[:10]) + (" ..." if len(removed) > 10 else ""))
        if changed:
            print("Changed models:")
            for item in changed[:10]:
                parts = []
                for diff in item.get("fieldDiffs") or []:
                    parts.append(f"{diff['field']}({diff['beforeText']} → {diff['afterText']})")
                print(f"- {item['id']}: " + "; ".join(parts))
            if len(changed) > 10:
                print(f"- ... and {len(changed) - 10} more")

    models = summary.get("models") or []
    if models:
        print(f"\nModel summary: {summary.get('modelCount', len(models))}")
        model_rows = []
        for m in models:
            model_rows.append(
                [
                    m.get("id", ""),
                    ",".join(m.get("input", [])) if isinstance(m.get("input"), list) else "text",
                    "yes" if m.get("reasoning") else "no",
                    m.get("contextWindow", "-"),
                    m.get("maxTokens", "-"),
                ]
            )
        print_md_table(["model", "input", "reasoning", "context", "max_tokens"], model_rows)

    probe_results = summary.get("probeResults") or []
    if probe_results:
        print("\nAPI probe summary")
        probe_rows = [
            [
                r.get("mode"),
                "yes" if r.get("supported") else "no",
                r.get("status") if r.get("status") is not None else "-",
                (r.get("detail") or "")[:80],
            ]
            for r in probe_results
        ]
        print_md_table(["mode", "supported", "status", "note"], probe_rows)
        if summary.get("recommendedProviderApi"):
            print(f"Recommended provider.api: {summary['recommendedProviderApi']}")

    if summary.get("normalizeProfile") and summary.get("normalizeProfile") != "generic":
        print(f"\nNormalization profile: {summary['normalizeProfile']}")

    if summary.get("preserveExistingModelFields"):
        print("\nModel merge policy: preserve existing local capability fields (by model id)")

    if summary.get("checkOnly"):
        print("\nCheck-only mode. No file written.")
    elif summary.get("dryRun"):
        print("\nDry-run only. No file written.")

    if summary.get("backup"):
        print(f"\nBackup: {summary['backup']}")
    if summary.get("updated"):
        print(f"Updated: {summary['updated']}")


def main():
    ap = argparse.ArgumentParser(description="Sync provider fields from upstream to openclaw.json")
    ap.add_argument("--config", default="/root/.openclaw/openclaw.json", help="openclaw.json path")
    ap.add_argument("--provider-root", default="models.providers", help="provider map path in config")
    ap.add_argument("--provider-id", required=True, help="provider id in openclaw.json")
    ap.add_argument("--endpoint", required=True, help="upstream API endpoint")
    ap.add_argument("--method", default="GET", choices=["GET", "POST", "PUT", "PATCH"])
    ap.add_argument("--header", action="append", default=[], help="HTTP header: Key:Value")
    ap.add_argument("--body-file", help="JSON file for request body")
    ap.add_argument("--response-root", default="", help="optional root path in response payload")
    ap.add_argument("--mapping-file", required=True, help="mapping json file")
    ap.add_argument("--normalize-models", action="store_true", help="normalize model fields for OpenClaw")
    ap.add_argument("--preserve-existing-model-fields", action="store_true", help="preserve existing local model capability fields by model id")
    ap.add_argument("--default-context-window", type=int, default=128000)
    ap.add_argument("--default-max-tokens", type=int, default=8192)
    ap.add_argument("--normalize-profile", default="generic", choices=["generic", "gemini"], help="field normalization profile")
    ap.add_argument("--probe-api-modes", default="", help="comma-separated api modes to probe, e.g. openai-responses,openai-completions")
    ap.add_argument("--auto-detect-provider-api", action="store_true", help="set provider.api based on probe results")
    ap.add_argument("--allow-outside-provider", action="store_true", help="allow writing outside provider subtree")
    ap.add_argument(
        "--sync-agent-aliases",
        dest="sync_agent_aliases",
        action="store_true",
        default=True,
        help="ensure agents.defaults.models contains <provider-id>/<model-id> entries with alias (default: on)",
    )
    ap.add_argument(
        "--no-sync-agent-aliases",
        dest="sync_agent_aliases",
        action="store_false",
        help="do not sync agents.defaults.models aliases",
    )
    ap.add_argument("--include-model", action="append", default=[], help="only include these model ids (repeatable or comma-separated)")
    ap.add_argument("--exclude-model", action="append", default=[], help="exclude these model ids (repeatable or comma-separated)")
    ap.add_argument("--output", default="markdown", choices=["markdown", "json"], help="summary output format")
    ap.add_argument("--check-only", action="store_true", help="validate fetch/mapping/probe flow and print summary without writing")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.config):
        die(f"config not found: {args.config}")

    cfg = load_json(args.config)
    providers = get_path(cfg, args.provider_root)
    if not isinstance(providers, dict):
        die(f"provider root not found or not object: {args.provider_root}")
    if args.provider_id not in providers:
        die(f"provider not found: {args.provider_id}")

    provider_base = f"{args.provider_root}.{args.provider_id}"
    provider_obj = get_path(cfg, provider_base) or {}
    provider_api = provider_obj.get("api", "openai-completions")

    include_models = expand_list_args(args.include_model)
    exclude_models = expand_list_args(args.exclude_model)

    headers = parse_headers(args.header)
    body = load_json(args.body_file) if args.body_file else None

    upstream = fetch_json(args.endpoint, args.method, headers, body)
    source = get_path(upstream, args.response_root) if args.response_root else upstream
    if source is None:
        die("response-root resolved to null")

    mappings = load_json(args.mapping_file)
    if not isinstance(mappings, list):
        die("mapping-file must be a JSON array")

    new_cfg = copy.deepcopy(cfg)
    changes = []
    model_notes: List[Dict[str, Any]] = []

    for m in mappings:
        src_path = m.get("from")
        raw_dst_path = m.get("to")
        mode = m.get("mode", "replace")
        if not src_path or not raw_dst_path:
            die(f"invalid mapping item: {m}")

        dst_path = resolve_dst_path(raw_dst_path, args.provider_root, args.provider_id)
        if (not args.allow_outside_provider) and (not dst_path.startswith(provider_base)):
            die(f"blocked write outside provider subtree: {dst_path}")

        incoming = get_path(source, src_path)

        if dst_path.endswith(".models") and (include_models or exclude_models):
            incoming = filter_models(incoming, include_models, exclude_models)

        if args.normalize_models and dst_path.endswith(".models"):
            incoming, notes = normalize_models(
                incoming,
                provider_api=provider_api,
                default_ctx=args.default_context_window,
                default_max=args.default_max_tokens,
                normalize_profile=args.normalize_profile,
            )
            model_notes.extend(notes)

        oldv = get_path(new_cfg, dst_path)

        if args.preserve_existing_model_fields and dst_path.endswith(".models"):
            incoming = merge_with_existing_models(incoming, oldv)

        if dst_path.endswith(".models"):
            incoming = sort_models_by_id(incoming)

        if mode == "append_unique":
            newv = append_unique(oldv, incoming)
        else:
            newv = incoming

        if oldv != newv:
            set_path(new_cfg, dst_path, newv)
            changes.append({"to": dst_path, "from": src_path, "mode": mode})

    probe_results: List[Dict[str, Any]] = []
    picked_mode = None
    if args.probe_api_modes:
        modes = [x.strip() for x in args.probe_api_modes.split(",") if x.strip()]
        probe_model = model_notes[0]["id"] if model_notes else None
        if not probe_model:
            maybe_models = get_path(new_cfg, f"{provider_base}.models")
            if isinstance(maybe_models, list) and maybe_models:
                first = maybe_models[0]
                if isinstance(first, dict):
                    probe_model = first.get("id")

        if probe_model:
            base_v1 = to_base_v1_url(args.endpoint)
            for mode in modes:
                res = probe_mode(base_v1, mode, probe_model, headers)
                probe_results.append(res)

            for r in probe_results:
                if r.get("supported"):
                    picked_mode = r["mode"]
                    break

            if args.auto_detect_provider_api and picked_mode:
                old_api = get_path(new_cfg, f"{provider_base}.api")
                if old_api != picked_mode:
                    set_path(new_cfg, f"{provider_base}.api", picked_mode)
                    changes.append({"to": f"{provider_base}.api", "from": "(probe)", "mode": "replace"})

                    model_path = f"{provider_base}.models"
                    mlist = get_path(new_cfg, model_path)
                    if isinstance(mlist, list):
                        for model in mlist:
                            if isinstance(model, dict):
                                model["api"] = picked_mode
        else:
            probe_results.append({"mode": "(all)", "supported": False, "status": None, "detail": "no model id available for probing"})

    if args.sync_agent_aliases:
        provider_models = get_path(new_cfg, f"{provider_base}.models")
        if isinstance(provider_models, list):
            agents_obj = new_cfg.setdefault("agents", {})
            defaults_obj = agents_obj.setdefault("defaults", {})
            models_index = defaults_obj.setdefault("models", {})
            if not isinstance(models_index, dict):
                models_index = {}
                defaults_obj["models"] = models_index

            for model in provider_models:
                if not isinstance(model, dict):
                    continue
                mid = model.get("id")
                if not mid:
                    continue
                key = f"{args.provider_id}/{mid}"
                existing = models_index.get(key)

                if existing is None:
                    models_index[key] = {"alias": mid}
                    changes.append({"to": f"agents.defaults.models[{key}]", "from": "(sync-agent-aliases)", "mode": "replace"})
                elif isinstance(existing, dict) and ("alias" not in existing or not existing.get("alias")):
                    existing["alias"] = mid
                    changes.append({"to": f"agents.defaults.models[{key}].alias", "from": "(sync-agent-aliases)", "mode": "replace"})

    current_models = get_path(new_cfg, f"{provider_base}.models")
    previous_models = get_path(cfg, f"{provider_base}.models")
    model_delta = summarize_model_delta(previous_models, current_models)
    summary = build_summary(
        changes=changes,
        current_models=current_models,
        probe_results=probe_results,
        picked_mode=picked_mode,
        dry_run=args.dry_run,
        check_only=args.check_only,
        preserve_existing_model_fields=args.preserve_existing_model_fields,
        normalize_profile=args.normalize_profile,
        model_delta=model_delta,
    )

    if args.output == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_summary(summary)

    if not changes:
        return

    if args.dry_run or args.check_only:
        return

    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{args.config}.bak.{ts}"
    dump_json(backup, cfg)
    dump_json(args.config, new_cfg)

    if args.output == "json":
        summary["backup"] = backup
        summary["updated"] = args.config
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"\nBackup: {backup}")
        print(f"Updated: {args.config}")


if __name__ == "__main__":
    main()
