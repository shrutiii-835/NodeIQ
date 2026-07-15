# Architecture — Core Execution Infrastructure (Phase 3.1–3.4)

**Status:** `nodeiq.core` exists and is tested, including the collector
contract types (`CollectorContext`, `CollectorResult`) and a working
`run_scan()` coordinator (Phase 3.4). `nodeiq.collectors` has two real
collectors, `system.py` and `cpu_memory.py` — the remaining seven are
still scaffolding. No CLI or LLM integration exists yet; `run_scan()`
returns an in-memory snapshot dict and never writes to disk.

This document explains the code built in Phase 3.1, refined in Phase
3.2B, and completed (for the coordinator) in Phase 3.4 — the reusable
foundation every collector runs on top of. For the *data* architecture
(what a snapshot looks like), see [snapshot_schema.md](snapshot_schema.md)
and [data_model_design.md](data_model_design.md). For the practical,
how-to-write-a-collector contract, see
[collector_guidelines.md](collector_guidelines.md). For the coordinator
itself, see [coordinator.md](coordinator.md). For the overall project
architecture and phases, see [CONTEXT.md](../CONTEXT.md).

---

## Diagram

```
                         ┌───────────────────────────┐
                         │   nodeiq.core.coordinator   │  run_scan() —
                         │   builds one CollectorContext│  implemented,
                         │   "run every collector,      │  Phase 3.4
                         │    assemble one snapshot"    │
                         └─────────────┬─────────────────┘
                                       │ passes the same CollectorContext
                                       │ to every collect() call
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                 ▼
              ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
              │ collectors/  │   │ collectors/  │   │ collectors/  │  ... (not yet
              │  system.py   │   │cpu_memory.py │   │ services.py  │       built)
              │ collect(ctx) │   │ collect(ctx) │   │ collect(ctx) │
              └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
                     │   each returns one CollectorResult  │
                     └─────────────────┼─────────────────┘
                                       ▼
                         ┌─────────────────────────┐
                         │   nodeiq.core.runner      │
                         │   run_command(...)        │  ← built in Phase 3.1
                         └────────────┬─────────────┘
                                      │ uses
                                      ▼
                         ┌─────────────────────────┐
                         │   Python's subprocess     │
                         │   (shell=False, timeout)  │
                         └────────────┬─────────────┘
                                      │ launches
                                      ▼
                         ┌─────────────────────────┐
                         │   The real Linux system   │
                         │   (df, systemctl, /proc)  │
                         └─────────────────────────┘

    CollectorContext (nodeiq.core.collector) — scan_start_time,
    default_timeout — is built once per scan and shared, read-only,
    with every collector's collect() call.

    CollectorResult (nodeiq.core.collector) — collector_name, data,
    errors, duration_ms, and a computed success — is what every
    collect() call returns to the coordinator.

    run_command() always returns a CommandResult (nodeiq.core.result) —
    never an exception from anything the OS or the command itself did
    wrong.
```

---

## Dependency Flow

Dependencies only ever point **downward** in the diagram above — nothing
at the bottom knows anything about what's above it:

- `nodeiq.core.runner` depends on Python's `subprocess` and
  `nodeiq.core.result` / `nodeiq.core.exceptions`. It knows nothing about
  collectors, the coordinator, or snapshots.
- A collector (e.g. `system.py`, `cpu_memory.py`) depends on
  `nodeiq.core.runner` to actually run commands, on `nodeiq.core.result`
  to understand what came back, and on `nodeiq.core.collector` for the
  `CollectorContext`/`CollectorResult` types. It knows nothing about any
  other collector, and nothing about the coordinator that calls it.
- `nodeiq.core.coordinator` is the only module that depends on multiple
  collectors at once — this is deliberate and expected (see
  `docs/coordinator.md`), not a violation of collector independence.

This one-directional flow is what makes "one broken collector never stops
the whole scan" (PROJECT_RULES.md Section 7) achievable: nothing upstream
of the coordinator can be affected by anything downstream misbehaving,
because nothing downstream is aware anything upstream exists.

---

## The Layers, Explained

### `nodeiq.core.result` — `CommandResult`

A small, immutable (`frozen=True`) dataclass holding everything about one
command execution: the command itself, its exit code, its stdout, its
stderr, how long it took, whether it timed out, and an error message if it
couldn't be run at all. Every other layer speaks in terms of this object
rather than raw subprocess internals.

### `nodeiq.core.exceptions` — `NodeIQError`, `InvalidCommandError`

Deliberately minimal. `run_command` never raises for anything the *system*
does wrong (a missing program, a timeout) — those become data inside a
`CommandResult`. `InvalidCommandError` is the one exception that exists,
reserved for a genuine programmer mistake (calling `run_command` with
something that isn't a valid command), which should fail immediately
rather than be silently absorbed like a real command's failure would be.

### `nodeiq.core.runner` — `run_command`

The one function in NodeIQ that actually calls `subprocess`. Every
collector will call this instead of using `subprocess` directly, which
means every collector automatically gets the same timeout handling, the
same `shell=False` safety, and the same "never raises for a system-level
failure" guarantee, without having to reimplement any of it.

### `nodeiq.core.collector` — `CollectorContext`, `CollectorResult`

Two small, immutable (`frozen=True`) dataclasses defining the collector
contract itself — not a base class, not a framework, just the shape of
what every `collect()` function receives and returns:

- **`CollectorContext`** carries information shared across a whole scan —
  currently `scan_start_time` and `default_timeout`. The coordinator will
  build exactly one of these per scan and pass the same instance to every
  collector, so all collectors agree on timing and timeout defaults
  without each deciding independently.
- **`CollectorResult`** is what every `collect()` call returns:
  `collector_name`, `data`, `errors`, `duration_ms`, and a computed
  `success` property. This replaces the earlier `(data, errors)` tuple
  contract from Phase 3.2A — see `DECISIONS.md` ADR-014 for why.

### `nodeiq.collectors` (two collectors built)

Holds one module per snapshot section (`system.py`, `cpu_memory.py`,
`disk.py`, ...), each exposing `collect(context: CollectorContext) ->
CollectorResult`, using `nodeiq.core.runner` (or, for `/proc`-backed data,
plain file I/O) to gather its own data. `system.py` (Phase 3.2C) and
`cpu_memory.py` (Phase 3.3, renamed from `resource.py` in Phase 3.4) are
built so far — see `docs/system_collector.md` and
`docs/cpu_memory_collector.md`. The remaining seven are still
scaffolding, following the same contract in `docs/collector_guidelines.md`.

### `nodeiq.core.coordinator` — `run_scan()` (MVP implemented, Phase 3.4)

The single orchestrator: builds one `CollectorContext`, calls every
registered collector with it, catches whatever each one raises, and
assembles the final snapshot dict from each returned `CollectorResult` —
see `docs/coordinator.md` for the full design and
`src/nodeiq/core/coordinator.py`'s own docstring. `_REGISTERED_COLLECTORS`
is currently `[system, cpu_memory]`; the remaining seven collectors will
be added to that list as they're built. `run_scan()` returns an in-memory
dict only — writing a snapshot to disk is Phase 5 (CLI).

---

## Why Collectors Remain Independent

Every collector will depend only on `nodeiq.core` (shared, generic
infrastructure) and nothing else in the codebase — never on another
collector's code or output. This is what CONTEXT.md Section 6 and
PROJECT_RULES.md Section 9 require, and it's enforced structurally here:
there is no code path by which one future collector module could import or
call another. The only thing collectors share is the runner underneath
them, and the runner has no memory between calls — running one command
tells the runner nothing about any other command that was ever run.

The practical payoff (see PROJECT_RULES.md Section 7): if the future
`services.py` collector breaks because `systemctl` is missing on some
system, that failure is contained entirely inside that one collector call.
Nothing about `disk.py` or `network.py` running afterward is affected,
because neither one ever depended on `services.py` succeeding — or even
running at all.

## Why the Coordinator Owns Snapshot Assembly

No individual collector ever sees the full snapshot — each one only ever
produces its own section, as the `data` field of the `CollectorResult` it
returns. Only the coordinator (Phase 3.4) holds the full picture, because
assembling the snapshot requires knowing about *every* collector at once
— something no single collector should need to know. This keeps
each collector's job small and testable in isolation (see
PROJECT_RULES.md Section 11, Testing Philosophy) while still producing
one coherent, complete snapshot at the end.

This also concentrates two other coordinator-only responsibilities in one
place, rather than spreading them across every collector: populating
`metadata` (facts about the scan itself — see docs/snapshot_schema.md
Section 2) and populating `collection_errors` (aggregating whatever each
collector reported went wrong — see docs/snapshot_schema.md Section 12).
Neither of these belongs to any individual collector, because both are
about the scan as a whole.

## Why the Runner Centralizes Subprocess Execution

Without a shared runner, every collector would need to independently get
several things right: use `shell=False`, apply a timeout, capture stdout
and stderr separately, and catch every way a subprocess call can fail.
Centralizing this in `nodeiq.core.runner`:

- Guarantees every collector gets the same safety properties automatically
  (PROJECT_RULES.md Section 9, item 8: every subprocess call needs a
  timeout — trivially true here, since there's only one place subprocess
  calls happen).
- Means a future improvement to how commands are run (a new safety check,
  better logging) only has to be made once, in one file, to benefit every
  collector at once.
- Makes the runner itself independently and thoroughly testable
  (`tests/core/test_runner.py`) without needing any real collector to
  exist yet — which is exactly what Phase 3.1 does, deliberately, before
  Phase 3.2C builds `system.py` (and the rest) on top of it.
