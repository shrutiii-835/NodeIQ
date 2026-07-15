# Services Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/services.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the
fifth real Linux collector (Collector Sprint 1, alongside
`scheduled_jobs.py` and `permissions.py`), following the same
`CollectorContext` → `collect()` → `CollectorResult` pattern as every
previous collector.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `services`
section, Section 7).

---

## Responsibilities

The Services Collector answers "what service failed?" — one of
NodeIQ's headline example questions. It runs two `systemctl`
invocations and combines them into one summary:

- **`systemctl list-units --type=service --all`** — every service's
  current load/active/sub state, used to compute
  `running_services_count`, `failed_services_count`, `failed_services`
  (full detail per failed service), and `restarting_services` (services
  whose sub-state is `auto-restart` — mid-retry after a failure, for
  units configured with `Restart=`).
- **`systemctl list-unit-files --type=service`** — whether each service
  is enabled to start at boot, used to compute `enabled_services_count`
  (services whose enablement state is exactly `"enabled"`).

`systemd_available` (matching `docs/snapshot_schema.md` Section 7 and
`DECISIONS.md` ADR-010) is `True` unless the first command fails
outright — the clearest, simplest signal this collector has for
"systemd doesn't exist here."

---

## Why Two Separate `systemctl` Commands

`list-units` and `list-unit-files` report genuinely different facts:
*is this service currently running* (a runtime, point-in-time state) vs.
*is this service configured to start automatically* (a persistent,
boot-time configuration). Neither command reports both, so they're
gathered and parsed independently — the same "separation of command
execution and parsing" principle every collector already follows, just
applied to two commands feeding one summary instead of one.

Real output pulled from the Multipass VM:

```
$ systemctl list-units --type=service --all --no-legend --no-pager --plain
apparmor.service   loaded    active   exited  Load AppArmor profiles
auditd.service     not-found inactive dead    auditd.service
...

$ systemctl list-unit-files --type=service --no-legend --no-pager --plain
apparmor.service   enabled  enabled
apport.service     static   -
...
```

Both are read with `--plain --no-legend --no-pager`, matching this
project's established convention (`docs/disk_collector.md`'s use of
`df -P`): these flags produce a stable, header-free, one-line-per-unit
format with no interactive pager to hang on, so each line can be parsed
by simple whitespace splitting.

---

## How `systemd_available` and Graceful Degradation Work

Per `DECISIONS.md` ADR-010, a missing systemd must degrade gracefully,
never crash the scan. This collector's two commands are handled
asymmetrically, because they're not equally important:

- **If `list-units` fails** (most notably because `systemctl` doesn't
  exist at all): nothing about service state can be known, so
  `systemd_available` is `False`, every count is `None`, and both list
  fields come back empty — with one error entry recorded.
- **If only `list-unit-files` fails**: `systemd_available` is still
  `True` and every other field (from `list-units`) is fully populated —
  only `enabled_services_count` becomes `None`, with its own error
  entry. Partial data always beats no data (`PROJECT_RULES.md`
  Section 7).

Verified for real: on macOS (no `systemctl` at all), `collect()`
correctly returns `systemd_available: False` with every count `None`
and a clear error entry, rather than crashing.

---

## Testing

- **Unit tests** (`tests/collectors/test_services.py`, 11 tests):
  `_parse_service_units` and `_parse_unit_files` tested with literal
  sample text; `_summarize_services` tested for running/failed counts,
  restarting-service detection, and the empty case; `collect()` tested
  end-to-end for the happy path, `systemctl` missing entirely, and only
  the unit-files command failing.
- **Integration test**
  (`tests/collectors/test_services_integration.py`, 1 test): calls the
  real `collect()` with nothing mocked, automatically skipped unless
  running on Linux. Verified on the Multipass VM (real result: 54
  running services, 0 failed, 45 enabled, no errors) as part of the full
  151-test suite for this sprint.

---

## Collector Review Checklist

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — both anticipated failure points (either `systemctl` invocation failing) are caught and turned into error entries.
- [x] `systemd_available` (DECISIONS.md ADR-010) is reported explicitly, with full graceful degradation when systemd is absent.
- [x] Uses `nodeiq.core.runner.run_command` for both invocations — never raw `subprocess`.
- [x] Parsing is separated from command execution: `_parse_service_units` and `_parse_unit_files` are pure functions, tested with literal sample text.
- [x] `list-units` and `list-unit-files` failures are independent — an enabled-count failure never loses the running/failed/restarting data already gathered.
- [x] No unnecessary abstractions — no generic "systemctl output parser" framework, just two small, purpose-built parsers.
- [x] Field names use `snake_case`; no collector-invented redaction, logging, retries, or presentation logic.
- [x] Unit tests cover parsing, summarization, and `collect()` end-to-end (happy path and both partial-failure modes); an integration test verifies real behavior on the Multipass VM.
