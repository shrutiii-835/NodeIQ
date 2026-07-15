# ROADMAP.md — NodeIQ High-Level Roadmap

This file tracks NodeIQ's milestones at a high level. For the detailed,
checkbox-level task breakdown, see [CHECKLIST.md](CHECKLIST.md). For *why*
each milestone is ordered this way, see [CONTEXT.md](CONTEXT.md) Section 8.

---

## Current Milestone

**Phase 3.5A — Process Collector Design**

A design-only phase (no code): studied how Linux exposes process
information through `/proc/<pid>`, proposed a v1 process schema
(`pid`, `process_name`, `command`, `state`, `memory_rss_bytes`, `owner`,
`start_time`, `threads`), documented the five Linux process states
(`R`/`S`/`D`/`T`/`Z`) and their operational significance, recommended a
summarize-don't-dump strategy for feeding process data to the LLM, and
reviewed `docs/snapshot_schema.md` Section 5's existing `processes`
schema against this new design (see `docs/process_collector_design.md`
for the full write-up, including open design questions still unresolved).
The Process Collector itself is not implemented yet.

---

## Upcoming Milestone

**Phase 3.2C continued — Implement the Processes Collector**

Implement `collectors/processes.py` following
`docs/process_collector_design.md`'s plan, then continue with the
remaining collectors (disk + inodes, services, logs, network, scheduled
jobs, permissions) — registering each one with the coordinator
(`docs/coordinator.md`) as it's built, so `run_scan()`'s snapshot grows
one section at a time.

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
