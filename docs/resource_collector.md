# Resource Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/resource.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the second
real Linux collector, following `system.py`'s
`CollectorContext` → `collect()` → `CollectorResult` pattern
(`docs/system_collector.md`) — but needs **no commands at all**: every
field comes from reading `/proc/meminfo` and `/proc/loadavg` directly.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `cpu_memory`
section schema, which this v1 collector deliberately diverges from — see
"A Note on Naming and Schema Alignment" below).

---

## Responsibilities

The Resource Collector answers "how loaded is this machine right now?" —
directly supporting two of NodeIQ's headline example questions: "what is
consuming memory?" and "is this system under load?" v1 gathers exactly
eight facts, from two independent sources:

**From `/proc/meminfo`:**
- `memory_used_bytes`, `memory_available_bytes`, `memory_usage_percent`
- `swap_used_bytes`, `swap_usage_percent`

**From `/proc/loadavg`:**
- `load_average_1m`, `load_average_5m`, `load_average_15m`

Nothing else — CPU utilization *percentages* are explicitly **not**
collected in v1 (see "Fields Not Yet Collected" below). Memory and load
average are two independent data sources: if one file can't be read or
parsed, its fields come back `None` with an error recorded, but the other
source is still collected in full (see PROJECT_RULES.md Section 7).

---

## Why `/proc/meminfo` Was Chosen Instead of `free`

Compare:

```
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           951Mi       189Mi       561Mi       1.1Mi       279Mi       762Mi
Swap:             0B          0B          0B

$ cat /proc/meminfo
MemTotal:         974844 kB
MemFree:          572636 kB
MemAvailable:     706648 kB
...
```

`free`'s output is a table formatted for a human to read at a glance —
column widths, human-friendly units (`Mi`, `Gi`) that round for
readability, and a layout that has had minor variations across different
`procps` versions and distributions. Extracting one exact number means
parsing a table whose column alignment and unit suffixes aren't
guaranteed to be identical everywhere.

`/proc/meminfo` is the kernel's own source of truth — `free` itself reads
this same file and does the formatting `free` displays. Reading it
directly means NodeIQ gets exact byte-precise values (via kB, a stable
unit that never changes based on how "pretty" the number would look) with
no intermediate formatting or rounding to undo. This is the same reasoning
already applied to `system.py`'s `/etc/os-release` and `/proc/uptime`
choices (`docs/system_collector.md`) and stated as a standing rule in
`PROJECT_RULES.md` Section 9 (item 7).

## Why `/proc/loadavg` Was Chosen Instead of `uptime`

Compare:

```
$ uptime
 04:52:54 up 7 min,  2 users,  load average: 0.08, 0.05, 0.01

$ cat /proc/loadavg
0.56 0.12 0.04 4/138 1069
```

`uptime`'s output bundles the current wall-clock time, how long the
system has been up, logged-in user count, and the three load averages
into one human-oriented sentence. Getting just the three load numbers out
means parsing text after the literal words `"load average:"`, which is
exactly the kind of fragile, wording-dependent parsing NodeIQ avoids
whenever a machine-readable alternative exists (see
`docs/system_collector.md`'s "Why Machine-Readable Files Are Preferred").

`/proc/loadavg` is that machine-readable alternative: five
space-separated fields, always in the same order, with a format the
kernel has kept stable for decades. The first three are exactly the load
averages this collector needs; the last two (currently-running vs. total
process count, and the most recently created PID) aren't collected in v1.

---

## Explanation of Each Collected Field

| Field | Meaning |
|---|---|
| `memory_used_bytes` | Memory actually in use, computed as `MemTotal - MemAvailable` (in kB from `/proc/meminfo`, converted to bytes). |
| `memory_available_bytes` | Memory that could be made available to a new process without swapping, taken directly from `/proc/meminfo`'s `MemAvailable` (converted to bytes) — see "Why Available Memory Is Often More Useful Than Free Memory" in `LEARNING_NOTES.md`. |
| `memory_usage_percent` | `memory_used_bytes` as a percentage of total memory, rounded to two decimal places. |
| `swap_used_bytes` | Swap space actually in use, computed as `SwapTotal - SwapFree` (converted to bytes). `0` on a machine with no swap configured at all. |
| `swap_usage_percent` | `swap_used_bytes` as a percentage of total swap space. `0.0` (not an error) when `SwapTotal` is `0` — see `_percent`'s division-by-zero guard in `resource.py`. |
| `load_average_1m` / `_5m` / `_15m` | The system's load average over the last 1, 5, and 15 minutes, taken directly from `/proc/loadavg` — see "What Load Average Actually Means" in `LEARNING_NOTES.md`. |

---

## Fields Not Yet Collected

- **CPU utilization percentages** (e.g. "this machine's CPU is 40% busy
  right now") are explicitly out of scope for this task. Unlike memory,
  computing a CPU percentage from `/proc/stat` requires taking two
  readings a short interval apart and computing the *difference* between
  them (CPU time is cumulative, not a point-in-time snapshot like memory)
  — a meaningfully different collection strategy from everything else
  this collector does, deferred to a future increment.
- **Process/thread counts and per-core load** (`/proc/loadavg`'s fourth
  field, `running/total`) are read but not collected — only the three load
  averages are, per this task's scope.

## A Note on Naming and Schema Alignment

`docs/snapshot_schema.md` Section 4 already defines a `cpu_memory` section
(owned by a collector module it calls `collectors/cpu_memory.py`) with a
different shape than this collector produces:

```json
{
  "cpu": { "core_count": 0, "load_average_1m": 0.0, "load_average_5m": 0.0, "load_average_15m": 0.0 },
  "memory": { "total_kb": 0, "used_kb": 0, "free_kb": 0, "available_kb": 0 },
  "swap": { "total_kb": 0, "used_kb": 0, "free_kb": 0 }
}
```

This task explicitly named the module `resource.py` and specified flat,
byte-denominated field names (`memory_used_bytes`, not a nested
`memory.used_kb`). Rather than silently reconciling one against the
other, this is recorded here as a **known, deliberate divergence** — the
same treatment given to `system.py`'s `operating_system` field in
`docs/system_collector.md`:

- **Module name:** `resource.py`, not `cpu_memory.py`. `collector_name`
  in the returned `CollectorResult` is `"resource"` to match.
- **Field naming and units:** flat `snake_case` fields in bytes
  (`memory_used_bytes`) rather than a nested `memory: {used_kb: ...}`
  structure in kilobytes.
- **`core_count` is not collected.**

This tension is tracked in `LOGS.md` and `CHECKLIST.md` as a follow-up —
either `docs/snapshot_schema.md` Section 4 should be updated to match what
was actually built, or a future task should reconcile `resource.py`'s
output to the original `cpu_memory` shape. Not resolved silently either
way.

---

## Testing

- **Unit tests** (`tests/collectors/test_resource.py`, 17 tests): every
  `_parse_*`/`_compute_*` function tested with literal sample text/dicts
  (no I/O at all, including the `SwapTotal == 0` division-by-zero edge
  case observed for real on the Multipass VM); file-based getters tested
  via monkeypatched module-level path constants and `tmp_path`;
  `collect()` tested end-to-end for "everything succeeds," "memory source
  fails, load average doesn't," and "load average fails, memory doesn't."
- **Integration test** (`tests/collectors/test_resource_integration.py`, 1
  test): calls the real `collect()` with no mocking at all, automatically
  skipped unless running on Linux. Verified by copying the code to the
  Multipass Ubuntu 24.04 VM (`main-cattle`), installing `pytest` there, and
  running the full suite — all 48 tests passed, including this one
  running for real.

---

## Collector Review Checklist

A short, reusable checklist — for this collector, and as a starting point
for reviewing every collector built after it:

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — every anticipated failure is caught and turned into an error entry, per data source.
- [x] Each independent data source (`/proc/meminfo`, `/proc/loadavg`) fails on its own without blocking the other.
- [x] No `subprocess`/`run_command` calls where a `/proc` file already provides the same information (this collector uses zero commands).
- [x] Parsing is separated from file I/O: `_parse_meminfo`/`_parse_loadavg` are pure functions, tested with literal sample text, never touching a real file.
- [x] Computation is separated from parsing: `_compute_memory_fields` and `_percent` are pure functions operating on already-parsed values, not on raw text.
- [x] Division-by-zero and other realistic edge cases (`SwapTotal == 0`) are handled explicitly, not left to crash or silently produce `NaN`.
- [x] No duplicated logic left unsimplified *within* this collector — `_get_memory_fields` and `_get_load_average_fields` originally repeated an identical "read a `/proc` file, wrap `OSError` as `ValueError`" block; both now call a shared private `_read_proc_file` helper, mirroring how `system.py`'s three command-based getters already share `_run_and_capture`.
- [x] Duplication *across collectors* (`_error_entry`, and the same "read file, wrap as ValueError" shape now in both `system.py` and `resource.py`) is real but deliberately **not** extracted into `nodeiq.core` yet — `DECISIONS.md` ADR-012 sets a threshold of "three or more collectors" showing the same duplication before extracting a shared helper from evidence rather than speculatively. Noted here so it isn't missed when the third collector is built.
- [x] Field names use `snake_case`; no collector-invented redaction, logging, retries, or presentation logic.
- [x] Unit tests cover parsing, computation, error handling, and `collect()` end-to-end; an integration test verifies real behavior on the Multipass VM.
- [ ] *(Deferred, not yet reconciled)* Field names and structure fully match `docs/snapshot_schema.md`'s original `cpu_memory` section — see "A Note on Naming and Schema Alignment" above.
