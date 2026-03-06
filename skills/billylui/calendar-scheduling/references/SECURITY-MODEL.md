# Security Model

The router delegates to two sub-skills (datetime and scheduling) based on user intent. All tools share the same MCP server binary and security model.

## Content Sanitization

All user-provided text (event summaries, descriptions) passes through a prompt injection firewall before reaching the calendar API:

- **Event summary** — checked for injection patterns
- **Event description** — checked for injection patterns
- **Rejected content** — returns an error asking the user to rephrase

This prevents malicious content from being written to calendars via AI agents. The firewall runs locally inside the MCP server process.

## Filesystem Containment

The MCP binary reads and writes only `~/.config/temporal-cortex/`:

| File | Purpose | Created By |
|------|---------|-----------|
| `credentials.json` | OAuth tokens for calendar providers | Setup wizard / auth command |
| `config.json` | Timezone, week start, provider labels | Setup wizard / configure script |

No other filesystem paths are accessed. Verifiable by:
- Inspecting the [open-source Rust code](https://github.com/temporal-cortex/mcp)
- Running under Docker where the volume mount is the only writable path

## Network Scope

| Layer | Tools | Network Access |
|-------|-------|---------------|
| Layer 1 (datetime) | `get_temporal_context`, `resolve_datetime`, `convert_timezone`, `compute_duration`, `adjust_timestamp` | **None** — pure local computation |
| Layers 2-4 (scheduling) | `list_calendars`, `list_events`, `find_free_slots`, `check_availability`, `expand_rrule`, `get_availability`, `book_slot` | Calendar provider APIs only |

Scheduling tools connect only to your configured providers:
- Google Calendar: `googleapis.com`
- Microsoft Outlook: `graph.microsoft.com`
- CalDAV: your configured server endpoint

No callbacks to Temporal Cortex servers. Telemetry is off by default.

## Tool Annotations

Only `book_slot` modifies external state. All other tools (11/12) are read-only and idempotent — safe to retry without side effects.

| Property | Value | Meaning |
|----------|-------|---------|
| `readOnlyHint` | `false` | `book_slot` creates calendar events |
| `destructiveHint` | `false` | Never deletes or overwrites existing events |
| `idempotentHint` | `false` | Calling `book_slot` twice creates two events |
| `openWorldHint` | `true` | Makes external API calls to calendar providers |

## Two-Phase Commit (book_slot)

The `book_slot` tool uses Two-Phase Commit (2PC) to guarantee conflict-free booking:

1. **LOCK** — Acquire exclusive lock on the time slot
2. **VERIFY** — Check for overlapping events and active locks
3. **WRITE** — Create event in the calendar provider
4. **RELEASE** — Release the exclusive lock

If any step fails, the lock is released and the booking is aborted. No partial writes.
