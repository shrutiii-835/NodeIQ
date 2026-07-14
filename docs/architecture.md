# Architecture — Core Execution Infrastructure (Phase 3.1)

**Status:** `nodeiq.core` exists and is tested. `nodeiq.collectors` is an
empty package waiting for its first collector (Phase 3.2). No CLI or LLM
integration exists yet.

This document explains the code built in Phase 3.1 — the reusable
foundation every future collector will run on top of. For the *data*
architecture (what a snapshot looks like), see
[snapshot_schema.md](snapshot_schema.md) and
[data_model_design.md](data_model_design.md). For the overall project
architecture and phases, see [CONTEXT.md](../CONTEXT.md).

---

## Diagram

```
                         ┌─────────────────────────┐
                         │   nodeiq.core.coordinator │   (Phase 3.2 — placeholder only)
                         │   "run every collector,   │
                         │    assemble one snapshot" │
                         └────────────┬─────────────┘
                                      │ will call (future)
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
              ┌────────────┐   ┌────────────┐   ┌────────────┐
              │ collectors/ │   │ collectors/ │   │ collectors/ │   ... (Phase 3.2,
              │  system.py  │   │   disk.py   │   │ services.py │        not yet built)
              └──────┬─────┘   └──────┬─────┘   └──────┬─────┘
                     │                │                │
                     └────────────────┼────────────────┘
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

              run_command() always returns a CommandResult
              (nodeiq.core.result) — never an exception from
              anything the OS or the command itself did wrong.
```

---

## Dependency Flow

Dependencies only ever point **downward** in the diagram above — nothing
at the bottom knows anything about what's above it:

- `nodeiq.core.runner` depends on Python's `subprocess` and
  `nodeiq.core.result` / `nodeiq.core.exceptions`. It knows nothing about
  collectors, the coordinator, or snapshots.
- A collector (Phase 3.2) will depend on `nodeiq.core.runner` to actually
  run commands, and on `nodeiq.core.result` to understand what came back.
  It will know nothing about any other collector, and nothing about the
  coordinator that will eventually call it.
- `nodeiq.core.coordinator` (still a placeholder) will be the only module
  that depends on multiple collectors at once.

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

### `nodeiq.collectors` (empty so far)

Will hold one module per snapshot section (`system.py`, `disk.py`, ...),
each using `nodeiq.core.runner` to gather its own data and returning
`(data, errors)` — a plain `dict` matching its section of
`docs/snapshot_schema.md`, plus a list of anything that went wrong. Built
in Phase 3.2B, following the contract in `docs/collector_guidelines.md`
(Phase 3.2A).

### `nodeiq.core.coordinator` (placeholder so far)

Will be the single orchestrator that runs every collector, catches
whatever each one raises, and assembles the final JSON snapshot — see the
module's own docstring for the full plan. Built once collectors exist to
orchestrate (Phase 3.2).

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
produces its own section as a plain `dict`. Only the coordinator (Phase
3.2) will hold the full picture, because assembling the snapshot requires
knowing about *every* collector at once — something no single collector
should need to know. This keeps each collector's job small and testable in
isolation (see PROJECT_RULES.md Section 11, Testing Philosophy) while
still producing one coherent, complete snapshot at the end.

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
  Phase 3.2 builds anything on top of it.
