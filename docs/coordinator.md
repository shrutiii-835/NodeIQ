# Scan Coordinator — NodeIQ

**Status:** Implemented (MVP) and tested (`src/nodeiq/core/coordinator.py`),
both with mocked unit tests (fake collectors) and a real end-to-end
integration test verified against the Multipass Ubuntu 24.04 VM
(`DECISIONS.md` ADR-002). This is the first working implementation of
`run_scan()` — it replaces the `NotImplementedError` placeholder that
existed since Phase 3.1.

This is the first task to prove the whole architecture works end to end:

```
CollectorContext → collectors → CollectorResult → coordinator → snapshot
```

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the fuller envelope this MVP
deliberately simplifies — see "MVP Simplifications" below). No CLI and no
disk-writing exist yet — `run_scan()` returns a plain in-memory dict.

---

## Responsibilities

`run_scan()` (in `nodeiq.core.coordinator`) does exactly five things:

1. Builds one `CollectorContext` for the scan.
2. Runs every registered collector with that context.
3. Aggregates whatever each collector reported went wrong.
4. Builds `metadata` describing the scan itself.
5. Assembles everything into one snapshot dict and returns it.

It does **not** decide what the collectors collect (that's each
collector's own job), does not write anything to disk, and does not know
about the CLI (`scan`/`report`/`ask`) that will eventually call it —
those are all later phases.

---

## Why Collectors Remain Independent

This is the same principle established in `docs/data_model_design.md`
and `docs/collector_guidelines.md`, now proven in running code rather
than just documented: the coordinator imports `system` and `cpu_memory`
directly, but neither collector imports the other, imports the
coordinator, or knows the coordinator exists. Each collector's entire
interface to the outside world is its one `collect(context) ->
CollectorResult` function.

The practical proof is in `_REGISTERED_COLLECTORS` and the loop that runs
it: the coordinator calls `collector_module.collect(context)` for each
registered module in turn, and nothing about how one collector runs
(or fails) is visible to, or has any effect on, the next one. The unit
tests (`tests/core/test_coordinator.py`) exercise this directly with fake
collector modules that have nothing to do with `system`/`cpu_memory` at
all — the coordinator's orchestration logic doesn't care what a
collector's internals look like, only that it exposes the standard
`collect(context) -> CollectorResult` shape.

---

## Why the Coordinator Owns Orchestration

Only the coordinator knows about *every* collector at once — this is
deliberate and is what actually makes "one broken collector never stops
the whole scan" true in practice, not just in principle:

- Each `collector_module.collect(context)` call is wrapped in its own
  `try`/`except Exception`. If a collector's own error handling somehow
  fails and it raises anyway, that failure is caught right there, in the
  one loop iteration for that collector, and recorded as a
  `collection_errors` entry — the loop then moves on to the next
  collector unaffected.
- No collector needs to know this safety net exists. Per
  `docs/collector_guidelines.md`, every collector is still expected to
  catch its own anticipated failures first; the coordinator's `except
  Exception` is a last resort for the unexpected case, not a substitute
  for a collector's own error handling.

This is why orchestration belongs in exactly one place rather than being
spread across collectors: if every collector had to defend against *other
collectors* failing, that would mean collectors knowing about each other
— the opposite of the independence this architecture is built around.

---

## Snapshot Assembly Process

For each registered collector module, in order:

1. Compute a fallback name from the module's own dotted `__name__` (e.g.
   `nodeiq.collectors.system` → `"system"`) — used only if the collector
   crashes before returning anything.
2. Call `collector_module.collect(context)`.
3. **If it raises:** record a crash entry in `collection_errors` under
   the fallback name, and set that section to `None` in the snapshot.
4. **If it returns a `CollectorResult`:** store `result.data` under
   `result.collector_name` in the snapshot, and — if `result.errors` is
   non-empty — store it under the same name in `collection_errors`.

After every collector has run, the coordinator builds `metadata` (see
below) and returns:

```python
{
    "metadata": {...},
    "collection_errors": {...},
    "system": {...},       # or None, if system crashed
    "cpu_memory": {...},   # or None, if cpu_memory crashed
}
```

`_validate_snapshot` then does one final, lightweight check (see "Snapshot
Validation" below) before the dict is returned.

---

## Error Aggregation

`collection_errors` is a plain dict, keyed by collector name, exactly
matching the shape defined in `docs/snapshot_schema.md` Section 12 — a
collector name maps to a list of error-detail dicts (`message`,
`severity`, `exception_type`). Two things feed it:

- **The normal path:** a collector caught its own anticipated failure
  (per `docs/collector_guidelines.md`) and returned it in
  `CollectorResult.errors`. The coordinator just copies this list into
  `collection_errors[result.collector_name]` if it's non-empty.
- **The crash path:** a collector raised an exception the coordinator had
  to catch itself. The coordinator builds a single-entry list describing
  the crash (`"collector crashed: {exc}"`, `severity: "error"`,
  `exception_type` from the exception's class name) under the fallback
  name.

A collector that succeeds completely contributes nothing to
`collection_errors` at all — an empty `collection_errors` dict means
every registered collector ran cleanly, matching
`docs/snapshot_schema.md` Section 12's "empty means everything succeeded"
convention exactly.

---

## Metadata Generation

`metadata` is built entirely by the coordinator, never by a collector —
per `docs/snapshot_schema.md` Section 2 and `docs/data_model_design.md`,
this data describes the *scan process*, not the machine, so no individual
collector should own it. This MVP's `metadata` is intentionally small:

| Field | Source |
|---|---|
| `scan_timestamp` | `CollectorContext.scan_start_time`, ISO 8601 |
| `scan_duration_ms` | Wall-clock time for the whole `run_scan()` call |
| `collector_count` | `len(_REGISTERED_COLLECTORS)` |
| `nodeiq_version` | `nodeiq.__version__` |
| `hostname` | `system`'s collected `hostname` field, if the `system` collector produced one — `None` otherwise |

`hostname` is the one field that depends on a collector's output rather
than the scan process alone — this is explicitly allowed by this task's
own instructions ("reuse collected system hostname if available") and is
read defensively: if `system` crashed entirely (its section is `None`) or
succeeded but couldn't determine its own `hostname` field, `metadata.hostname`
is simply `None` too, never an error.

---

## Snapshot Validation

`_validate_snapshot` is a plain function — no external validation
library — that checks four required keys
(`metadata`, `system`, `cpu_memory`, `collection_errors`) are present in
the assembled dict, raising `ValueError` naming exactly which key(s) are
missing if not. With the current two registered collectors, every
section is always populated one way or another (successfully, or as a
recorded crash with `None`), so this check is a defensive safety net
against a *coordinator* bug (e.g. a future collector whose
`collector_name` doesn't match what's expected), not something normal
collector failures should ever trigger.

---

## MVP Simplifications (Known, Deliberate Divergences)

This task's `metadata` and top-level snapshot shape are simpler than the
fuller envelope already defined in `docs/snapshot_schema.md`. Recorded
explicitly here, per this project's established practice of flagging such
tensions rather than silently resolving or ignoring them:

- **No top-level `timestamp`/`hostname` keys.** `docs/snapshot_schema.md`
  Section 1 has denormalized `timestamp` and `hostname` fields at the
  snapshot's top level, separate from `metadata`. This MVP puts
  `hostname` inside `metadata` only, and has no top-level `timestamp` at
  all (only `metadata.scan_timestamp`).
- **`metadata` has 5 fields, not 7.** `docs/snapshot_schema.md` Section 2
  also specifies `schema_version`, `scan_started_at` *and*
  `scan_finished_at` (two timestamps, not one), and
  `collectors_run`/`collectors_skipped` lists. This MVP has one
  `scan_timestamp`, one `scan_duration_ms`, and no schema version or
  per-collector run/skip lists.
- **Only two collectors are registered.** `_REGISTERED_COLLECTORS` is
  `[system, cpu_memory]` — the seven other planned collectors
  (`processes`, `disk`, `services`, `logs`, `network`, `scheduled_jobs`,
  `permissions`) don't exist yet (per `CHECKLIST.md`), so `collector_count`
  is currently always `2`.

None of these are bugs — they're the smallest useful implementation that
proves the architecture works, per this task's explicit objective. A
follow-up task should decide whether to grow `run_scan()`'s `metadata`
and snapshot shape to match `docs/snapshot_schema.md` exactly, or update
that schema doc to reflect the simpler shape actually built.

---

## Testing

- **Unit tests** (`tests/core/test_coordinator.py`, 11 tests): use fake
  "collector modules" (simple objects with a `collect(context)` function
  and a dotted `__name__`) instead of the real `system`/`cpu_memory`
  collectors, so these tests verify the coordinator's own orchestration
  logic — every collector runs, data is assembled under the right key,
  errors aggregate correctly, a crash in one collector doesn't stop the
  next, metadata is populated correctly (including the `hostname`
  fallback to `None`), and `_validate_snapshot` both passes and fails as
  expected.
- **Integration test** (`tests/core/test_coordinator_integration.py`, 1
  test): calls the real `run_scan()` with the real `system` and
  `cpu_memory` collectors, no mocking at all, automatically skipped
  unless running on Linux. Verified by copying the code to the Multipass
  Ubuntu 24.04 VM (`main-cattle`), installing `pytest` there, and running
  the full 60-test suite — all 60 passed, including this one running for
  real, producing a genuine, complete, error-free snapshot (see the
  Example Assembled Snapshot in this session's final output).

---

## Coordinator Review Checklist

- [x] Builds exactly one `CollectorContext` per scan and passes the same instance to every collector.
- [x] Collectors are called through their single entry point, `collect(context) -> CollectorResult` — nothing else about a collector's internals is touched.
- [x] Every collector call is individually wrapped in `try`/`except Exception` — one crashing collector never stops the rest of the loop.
- [x] `collection_errors` aggregates both the normal path (a collector's own reported `errors`) and the crash path (an unhandled exception), in the same shape either way.
- [x] `metadata` is built entirely by the coordinator — no collector writes to it directly.
- [x] No collector is aware of the coordinator, of any other collector, or of the snapshot being assembled — verified both by code inspection and by unit tests using fake collectors that share no code with the real ones.
- [x] `_REGISTERED_COLLECTORS` is a plain list — no registry class, no plugin discovery, no dynamic import mechanism.
- [x] Snapshot validation is a plain function checking key presence — no external validation library.
- [x] Does not write to disk; does not import or depend on anything CLI-related.
- [x] Unit tests use fakes and never depend on the real machine's state; an integration test verifies real behavior on the Multipass VM.
- [ ] *(Deferred, not yet reconciled)* `metadata` shape and top-level envelope fully match `docs/snapshot_schema.md` Sections 1–2 — see "MVP Simplifications" above.
