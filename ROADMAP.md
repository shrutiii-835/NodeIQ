# ROADMAP.md — NodeIQ High-Level Roadmap

This file tracks NodeIQ's milestones at a high level. For the detailed,
checkbox-level task breakdown, see [CHECKLIST.md](CHECKLIST.md). For *why*
each milestone is ordered this way, see [CONTEXT.md](CONTEXT.md) Section 8.

---

## Current Milestone

**Phase 1 — Project Architecture**

Establish the repository structure and the full documentation set
(`README.md`, `CONTEXT.md`, `PROJECT_RULES.md`, `LOGS.md`, `CHECKLIST.md`,
`DECISIONS.md`, `ROADMAP.md`, `LEARNING_NOTES.md`) before any application
code is written, and get the git repository initialized with a clean first
commit.

---

## Upcoming Milestone

**Phase 2 — Data Model**

Design the snapshot JSON schema: the top-level envelope plus every section
(`metadata`, `system`, `cpu_memory`, `processes`, `disk`, `services`,
`logs`, `network`, `scheduled_jobs`, `permissions`, `collection_errors`).
This schema becomes the contract every collector (Phase 3) writes to and
every consumer (`report`, `ask`) reads from.

---

## Long-Term Milestones

1. **Phase 3 — Collectors**
   Implement each Linux data collector independently: system metadata, CPU,
   memory, processes, disk, inodes, services, logs, network, scheduled
   jobs, permissions — plus the scan coordinator that runs them all and
   assembles one snapshot.

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

*(This section is intentionally empty. As each milestone above is finished
and verified, move a short summary of it here — do not delete history from
the sections above; this is a running record of what's actually shipped.)*
