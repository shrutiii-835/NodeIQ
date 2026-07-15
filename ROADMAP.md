# ROADMAP.md — NodeIQ High-Level Roadmap

This file tracks NodeIQ's milestones at a high level. For the detailed,
checkbox-level task breakdown, see [CHECKLIST.md](CHECKLIST.md). For *why*
each milestone is ordered this way, see [CONTEXT.md](CONTEXT.md) Section 8.

---

## Current Milestone

**Phase 3.5B — Process Collector Implementation**

The third real Linux collector: `collectors/processes.py` implements the
design from Phase 3.5A, reading only `/proc/<pid>/status`, `cmdline`, and
`comm` directly (`ps` is never invoked; `stat` is intentionally
deferred). It produces `process_count`, `zombie_count`,
`blocked_process_count`, and the top 10 processes by memory
(`top_by_memory`, with `owner` resolved from UID). A process that exits
mid-scan is skipped gracefully, never as a collector-wide error.
Registered with the coordinator (`_REGISTERED_COLLECTORS`), verified with
both mocked unit tests and a real end-to-end integration test on the
Multipass VM (88 tests passing) — see `docs/process_collector.md`.

---

## Upcoming Milestone

**Phase 3.2C continued — Remaining Collectors**

Implement each remaining Linux data collector independently, following
`system.py`, `cpu_memory.py`, and `processes.py` as templates: disk +
inodes, services, logs, network, scheduled jobs, permissions —
registering each one with the coordinator (`docs/coordinator.md`) as
it's built, so `run_scan()`'s snapshot grows one section at a time.

---

## Long-Term Milestones

1. **Phase 3.2C — Collectors** *(see Upcoming Milestone above for detail)*

2. **Phase 4 — Report Generation**
   Turn a snapshot into a clear, human-readable report.

3. **Phase 5 — CLI**
   Wire up `nodeiq scan`, `nodeiq report`, and `nodeiq ask` using
   `argparse`.

4. **Phase 6 — LLM Integration**
   Connect `ask` to the OpenAI API, with evidence-only prompting so the LLM
   never answers from anything but the snapshot it's given.

5. **Phase 7 — Robustness**
   Timeouts, partial-failure handling, secret redaction, large-log
   handling, missing-systemd handling, firewall-implementation variance,
   and permission-error handling.

6. **Phase 8 — Testing**
   Unit and integration tests, end-to-end validation, and demo preparation.

7. **Post-v1 Future Directions** *(not yet scheduled into a phase)*
   - Remote host support (currently single, local server only)
   - Historical snapshot comparison / trend detection
   - Scheduled scans (via cron or systemd timers) with alerting
   - Support for multiple LLM providers
   - A simple web UI for browsing reports

---

## Eventually Completed

- **Phase 1 — Project Architecture**: repository structure and full
  documentation set (`README.md`, `CONTEXT.md`, `PROJECT_RULES.md`,
  `LOGS.md`, `CHECKLIST.md`, `DECISIONS.md`, `ROADMAP.md`,
  `LEARNING_NOTES.md`) established; git repository initialized with a
  clean history. See `LOGS.md` entries dated 2026-07-14 for the full
  record.
- **Phase 3.1 — Core Execution Infrastructure**: `nodeiq.core.runner`,
  `nodeiq.core.result`, `nodeiq.core.exceptions`, and a documented
  `nodeiq.core.coordinator` placeholder built and tested; `pytest`
  introduced. See `LOGS.md`, "Phase 3.1: Core Execution Infrastructure."
- **Phase 3.2A — Collector Design Pattern**: the standard `collect()`
  contract, lifecycle, and testing expectations documented in
  `docs/collector_guidelines.md`; ADR-012 and ADR-013 recorded. See
  `LOGS.md` for this entry's full record.
- **Phase 3.2B — Collector Infrastructure Refinement**: `collect()`'s
  return contract refined from a `(data, errors)` tuple to
  `CollectorContext`/`CollectorResult` dataclasses in
  `nodeiq.core.collector`; ADR-014 recorded. See `LOGS.md` for this
  entry's full record.
- **Phase 3.2C / 3.3 — System and CPU + Memory Collectors**: the first two
  real Linux collectors built and verified on the Multipass VM. See
  `docs/system_collector.md` and `docs/cpu_memory_collector.md`.
- **Phase 3.4 — Coordinator MVP**: `run_scan()` implemented for real,
  replacing the Phase 3.1 placeholder — builds a `CollectorContext`, runs
  the registered collectors, aggregates `collection_errors`, builds
  `metadata`, and assembles an in-memory snapshot, verified end to end on
  the Multipass VM; `resource.py` renamed to `cpu_memory.py`. See
  `LOGS.md`, "Phase 3.4: Coordinator MVP."
- **Phase 3.5A — Process Collector Design**: designed (not implemented)
  the Process Collector — `/proc/<pid>` structure, a proposed v1 schema,
  process states, and a summarization strategy, plus a review of the
  existing `processes` schema section. See `docs/process_collector_design.md`
  and `LOGS.md`, "Phase 3.5A: Process Collector Design."
- **Phase 3.5B — Process Collector Implementation**: built and verified
  `collectors/processes.py` from the Phase 3.5A design — `process_count`,
  `zombie_count`, `blocked_process_count`, and `top_by_memory`, reading
  only `/proc/<pid>/status`/`cmdline`/`comm`, registered with the
  coordinator, verified end to end on the Multipass VM. See
  `docs/process_collector.md` and `LOGS.md`, "Phase 3.5B: Process
  Collector Implementation."
