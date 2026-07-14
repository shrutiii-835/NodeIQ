# CHECKLIST.md — NodeIQ Progress Tracker

This is the permanent, living progress tracker for NodeIQ, organized by the
implementation phases defined in [CONTEXT.md](CONTEXT.md) Section 8. Update
this file whenever a task is completed — check off the task and, if needed,
add newly-discovered sub-tasks. Do not remove future/unchecked tasks; they
stay listed (unchecked) until their phase is actually worked on.

---

## Progress Summary

- **Current Phase:** Phase 2 — Data Model (schema designed; code representation decision still open)
- **Next Phase:** Phase 3 — Collectors
- **Overall Progress:** 24 / 59 tasks complete (~41%)
- **Completed Tasks:** 24 (all of Phase 1, 13 of 14 in Phase 2)
- **Remaining Tasks:** 35 (1 in Phase 2, all of Phases 3–8)

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

- [ ] System metadata collector (hostname, OS version, kernel, uptime)
- [ ] CPU collector
- [ ] Memory collector
- [ ] Processes collector
- [ ] Disk collector
- [ ] Inodes collector
- [ ] Services collector
- [ ] Logs collector
- [ ] Network collector
- [ ] Scheduled jobs collector (cron + systemd timers)
- [ ] Permissions collector
- [ ] Scan coordinator that runs all collectors independently and assembles one snapshot

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
