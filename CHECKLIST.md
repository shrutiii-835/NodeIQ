# CHECKLIST.md — NodeIQ Progress Tracker

This is the permanent, living progress tracker for NodeIQ, organized by the
implementation phases defined in [CONTEXT.md](CONTEXT.md) Section 8. Update
this file whenever a task is completed — check off the task and, if needed,
add newly-discovered sub-tasks. Do not remove future/unchecked tasks; they
stay listed (unchecked) until their phase is actually worked on.

---

## Progress Summary

- **Current Phase:** Phase 3.5A — Process Collector Design (complete)
- **Next Phase:** Phase 3.2C continues (next: implement the `processes` collector, following `docs/process_collector_design.md`)
- **Overall Progress:** 60 / 90 tasks complete (~67%)
- **Completed Tasks:** 60 (all of Phase 1, 13 of 14 in Phase 2, all of Phase 3.1, all of Phase 3.2A, all of Phase 3.2B, 2 of 9 in Phase 3.2C, all of Phase 3.4, all of Phase 3.5A)
- **Remaining Tasks:** 30 (1 in Phase 2, 7 in Phase 3.2C, all of Phases 4–8)

> This summary must be updated by hand whenever tasks below are checked or
> added, so it always matches the checkboxes further down this file.

---

## Phase 1 — Project Architecture

- [x] Define project folder structure (`docs/`, `snapshots/`, `src/nodeiq/`, `tests/`)
- [x] Write `README.md`
- [x] Write `CONTEXT.md`
- [x] Write `PROJECT_RULES.md`
- [x] Write `LOGS.md`
- [x] Create `requirements.txt` and `.gitignore`
- [x] Write `CHECKLIST.md` (this file)
- [x] Write `DECISIONS.md` (Architecture Decision Record)
- [x] Write `ROADMAP.md`
- [x] Write `LEARNING_NOTES.md`
- [x] Initialize git repository and make the first commit

## Phase 2 — Data Model

- [x] Define the top-level snapshot envelope schema (`timestamp`, `hostname`, `collection_errors`, etc.)
- [x] Define `metadata` section schema
- [x] Define `system` section schema
- [x] Define `cpu_memory` section schema
- [x] Define `processes` section schema
- [x] Define `disk` section schema (includes inode usage — see `docs/snapshot_schema.md` Section 14)
- [x] Define `services` section schema
- [x] Define `logs` section schema
- [x] Define `network` section schema
- [x] Define `scheduled_jobs` section schema
- [x] Define `permissions` section schema (scope intentionally conservative — flagged as an open question)
- [x] Define `collection_errors` section schema
- [x] Document all section schemas under `docs/` (`docs/snapshot_schema.md`, `docs/data_model_design.md`)
- [ ] Decide on schema representation in code (dataclasses vs. TypedDict)

## Phase 3 — Collectors

### Phase 3.1 — Core Execution Infrastructure

- [x] Create `src/nodeiq/core/` and `src/nodeiq/collectors/` package structure
- [x] Implement `CommandResult` (`core/result.py`)
- [x] Implement project-specific exceptions (`core/exceptions.py`)
- [x] Implement the command runner (`core/runner.py`) — timeout, stdout/stderr/returncode capture, duration measurement, never raises for a system-level failure
- [x] Add a documented scan coordinator placeholder (`core/coordinator.py`) — no scanning logic yet
- [x] Introduce `pytest`; write focused runner tests (success, non-zero exit, timeout)
- [x] Document the execution architecture (`docs/architecture.md`)

### Phase 3.2A — Collector Design Pattern

- [x] Document collector purpose, responsibilities, and non-responsibilities (`docs/collector_guidelines.md`)
- [x] Document the standard lifecycle: `collect()` → `run_command()` → parse → validate → return
- [x] Document separation of command execution and parsing
- [x] Document error handling expectations (the `(data, errors)` contract)
- [x] Document JSON output expectations
- [x] Document helper function conventions (`_parse_*`, `_validate_*`)
- [x] Document testing expectations for collectors
- [x] Review core infrastructure against the design; reconcile `collect()` return-type documentation (`PROJECT_RULES.md` Section 9, `core/coordinator.py`, `docs/architecture.md`)
- [x] Add ADR-012 (parsing location) and ADR-013 (no v1 application logging) to `DECISIONS.md`

### Phase 3.2B — Collector Infrastructure Refinement

- [x] Create `src/nodeiq/core/collector.py` with `CollectorContext` and `CollectorResult` dataclasses
- [x] Replace the `collect() -> tuple[dict, list[dict]]` contract with `collect(context) -> CollectorResult` in `docs/collector_guidelines.md`
- [x] Update `docs/architecture.md` diagram and layer explanations for the refined contract
- [x] Add ADR-014 (structured `CollectorResult` vs. tuple; why `CollectorContext` exists before many options need it)
- [x] Update `core/coordinator.py` docstring and `PROJECT_RULES.md` Section 9 (documentation only, no logic changed)
- [x] Add focused unit tests for `CollectorContext`/`CollectorResult`

### Phase 3.2C — Collectors (Implementation, in progress)

- [x] System metadata collector (`system`: hostname, operating_system, kernel_version, architecture, uptime_seconds — `os_name`/`os_version` split and `boot_time` deferred, see `docs/system_collector.md`)
- [x] CPU + memory collector (`cpu_memory`: memory/swap usage from `/proc/meminfo`, load averages from `/proc/loadavg` — CPU utilization percentages deferred; module renamed from `resource.py` to `cpu_memory.py` in Phase 3.4 to match `docs/snapshot_schema.md` Section 4; field-shape divergence — flat byte fields vs. nested kB, no `core_count` — still not reconciled, see `docs/cpu_memory_collector.md`)
- [ ] Processes collector (`processes` — design complete, see `docs/process_collector_design.md`; implementation not yet started)
- [ ] Disk + inodes collector (`disk`)
- [ ] Services collector (`services`)
- [ ] Logs collector (`logs`)
- [ ] Network collector (`network`)
- [ ] Scheduled jobs collector (`scheduled_jobs`: cron + systemd timers)
- [ ] Permissions collector (`permissions` — scope open, see `docs/snapshot_schema.md` Section 11)

### Phase 3.4 — Coordinator MVP

- [x] Rename `resource.py` to `cpu_memory.py` (module, tests, docs, and all references)
- [x] Implement `run_scan()`: build one `CollectorContext`, run registered collectors, aggregate errors, assemble an in-memory snapshot (no disk writes yet)
- [x] Register collectors in a simple list (`_REGISTERED_COLLECTORS`) — no plugin system
- [x] Populate `metadata` (`scan_timestamp`, `scan_duration_ms`, `collector_count`, `nodeiq_version`, `hostname`)
- [x] Add lightweight snapshot validation (`_validate_snapshot`) — no external validation library
- [x] Coordinator unit tests (fake collectors) and an end-to-end integration test verified on the Multipass VM
- [x] Document the coordinator (`docs/coordinator.md`)

### Phase 3.5A — Process Collector Design (design only, no code)

- [x] Document how Linux represents processes, `/proc/<pid>` structure, which files NodeIQ should/shouldn't use, and `/proc` vs. `ps` trade-offs (`docs/process_collector_design.md`)
- [x] Propose the v1 process schema (`pid`, `process_name`, `command`, `state`, `memory_rss_bytes`, `owner`, `start_time`, `threads`) with Source/Why/Required-or-optional for each field
- [x] Recommend a process summarization strategy (`process_count`, `top_by_memory`, zombie/`D`-state counts; not sending every process to the LLM)
- [x] Research and document Linux process states (`R`, `S`, `D`, `T`, `Z`) and their operational significance
- [x] Review `docs/snapshot_schema.md` Section 5's existing `processes` schema against this design and record recommended improvements (not implemented)

## Phase 4 — Report Generation

- [ ] Design human-readable report layout
- [ ] Implement report generator (snapshot JSON → readable text)
- [ ] Cover every snapshot section in the report output

## Phase 5 — CLI

- [ ] Wire up `argparse` with subcommands
- [ ] Implement `nodeiq scan`
- [ ] Implement `nodeiq report`
- [ ] Implement `nodeiq ask` (stub, before real LLM wiring)

## Phase 6 — LLM Integration

- [ ] Add OpenAI SDK dependency and `.env`-based key loading
- [ ] Design evidence-only prompt template
- [ ] Wire `ask` command to the OpenAI API
- [ ] Add guardrails so the LLM only answers from snapshot evidence

## Phase 7 — Robustness

- [ ] Apply timeouts to every subprocess call
- [ ] Handle partial collector failures end-to-end (verify `collection_errors` works in practice)
- [ ] Implement secret redaction for logs/config data
- [ ] Handle very large log volumes gracefully
- [ ] Handle missing systemd gracefully
- [ ] Handle different firewall implementations (iptables / nftables / ufw)
- [ ] Handle permission errors gracefully (e.g., non-root user)

## Phase 8 — Testing

- [ ] Unit tests for every collector (happy path + failure paths)
- [ ] Integration tests for CLI commands against fixture snapshots
- [ ] End-to-end validation pass
- [ ] Demo preparation

---

## Notes on Using This File

- Check a box only when the task is actually complete and verified, per the
  Definition of Done in `PROJECT_RULES.md`.
- If a task turns out to need splitting into smaller tasks mid-phase, add
  the new sub-tasks (unchecked) rather than silently expanding scope.
- Update the **Progress Summary** section at the top every time a checkbox
  changes, so the two never drift out of sync.
