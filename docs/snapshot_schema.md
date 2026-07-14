# Snapshot Schema — NodeIQ Data Model

**Status:** Design only. No collectors, CLI, or LLM integration exist yet.
This document defines the *shape* of the JSON a `scan` will eventually
produce — it does not run any Linux command or write any Python code.

**Schema version:** `1.0` (draft, first design pass)

This document is the detailed, field-level companion to
[CONTEXT.md](../CONTEXT.md) Section 7 (JSON-First Design), which already
established the philosophy and the fixed top-level key set. Read
[data_model_design.md](data_model_design.md) alongside this file for the
*why* behind these choices — this file is the *what*.

---

## 1. The Top-Level Envelope

Every snapshot is a single JSON object. Two fields sit at the top level for
quick access without digging into nested objects; everything else is
grouped into one object per concern:

```json
{
  "timestamp": "<ISO 8601 UTC timestamp — when this snapshot was taken>",
  "hostname": "<string — the machine's hostname, denormalized for convenience>",
  "metadata": { "...": "see Section 2" },
  "system": { "...": "see Section 3" },
  "cpu_memory": { "...": "see Section 4" },
  "processes": { "...": "see Section 5" },
  "disk": { "...": "see Section 6" },
  "services": { "...": "see Section 7" },
  "logs": { "...": "see Section 8" },
  "network": { "...": "see Section 9" },
  "scheduled_jobs": { "...": "see Section 10" },
  "permissions": { "...": "see Section 11" },
  "collection_errors": { "...": "see Section 12" }
}
```

**Why `timestamp` and `hostname` are duplicated at the top level:** the
`system` section (Section 3) also contains a hostname, and `metadata`
(Section 2) also contains scan timing detail. The top-level copies aren't a
second source of truth — they are a denormalized convenience so that a
human skimming a snapshot, a filename generator, or a one-line log message
never has to descend into nested JSON just to answer "when was this taken"
and "which machine is this." `system.hostname` remains the authoritative
value; the top-level `hostname` is always copied from it by the scan
coordinator.

**Mandatory:** every field in the envelope above is always present in a
valid snapshot — even sections whose *content* turned out to be empty (see
each section's own Mandatory/Optional note below).

---

## 2. `metadata`

**Purpose:** Describes facts about *the snapshot itself* — how and when it
was produced — as distinct from facts about the system being inspected.

**Description:** Think of `metadata` as the label on a jar, and every other
section as the jar's contents. `metadata` tells you which version of the
schema you're reading, which version of NodeIQ produced it, how long the
scan took, and which collectors actually ran. This is what lets `report`
and `ask` (and future consumers) know how much to trust a snapshot and how
to parse it correctly, even years from now if the schema has since changed.

**Collector responsible:** Not a collector — populated directly by the scan
coordinator (the function that runs every collector and assembles the final
JSON), since this data is *about* the scan process, not about the machine.

**Used by future report(s):**
- The header of every human-readable report (`report` command)
- `ask` — so the LLM can note if a snapshot is old or incomplete
- A future historical-comparison feature (comparing `metadata.timestamp`
  across snapshots)

**Mandatory or optional:** Mandatory. Always fully populated.

**Example placeholder structure:**

```json
{
  "schema_version": "1.0",
  "nodeiq_version": "<string — NodeIQ's own version>",
  "scan_started_at": "<ISO 8601 UTC timestamp>",
  "scan_finished_at": "<ISO 8601 UTC timestamp>",
  "scan_duration_seconds": 0.0,
  "collectors_run": ["<collector name>", "..."],
  "collectors_skipped": ["<collector name>", "..."]
}
```

---

## 3. `system`

**Purpose:** Static or slow-changing facts that identify the machine and
its operating system.

**Description:** This answers "what is this machine, and what is it
running" — the kind of information you'd want at the top of any diagnostic
report before looking at anything else.

**Collector responsible:** `collectors/system.py` (the "system metadata
collector" from CONTEXT.md Section 6).

**Used by future report(s):**
- Report header / system overview section
- `ask` — baseline context for almost every question

**Mandatory or optional:** Mandatory.

**Example placeholder structure:**

```json
{
  "hostname": "<string>",
  "os_name": "<string — e.g. Ubuntu>",
  "os_version": "<string — e.g. 24.04>",
  "kernel_version": "<string>",
  "architecture": "<string — e.g. x86_64>",
  "boot_time": "<ISO 8601 UTC timestamp>",
  "uptime_seconds": 0
}
```

---

## 4. `cpu_memory`

**Purpose:** Point-in-time resource utilization — how busy the CPU is and
how memory/swap are being used.

**Description:** Supports questions like "what is consuming memory?" and
"is this system under load?" CPU load and memory usage are read from two
different `/proc` files (`/proc/loadavg` and `/proc/meminfo`), but they
share one top-level key because they're both "point-in-time resource
usage" from the reader's perspective, and are almost always looked at
together.

**Collector responsible:** `collectors/cpu_memory.py` — one collector
module owns this whole section (see
[data_model_design.md](data_model_design.md) for why CPU and memory, though
conceptually distinct, are implemented as one collector with a single
entry point rather than two).

**Used by future report(s):**
- Resource usage report section
- `ask` — "what is consuming memory/CPU?", "is the system under load?"

**Mandatory or optional:** Mandatory.

**Example placeholder structure:**

```json
{
  "cpu": {
    "core_count": 0,
    "load_average_1m": 0.0,
    "load_average_5m": 0.0,
    "load_average_15m": 0.0
  },
  "memory": {
    "total_kb": 0,
    "used_kb": 0,
    "free_kb": 0,
    "available_kb": 0
  },
  "swap": {
    "total_kb": 0,
    "used_kb": 0,
    "free_kb": 0
  }
}
```

---

## 5. `processes`

**Purpose:** A snapshot of running processes, focused on what's consuming
the most resources.

**Description:** Rather than dumping every process on the system (which
could be hundreds of entries and isn't usually what someone asking "what's
consuming memory?" wants), this section is intentionally summarized to the
processes most likely to matter.

**Collector responsible:** `collectors/processes.py`.

**Used by future report(s):**
- "Resource hotspots" report section
- `ask` — "what is consuming memory?", "what is consuming CPU?"

**Mandatory or optional:** Mandatory.

**Example placeholder structure:**

```json
{
  "process_count": 0,
  "top_by_memory": [
    {
      "pid": 0,
      "name": "<string>",
      "memory_percent": 0.0,
      "memory_kb": 0
    }
  ],
  "top_by_cpu": [
    {
      "pid": 0,
      "name": "<string>",
      "cpu_percent": 0.0
    }
  ]
}
```

---

## 6. `disk`

**Purpose:** Filesystem space usage *and* inode usage for every mounted
filesystem.

**Description:** Supports "why might disk space be running out?" — one of
NodeIQ's headline example questions. Both space usage and inode usage come
from the same underlying tool (`df`, with and without the `-i` flag) and
describe the same mounted filesystems, so they are combined into one
section populated by one collector, rather than two. (CONTEXT.md Section 6
originally lists "Disk" and "Inodes" as two separate planned collectors —
see [data_model_design.md](data_model_design.md) for why this design
combines them under one owner.)

**Collector responsible:** `collectors/disk.py`.

**Used by future report(s):**
- Disk usage report section
- `ask` — "why might disk space be running out?"

**Mandatory or optional:** Mandatory.

**Example placeholder structure:**

```json
{
  "filesystems": [
    {
      "mount_point": "<string — e.g. />",
      "device": "<string — e.g. /dev/sda1>",
      "filesystem_type": "<string — e.g. ext4>",
      "size_kb": 0,
      "used_kb": 0,
      "available_kb": 0,
      "used_percent": 0.0,
      "inodes_total": 0,
      "inodes_used": 0,
      "inodes_used_percent": 0.0
    }
  ]
}
```

---

## 7. `services`

**Purpose:** The state of systemd-managed services, especially any that
have failed.

**Description:** Supports "what service failed?" — another headline
example question. Because not every Linux system has systemd (see
`DECISIONS.md` ADR-010), this section explicitly records whether systemd
was available at all, so "no systemd" (a fact) is never confused with "we
couldn't check" (a collection failure — see Section 12).

**Collector responsible:** `collectors/services.py`.

**Used by future report(s):**
- Service health report section
- `ask` — "what service failed?"

**Mandatory or optional:** Mandatory (with graceful degradation — see
`systemd_available` below).

**Example placeholder structure:**

```json
{
  "systemd_available": true,
  "total_count": 0,
  "running_count": 0,
  "failed_services": [
    {
      "name": "<string — e.g. nginx.service>",
      "description": "<string>",
      "load_state": "<string>",
      "active_state": "<string>",
      "sub_state": "<string>"
    }
  ]
}
```

---

## 8. `logs`

**Purpose:** Recent, filtered log entries — especially errors and
warnings — relevant to diagnosing a problem.

**Description:** Logs can be enormous, so this section is always a bounded,
filtered slice, never a full log dump (the exact size/lookback policy is a
Phase 7 — Robustness — decision; this schema only fixes the *shape*, not
the policy, and includes a `truncated` flag so consumers always know
whether they're seeing the complete picture).

**Collector responsible:** `collectors/logs.py`.

**Used by future report(s):**
- "Recent issues" report section
- `ask` — almost any "why did X happen?" question

**Mandatory or optional:** Mandatory (with graceful degradation if
`journalctl` is unavailable — see `source` below).

**Example placeholder structure:**

```json
{
  "source": "<string — e.g. journalctl, syslog_files, or unavailable>",
  "truncated": false,
  "recent_errors": [
    {
      "timestamp": "<ISO 8601 UTC timestamp>",
      "unit": "<string — e.g. nginx.service>",
      "message": "<string, redacted of secrets>"
    }
  ]
}
```

---

## 9. `network`

**Purpose:** Network interfaces and listening ports.

**Description:** Supports "what ports are open?" — another headline
example question — plus basic interface/connectivity context.

**Collector responsible:** `collectors/network.py`.

**Used by future report(s):**
- Network report section
- `ask` — "what ports are open?"

**Mandatory or optional:** Mandatory.

**Example placeholder structure:**

```json
{
  "interfaces": [
    {
      "name": "<string — e.g. eth0>",
      "addresses": ["<string — e.g. 192.0.2.10/24>"],
      "state": "<string — e.g. up>"
    }
  ],
  "listening_ports": [
    {
      "protocol": "<string — tcp or udp>",
      "local_address": "<string>",
      "port": 0,
      "pid": 0,
      "process_name": "<string>"
    }
  ]
}
```

---

## 10. `scheduled_jobs`

**Purpose:** Cron jobs and systemd timers configured on the system.

**Description:** Supports "what cron jobs exist?" — another headline
example question. Both cron and systemd timers are legitimate ways to
schedule work on Linux, so both are covered under this one section.

**Collector responsible:** `collectors/scheduled_jobs.py`.

**Used by future report(s):**
- Scheduled jobs report section
- `ask` — "what cron jobs exist?"

**Mandatory or optional:** Mandatory (with graceful degradation if crontab
or timer data can't be read — recorded via `collection_errors`, not by
omitting the section).

**Example placeholder structure:**

```json
{
  "cron_jobs": [
    {
      "user": "<string>",
      "schedule": "<string — e.g. '0 * * * *'>",
      "command": "<string>",
      "source_file": "<string>"
    }
  ],
  "systemd_timers": [
    {
      "name": "<string — e.g. logrotate.timer>",
      "next_run": "<ISO 8601 UTC timestamp, nullable>",
      "last_run": "<ISO 8601 UTC timestamp, nullable>",
      "unit": "<string — the .service unit it triggers>"
    }
  ]
}
```

---

## 11. `permissions`

**Purpose:** Ownership and permission facts for a small set of
security-sensitive paths.

**Description:** This is the least precisely scoped section in the current
design — "permissions and ownership" was named as a data source in the
original project spec, but *which* paths matter and *what* counts as
noteworthy (e.g., world-writable files, unexpected ownership) hasn't been
decided in detail yet. This document commits to a conservative placeholder
shape now and treats the exact scope as an open question for the
collector-implementation phase (Phase 3) — see the Design Review (Section
13) and the Open Questions list at the end of this document.

**Collector responsible:** `collectors/permissions.py`.

**Used by future report(s):**
- A future security/permissions report section
- `ask` — questions about unexpected file permissions or ownership

**Mandatory or optional:** **Optional.** Unlike every other section, an
empty or minimal `permissions` object is an acceptable, expected outcome
until its exact scope is decided — this is the one section where "we
haven't defined what to check yet" is a legitimate state, distinct from a
collection failure.

**Example placeholder structure:**

```json
{
  "checked_paths": [
    {
      "path": "<string>",
      "owner": "<string>",
      "group": "<string>",
      "mode": "<string — e.g. '644'>",
      "world_writable": false
    }
  ]
}
```

---

## 12. `collection_errors`

**Purpose:** Records every collector failure, separately from collected
data — the single most important safety mechanism in this schema (see
CONTEXT.md Section 4, Safety Philosophy, and PROJECT_RULES.md Section 7,
Error Handling Philosophy).

**Description:** A dict keyed by collector name (matching the top-level
section name it corresponds to, e.g. `"services"`, `"logs"`). Each entry
describes what went wrong in enough detail that a human — or the LLM in
`ask` — can tell "this section may be incomplete" rather than mistaking a
failure for "the system genuinely has none of this."

**Collector responsible:** Not a collector — populated by the scan
coordinator, which collects each collector's own reported errors (a
collector never writes directly into this dict itself; it returns its
errors to the coordinator, which assembles this section).

**Used by future report(s):**
- A "collection health" section at the end of every report, listing
  anything that couldn't be checked
- `ask` — required reading for the LLM before answering, so it can say
  "I don't have that information" instead of guessing

**Mandatory or optional:** Mandatory. Always present, even if empty (`{}`
means every collector succeeded).

**Example placeholder structure:**

```json
{
  "<collector name, e.g. services>": [
    {
      "message": "<human-readable description of what went wrong>",
      "severity": "<string — warning or error>",
      "exception_type": "<string, optional — e.g. PermissionError>"
    }
  ]
}
```

---

## 13. Design Review (Quality Check)

Before finishing this design, it was checked against the following
questions:

**Can future collectors extend this without breaking compatibility?**
Yes — every section is an object, not a bare array, so new fields can be
added to any section later without breaking existing consumers that only
read the fields they know about. `metadata.schema_version` exists
specifically so a breaking change (if one is ever truly necessary) can be
detected and handled explicitly rather than silently.

**Is every section independent?**
Yes, at the level that matters: no collector reads another collector's
output to do its job. Two sections (`cpu_memory` and `disk`) group data
that maps to more than one *informally listed* collector from CONTEXT.md
Section 6 (CPU + Memory; Disk + Inodes) — but each such section still has
exactly one *owning* collector module with one entry point in this design
(see Section 14 below). Independence is preserved; only the informal
collector count from CONTEXT.md's Section 6 list and the formal top-level
key count from its Section 7 don't map 1:1, and that mismatch is resolved
here.

**Is the schema understandable by a beginner?**
Every section in this document states its purpose in plain language before
showing any structure, and every example uses placeholder values with
inline type/example hints rather than unexplained real data.

**Does it separate collected data from collection errors?**
Yes — `collection_errors` (Section 12) is the only place failures are
recorded. No other section uses `null`, `false`, or an empty list to mean
"something went wrong" — those values only ever mean "the system genuinely
has none of this."

**Will this structure work equally well for reports and LLM prompts?**
Yes — the whole snapshot (or any subset of its sections) is valid,
self-describing JSON that can be printed directly as evidence to an LLM
prompt, or walked section-by-section to generate a human-readable report.
Flat, explicit field names (rather than deeply nested or abbreviated ones)
keep both use cases straightforward.

---

## 14. Resolving the Collector-Count vs. Envelope-Key Mismatch

CONTEXT.md Section 6 lists 11 planned collectors: System metadata, CPU,
Memory, Processes, Disk, Inodes, Services, Logs, Network, Scheduled Jobs,
Permissions. CONTEXT.md Section 7's JSON envelope has 10 non-error
top-level data keys. The difference is CPU+Memory sharing `cpu_memory`, and
Disk+Inodes sharing `disk`.

This document resolves that difference as follows, without changing
CONTEXT.md itself (see the Recommendations in the session output for why):

- **`cpu_memory`** is owned by one collector module
  (`collectors/cpu_memory.py`) with one entry point, internally reading two
  different `/proc` files. CPU and memory are conceptually distinct but
  operationally almost always viewed together, and neither depends on the
  other's output.
- **`disk`** is owned by one collector module (`collectors/disk.py`) with
  one entry point, since both space and inode usage come from the same
  underlying tool (`df`) and describe the same set of mounted filesystems.

In both cases, "one section, one owning collector, one entry point" is
preserved — the CONTEXT.md Section 6 list is better read as "the categories
of information NodeIQ collects" rather than "one Python module per line
item."

---

## Open Questions for Later Phases

- **`permissions` scope** (Section 11): exact list of "sensitive paths" and
  what counts as noteworthy is undecided — revisit when Phase 3 implements
  this collector.
- **`logs` bounding policy** (Section 8): exact max line count / lookback
  window for `journalctl` is a Phase 7 (Robustness) decision; the schema
  only guarantees a `truncated` flag exists.
- **Secret redaction** (mentioned in CONTEXT.md Section 4): which fields
  need redaction (most likely `logs.recent_errors[].message` and possibly
  `scheduled_jobs.cron_jobs[].command`) will be finalized during Phase 7.
- **Code representation** (dataclasses vs. `TypedDict` for these shapes in
  Python) is intentionally left undecided by this document — see
  `CHECKLIST.md` Phase 2 and the Recommended Next Task in this session's
  output.
