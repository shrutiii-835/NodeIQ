# CONTEXT.md — NodeIQ Project Context

This document is the **permanent, authoritative source of truth** for what
NodeIQ is and why it is built the way it is. If any future instruction,
conversation, or plan seems to contradict this document, this document wins
— unless the project owner explicitly updates it.

This file is written for continuity across many development sessions. Read
it fully before making architectural decisions.

---

## 1. Project Objective

NodeIQ is a Python CLI application that runs on a single Linux server and
answers natural-language operational questions using **real system data**.

Example questions it must be able to answer:

- "What service failed?"
- "What is consuming memory?"
- "What ports are open?"
- "What cron jobs exist?"
- "Why might disk space be running out?"

The tool exists to save the mental overhead of manually running and
correlating many Linux diagnostic commands.

---

## 2. Architecture

NodeIQ has exactly two layers. This separation is fundamental and must not
be blurred.

### Layer 1 — Data Collection

Collects raw, factual information from the Linux system using native tools
and files, including but not limited to:

- `systemctl` (services)
- `journalctl` (logs)
- `ss`, `ip` (network)
- `df`, `du`, `findmnt` (disk and filesystems)
- `/proc` (CPU, memory, processes)
- `crontab`, systemd timers (scheduled jobs)
- `iptables` / `nftables` / `ufw` (firewall — implementation varies by system)
- filesystem metadata (permissions, ownership)

### Layer 2 — AI Interpretation

The LLM receives **only** the evidence collected in Layer 1, plus the user's
question. Three rules govern this layer absolutely:

1. The LLM interprets evidence. It does not gather it.
2. The LLM **never executes arbitrary shell commands.**
3. The LLM **never invents facts** that are not present in the snapshot.

### The Pipeline

```
scan    → collect Linux information → store structured JSON snapshot
report  → summarize an existing snapshot
ask     → load snapshot → send snapshot + question to LLM → answer from evidence only
```

---

## 3. Snapshot Philosophy (hard requirement)

**Snapshot-first architecture is non-negotiable.**

This means:

- A `scan` always produces a complete, self-contained JSON document (the
  "snapshot") describing the state of the system at that point in time.
- `report` and `ask` never talk to the live system directly — they only ever
  read a snapshot file.
- The LLM in `ask` never has the ability to run commands. It can only reason
  over the JSON it's given.

### Why snapshot-first?

- **Safety**: an LLM with live shell access on a production server is a
  security and reliability risk. A snapshot is a safe, inert artifact.
- **Reproducibility**: a snapshot can be saved, inspected, diffed, or shared
  without needing to reproduce the exact system state.
- **Determinism**: collection (Layer 1, deterministic Python/shell code) and
  interpretation (Layer 2, LLM reasoning) are cleanly separated, so bugs in
  one layer can't masquerade as bugs in the other.
- **Auditability**: because the snapshot is just JSON, you can always see
  exactly what evidence the LLM was given and check its answer against it.

---

## 4. Safety Philosophy

- The LLM is **never** given shell access, network access, or the ability to
  execute code.
- The LLM is **never** allowed to answer from general knowledge about "what
  Linux servers usually do" — only from the specific evidence in the
  snapshot for this specific machine.
- If evidence is missing or a collector failed, that fact must be visible in
  the snapshot's `collection_errors` field so the LLM (and the user) knows
  the answer may be incomplete — the LLM must say so rather than guessing.
- Secrets (passwords, tokens, keys) that might appear in logs or config
  files must be redacted by collectors before they ever reach a snapshot
  file or an LLM (see Phase 7 — Robustness).

---

## 5. Design Principles

- Small modules, single responsibility.
- Readable, simple code over clever code.
- Standard library first; minimal external dependencies.
- Every collector fails independently — one broken collector must never
  crash or block the rest of a scan.
- Type hints and docstrings throughout.
- JSON is the internal contract between layers — see Section 7.

---

## 6. Collector Architecture

A "collector" is a small, self-contained unit that gathers one category of
system information (e.g., "the disk collector" or "the services collector").

Rules for every collector:

- A collector must not raise an unhandled exception. Any failure it
  encounters must be caught and recorded, not allowed to crash the scan.
- A collector returns structured data (Python dict, later serialized to
  JSON) — never raw, unparsed command output as the final result.
- A collector's failure must be recorded separately from its data, in the
  snapshot's top-level `collection_errors` field, so that a failure never
  results in `null` being silently mistaken for "the system has nothing
  here."
- Collectors do not call each other. They are independent and orchestrated
  by a single "scan" coordinator.

Planned collectors (Phase 3), in implementation order:

1. System metadata (hostname, OS version, kernel, uptime)
2. CPU
3. Memory
4. Processes
5. Disk
6. Inodes
7. Services
8. Logs
9. Network
10. Scheduled Jobs
11. Permissions

---

## 7. JSON-First Design

JSON is the internal contract between Layer 1 (collection) and Layer 2
(interpretation). Every collector returns structured JSON — never free-form
text — so that:

- the LLM receives consistent, parseable evidence,
- snapshots can be validated, diffed, and tested,
- humans can read a snapshot directly without needing the LLM at all.

Every snapshot is expected to contain the following top-level fields:

```
{
  "timestamp": "...",
  "hostname": "...",
  "metadata": {...},
  "system": {...},
  "cpu_memory": {...},
  "processes": {...},
  "disk": {...},
  "services": {...},
  "logs": {...},
  "network": {...},
  "scheduled_jobs": {...},
  "permissions": {...},
  "collection_errors": {...}
}
```

The precise schema for each section is defined in Phase 2 (Data Model) and
documented in `docs/`. This section will be expanded as that work happens —
this file records the *philosophy*, not the exact schema.

---

## 8. Implementation Phases

We build incrementally and **never skip or reorder phases** without an
explicit decision from the project owner.

1. **Project architecture** — repository structure, documentation (current)
2. **Data model** — define the snapshot JSON schema
3. **Collectors** — system metadata, CPU, memory, processes, disk, inodes,
   services, logs, network, scheduled jobs, permissions
4. **Report generation** — human-readable summaries from a snapshot
5. **CLI** — `scan`, `report`, `ask` commands
6. **LLM integration** — wire `ask` to a real LLM, evidence-only prompting
7. **Robustness** — timeouts, partial failures, secret redaction, large
   logs, missing systemd, different firewall implementations, permission
   errors
8. **Testing** — validation and demo preparation

---

## 9. Future Roadmap

Beyond Phase 8, potential future directions (not committed, not scheduled):

- Remote host support (currently single, local server only)
- Historical snapshot comparison / trend detection
- Scheduled scans (via cron or systemd timers) with alerting
- Support for multiple LLM providers
- A simple web UI for browsing reports

---

## 10. How to Use This Document

- Read this file at the start of any new session before making
  architectural decisions.
- If the project owner gives an instruction that conflicts with this
  document, treat this document as authoritative and flag the conflict —
  unless the owner is explicitly updating the project's direction.
- Update this document only when the project's architecture or philosophy
  actually changes, not for routine implementation details (those belong in
  `LOGS.md` and `PROJECT_RULES.md`).
