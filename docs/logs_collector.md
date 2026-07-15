# Logs Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/logs.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the
ninth and final real Linux collector of NodeIQ v1 (Collector Sprint 2,
alongside `network.py`), following the same `CollectorContext` →
`collect()` → `CollectorResult` pattern as every previous collector.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `logs` section,
Section 8, whose `source`/`truncated` fields this implementation matches
— see "Schema Alignment" below).

---

## Responsibilities

The Logs Collector answers almost any "why did X happen?" question with
concrete, recent evidence: the most recent `_MAX_ENTRIES` (100)
warning-or-worse entries from the systemd journal, plus `warning_count`
and `error_count` computed from them. It deliberately never sends "the
logs" — only a small, bounded, recent slice, per this task's explicit
"avoid sending huge logs into the snapshot" instruction.

---

## Why `journalctl -o json`, Not `journalctl`'s Default Text Output

`journalctl`'s default output is a single human-oriented line per entry
(e.g. `Jul 15 07:00:01 main-cattle CRON[1234]: message`), with no
severity level shown inline at all — extracting `PRIORITY` would require
a separate flag combination, and the line format itself (timestamp
style, whether the PID is bracketed, whether the hostname is present)
has historically varied across `journalctl` versions and configurations.

`journalctl`'s own `--output=json` mode sidesteps all of this: one
complete JSON object per line (JSON Lines format), with every field
explicitly named — `__REALTIME_TIMESTAMP`, `PRIORITY`, `MESSAGE`,
`_SYSTEMD_UNIT`, `SYSLOG_IDENTIFIER`, and dozens more. This is the same
"prefer a machine-readable interface over parsing human-oriented text"
principle already applied throughout this project (`/proc` files over
commands, `df -P`, `systemctl --plain`), taken to its most direct form
yet: journald's own structured export format, rather than a flag that
merely makes text easier to parse.

Real output pulled from the Multipass VM (`journalctl -p warning -n 5
--no-pager -o json`), one entry:

```json
{"MESSAGE": "KASLR disabled due to lack of seed", "PRIORITY": "4",
 "SYSLOG_IDENTIFIER": "kernel", "__REALTIME_TIMESTAMP": "1784090714321586", ...}
```

`-p warning` filters to priority 4 (warning) or more urgent (0-3) —
exactly the "recent warning/error entries" this task asks for, in one
flag, with no post-filtering needed in this collector at all.

---

## Two Real Edge Cases in Journal Records

Pulled directly from real VM output, and handled explicitly rather than
assumed away:

1. **The unit name comes from different fields depending on the log
   source.** A systemd-managed service's entry has `_SYSTEMD_UNIT`
   (e.g. `"cron.service"`); a kernel message has no such field at all,
   only `SYSLOG_IDENTIFIER` (e.g. `"kernel"`). `_parse_journal_record`
   tries `_SYSTEMD_UNIT` first, falls back to `SYSLOG_IDENTIFIER`, and
   falls back again to the literal string `"unknown"` if neither is
   present — never a `KeyError`.
2. **`MESSAGE` can be a list of raw byte values instead of a string.**
   journald represents a message this way when the original bytes
   weren't valid UTF-8 (this can genuinely happen — binary data
   accidentally logged, a corrupted message, non-UTF-8 locale output).
   `_parse_message` detects a list and decodes it with
   `errors="replace"` rather than crashing or silently dropping the
   entry.

---

## Why `truncated` Is Computed the Way It Is

`docs/snapshot_schema.md` Section 8 already anticipated a `truncated`
flag — "whether consumers are seeing the complete picture." This
collector always requests exactly `_MAX_ENTRIES` entries via `-n`, so it
has no direct way to ask journald "how many matching entries exist in
total, beyond what I fetched." The honest, cheap-to-compute
approximation: `truncated = len(entries) >= _MAX_ENTRIES` — if fewer
entries than the cap came back, that's genuinely everything available
(journald had less than 100 to give); if exactly the cap came back,
there could be more that weren't fetched. This never overclaims
completeness and never requires an extra command just to count a total.

---

## Why the Entry List Is Named `recent_entries`, Not `recent_errors`

`docs/snapshot_schema.md` Section 8 names its list `recent_errors`, but
this collector's list holds **both** warnings and errors (per this
task's explicit "last 100 warning/error entries" scope) — calling a
mixed-severity list `recent_errors` would misdescribe roughly half its
contents on a typical healthy system (real VM data: 29 warnings, 0
errors in the last 100). `recent_entries` is used instead, flagged here
explicitly rather than silently matching a name that no longer fits, per
this project's established practice for schema-naming divergences.

---

## Error Handling and Graceful Degradation

There is exactly one command, and exactly one anticipated failure mode:
`journalctl` doesn't exist, or fails to run for any other reason (e.g.
no systemd journal on this system at all). This is this collector's
primary degradation path, conceptually the same as `DECISIONS.md`
ADR-010's "detect the absence of systemd and degrade gracefully" —
applied here to journald rather than `systemctl`. On that failure,
`source` becomes `"unavailable"` (matching the schema's own suggested
value), every count is `None`, `recent_entries` is `[]`, and one error
entry is recorded.

A single malformed JSON line within an otherwise-successful fetch is
handled at a finer grain: `_parse_journal_json` skips just that one
line and continues, rather than discarding the whole batch or raising —
one odd journal entry shouldn't cost every other one.

---

## Schema Alignment

`docs/snapshot_schema.md` Section 8's `source`/`truncated` fields are
matched exactly. The entry list is renamed `recent_entries` (see above),
and its per-entry shape (`timestamp`, `severity`, `unit`, `message`)
adds `severity` — not present in the original schema's `recent_errors`
entries at all, but necessary here since this list holds both
severities and a consumer needs to tell them apart. `warning_count`/
`error_count` are new top-level fields, added per this task's explicit
instruction, with no prior schema equivalent.

---

## Testing

- **Unit tests** (`tests/collectors/test_logs.py`, 19 tests): every
  `_parse_*` function tested with literal sample values, including both
  edge cases above (missing unit fields, a non-UTF-8-style `MESSAGE`
  list) and the `truncated` flag at, above, and below `_MAX_ENTRIES`;
  `collect()` tested end-to-end for the happy path and `journalctl`
  being entirely unavailable.
- **Integration test** (`tests/collectors/test_logs_integration.py`, 1
  test): calls the real `collect()` with nothing mocked, automatically
  skipped unless running on Linux. Verified on the Multipass VM (real
  result: 29 warnings, 0 errors in the last 100 matching entries, not
  truncated, no errors) as part of the full 193-test suite for this
  sprint — the last piece of NodeIQ v1's complete data collection layer.

---

## Collector Review Checklist

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — the one command failure mode is caught; a single malformed log line is skipped, not fatal.
- [x] Uses `nodeiq.core.runner.run_command` — never raw `subprocess`.
- [x] Parsing is separated from command execution: every `_parse_*` function is pure, tested with literal sample text/records.
- [x] Never sends unbounded log data — `_MAX_ENTRIES` is a named constant (not a magic number), used directly in the command itself (`-n <_MAX_ENTRIES>`), so the cap is adjustable in one place.
- [x] `truncated` is computed honestly (based on hitting the cap), never assumed `False`.
- [x] Handles two real journald edge cases (missing unit fields, non-UTF-8 `MESSAGE`) without crashing.
- [x] Degrades gracefully when `journalctl`/the journal is unavailable, matching the same spirit as `DECISIONS.md` ADR-010's systemd-absence handling.
- [x] Field names mostly match `docs/snapshot_schema.md` Section 8; the one naming divergence (`recent_entries` vs. `recent_errors`) is explicitly justified, not silent.
- [x] Unit tests cover parsing (including both edge cases), truncation logic, and `collect()` end-to-end (happy path and total unavailability); an integration test verifies real behavior on the Multipass VM.
