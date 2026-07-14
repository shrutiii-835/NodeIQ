# ROADMAP.md — NodeIQ High-Level Roadmap

This file tracks NodeIQ's milestones at a high level. For the detailed,
checkbox-level task breakdown, see [CHECKLIST.md](CHECKLIST.md). For *why*
each milestone is ordered this way, see [CONTEXT.md](CONTEXT.md) Section 8.

---

## Current Milestone

**Phase 3.2B — Collector Infrastructure Refinement**

The `collect()` contract is refined from a `(data, errors)` tuple to two
small, named dataclasses in `nodeiq.core.collector`: `CollectorContext`
(scan-wide info passed into every collector — `scan_start_time`,
`default_timeout`) and `CollectorResult` (what every collector returns —
`collector_name`, `data`, `errors`, `duration_ms`, computed `success`).
`docs/collector_guidelines.md` and `docs/architecture.md` are updated to
match, and ADR-014 records why. No collector, CLI, or LLM code exists yet.

---

## Upcoming Milestone

**Phase 3.2C — Collectors (Implementation)**

Implement each Linux data collector independently on top of the Phase 3.1
infrastructure and the refined Phase 3.2A/3.2B contract: system metadata,
CPU + memory, processes, disk + inodes, services, logs, network, scheduled
jobs, permissions — plus the real scan coordinator that builds a
`CollectorContext`, runs them all, and assembles one snapshot from their
`CollectorResult`s, matching the schema designed in Phase 2.

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
