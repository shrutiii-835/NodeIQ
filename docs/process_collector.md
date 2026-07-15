# Process Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/processes.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the third
real Linux collector, following `system.py` and `cpu_memory.py`'s
`CollectorContext` → `collect()` → `CollectorResult` pattern
(`docs/system_collector.md`, `docs/cpu_memory_collector.md`) — like
`cpu_memory.py`, it needs **no commands at all**: every field comes from
reading `/proc/<pid>/status`, `/proc/<pid>/cmdline`, and
`/proc/<pid>/comm` directly. `ps` is never invoked.

This is the first task to implement a *design* from an earlier,
dedicated design phase — see [process_collector_design.md](process_collector_design.md)
(Phase 3.5A) for the full rationale behind every choice below, including
six Open Design Questions this implementation deliberately did not
resolve (see "What This Implementation Narrows or Defers" below).

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `processes`
section, Section 5, which this implementation's field shape still
diverges from — see "A Note on Naming and Schema Alignment" below).

---

## Responsibilities

The Process Collector answers "what is consuming memory?" and "is
anything stuck?" at the process level — directly supporting NodeIQ's
headline example question about memory, plus giving early evidence
toward CPU-related questions once per-process CPU is eventually added.
v1 gathers a **summary**, not a full per-process dump:

- `process_count` — how many processes are currently running.
- `zombie_count` — how many are in the `Z` (zombie) state.
- `blocked_process_count` — how many are in the `D` (uninterruptible
  sleep) state.
- `top_by_memory` — the top 10 processes by RSS memory, each with `pid`,
  `process_name`, `memory_rss_bytes`, `owner`, `state`, and `command`.

Every process on the system is read once per scan to compute these
counts and rankings, but only the top 10 (plus the three counts) are
ever returned — see docs/process_collector_design.md Section 8,
"Recommended Process Summarization Strategy," for why sending every
process's full data to the LLM would be both wasteful and unhelpful.

---

## Why `/proc` Was Used (Not `ps`)

Compare:

```
$ ps aux | head -3
USER   PID %CPU %MEM   VSZ   RSS TTY STAT START TIME COMMAND
root     1  0.0  1.2 22092 12400 ?   Ss   04:45  0:00 /sbin/init
root     2  0.0  0.0     0     0 ?   S    04:45  0:00 [kthreadd]

$ cat /proc/1/status | head -5
Name:   systemd
State:  S (sleeping)
Pid:    1
PPid:   0
Uid:    0    0    0    0
```

`ps`'s output is a human-oriented table — column widths, truncated
command names, and formatting choices that can vary slightly by
`procps` version. Extracting `pid`/`state`/RSS/owner/command from it
means parsing aligned text columns, hoping a command name with unusual
characters doesn't shift the parse. `/proc/<pid>/status` and
`/proc/<pid>/cmdline` are the kernel's own machine-readable interfaces —
`ps` itself reads these same files internally and does the formatting
`ps` displays. Reading them directly avoids an intermediate formatting
layer with no benefit to a program that never needs the human-friendly
version. This is the same reasoning already applied to `system.py`'s
`/etc/os-release`/`/proc/uptime` choices and `cpu_memory.py`'s
`/proc/meminfo`/`/proc/loadavg` choices, and is a standing rule in
`PROJECT_RULES.md` Section 9 (item 7).

## Why `stat` Was Intentionally Deferred

`/proc/<pid>/stat` reports much of the same core information as
`status` (state, PPid), plus CPU-time counters (`utime`, `stime`) in one
dense, positional, space-separated line — but two things make it a worse
starting point than `status` for v1:

1. **Positional parsing is fragile in a way `status` isn't.** `status`
   names every field (`State:`, `VmRSS:`, `Uid:`), so a parser reads a
   specific line by its label. `stat`'s fields are only distinguished by
   their position in the line — the process name (field 2) is
   parenthesized specifically because it can itself contain spaces or
   even close-parens, making correct positional parsing genuinely
   trickier than reading a named field.
2. **`stat`'s main additional value — CPU time — isn't usable yet.**
   `utime`/`stime` are cumulative counters, not a point-in-time
   percentage. Computing "this process is using N% CPU" requires taking
   two readings a short interval apart and computing the difference —
   the exact same strategy `cpu_memory.py` already deferred for
   system-wide CPU utilization (see `docs/cpu_memory_collector.md`,
   "Fields Not Yet Collected"). Parsing `stat` now, without that
   two-reading machinery, would add parsing complexity for numbers this
   collector can't yet turn into anything useful.

Everything this v1 Process Collector actually needs (`state`, RSS
memory, owner, name, command) is available from `status`, `comm`, and
`cmdline` alone — so `stat` is left for whenever per-process CPU
utilization is actually implemented, consistent with
`docs/process_collector_design.md`'s own recommendation to defer
per-process CPU alongside `cpu_memory.py`'s deferred system-wide CPU.

---

## Race Conditions When Scanning Processes

Every previous collector reads a small, fixed set of files the kernel
guarantees are always present (`/proc/uptime`, `/proc/meminfo`,
`/proc/loadavg`). The Process Collector is structurally different: it
first **discovers** a dynamic, changing set of PIDs (`_discover_pids`,
by listing `/proc`'s numbered directories), then reads each one's files
separately. A process can legitimately exit at any point between those
two steps — its `/proc/<pid>/` directory simply disappears.

This is handled explicitly at exactly the boundary where it happens,
`_read_process`:

```python
try:
    status_text = (pid_dir / "status").read_text()
    comm_text = (pid_dir / "comm").read_text()
    cmdline_text = (pid_dir / "cmdline").read_text()
except OSError:
    return None
```

A disappearing process raises `FileNotFoundError` (a subclass of
`OSError`) on whichever file read happens to run after the process has
already exited. `_read_process` catches this and returns `None`; `collect()`
simply skips any `None` result and continues to the next PID. **This is
never recorded as a `collection_errors` entry** — per this task's
explicit instruction and the design in `docs/process_collector_design.md`
Section 5, a process exiting mid-scan is an expected, routine event for
one process, not evidence that the whole `processes` section failed to
collect. Contrast this with `_discover_pids` failing entirely (e.g.
`/proc` doesn't exist at all, as on macOS) — that *is* a real,
collector-wide failure (nothing about any process could be determined),
and is the one case that does produce a `collection_errors` entry, with
every summary field set to `None`.

A parse failure on a process that *hasn't* disappeared (e.g. a
malformed `status` file missing `State:` or `Uid:`) is handled the same
way — `_read_process` returns `None` and the PID is skipped — since this
project's "no unnecessary abstractions" quality bar doesn't call for a
separate per-process error-tracking mechanism the design/task never
asked for; the counts and top-10 list are still correct for every
process that *could* be read.

---

## Field-by-Field Explanation

| Field | Source | Notes |
|---|---|---|
| `pid` | The `/proc/<pid>` directory name itself | Always present by construction — it's how the process was found. |
| `process_name` | `/proc/<pid>/comm`, stripped | Matches the task's explicit file list; the kernel truncates this to 15 characters for long process names. |
| `memory_rss_bytes` | `/proc/<pid>/status`'s `VmRSS:` line, kB → bytes | Defaults to `0` (not an error) when absent — kernel threads (e.g. `kthreadd`) have no memory address space and no `VmRSS` line at all. |
| `owner` | `/proc/<pid>/status`'s `Uid:` line (first value = real UID), resolved via `pwd.getpwuid` | Falls back to the numeric UID as a string if no username can be resolved (e.g. no local mapping for an LDAP-backed UID) — a raw UID is still useful evidence. |
| `state` | `/proc/<pid>/status`'s `State:` line, single-letter code | See `docs/process_collector_design.md` Section 7 for what each code means operationally. |
| `command` | `/proc/<pid>/cmdline`, NUL-separated arguments joined with spaces | Empty string for kernel threads, which legitimately have no command line — not treated as an error. |

`process_count`, `zombie_count`, and `blocked_process_count` are computed
in `_summarize` from the full (in-memory only, never returned in full)
list of successfully-read processes for this scan.

---

## A Note on Naming and Schema Alignment

`docs/snapshot_schema.md` Section 5 defines a `processes` section with a
narrower shape than this implementation produces:

```json
{
  "process_count": 0,
  "top_by_memory": [
    {"pid": 0, "name": "<string>", "memory_percent": 0.0, "memory_kb": 0}
  ],
  "top_by_cpu": [
    {"pid": 0, "name": "<string>", "cpu_percent": 0.0}
  ]
}
```

Consistent with this project's established practice (the same treatment
given to `system.py` and `cpu_memory.py`'s own schema divergences), the
differences are recorded here explicitly rather than silently
reconciled:

- **`zombie_count`/`blocked_process_count` are new** — not in the
  original schema at all. This was flagged as a real, worth-fixing gap
  during Phase 3.5A's design review (`docs/process_collector_design.md`
  Section 9) and is now implemented as recommended there.
- **`name` (existing) vs. `process_name` (this implementation)** and
  **`memory_kb` (existing) vs. `memory_rss_bytes` (this implementation)**
  — same field-naming and unit-convention tension already open for
  `cpu_memory.py` (bytes vs. kB). Not reconciled here either; still an
  open, tracked question across both collectors.
- **`memory_percent` and `top_by_cpu` are not implemented.**
  `memory_percent` would require this collector to depend on
  `cpu_memory`'s `MemTotal` — a cross-collector dependency this project's
  principles avoid (`docs/data_model_design.md`, "Why Collectors Should
  Not Depend on Each Other"); `docs/process_collector_design.md` Section
  9 recommended computing it in a future report generator instead, which
  remains the recommendation. `top_by_cpu` requires per-process CPU
  percentages, deferred alongside `stat` parsing (see above).
- **No `command`/`owner` fields in the original schema's `top_by_memory`
  entries.** This implementation includes both, per this task's explicit
  field list — a superset of the original schema's per-entry shape, not
  a conflict with it.

None of this is resolved by editing `docs/snapshot_schema.md` itself —
consistent with how `system.py` and `cpu_memory.py` left their own
schema-alignment questions open, tracked here and in `CHECKLIST.md`/`LOGS.md`
rather than silently changed either direction.

---

## Testing

- **Unit tests** (`tests/collectors/test_processes.py`, 24 tests): every
  `_parse_*` function tested with literal sample text (including the
  kernel-thread edge case — missing `VmRSS`, empty `cmdline`); `_discover_pids`
  and `_read_process` tested via a monkeypatched `_PROC_ROOT` pointing at
  `tmp_path`, including a PID directory that doesn't exist at all
  (simulating a disappeared process) and a malformed `status` file;
  `_resolve_owner` tested with both a successful and a failing
  `pwd.getpwuid`; `_summarize` tested for zombie/blocked counts and
  top-10 sorting/capping with more than 10 processes; `collect()` tested
  end-to-end for the happy path, a disappearing process being skipped
  without an error, and total `/proc`-listing failure producing exactly
  one error entry with every field `None`.
- **Integration test** (`tests/collectors/test_processes_integration.py`,
  1 test): calls the real `collect()` with nothing mocked, automatically
  skipped unless running on Linux. Verified by copying the code to the
  Multipass Ubuntu 24.04 VM (`main-cattle`), installing dependencies
  there, and running the full suite — all 88 tests passed, including
  this one and the coordinator's end-to-end integration test (now
  covering all three collectors), producing a genuine sample snapshot
  with 91 real processes, a correctly-sorted top 10, and correct owner
  resolution (`root`, `ubuntu`, `systemd-resolve`) for real UIDs.

---

## Collector Review Checklist

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — the one collector-wide failure mode (`/proc` can't be listed at all) is caught and turned into an error entry; every other anticipated failure (a single process disappearing or being malformed) is handled per-PID.
- [x] No `subprocess`/`run_command` calls at all — `ps` is never invoked; every field comes from direct file I/O.
- [x] Parsing is separated from file I/O: `_parse_state`, `_parse_vmrss`, `_parse_uid`, `_parse_status`, and `_parse_cmdline` are pure functions, tested with literal sample text, never touching a real file.
- [x] A process disappearing mid-scan is handled explicitly and gracefully (`_read_process` returns `None`, `collect()` skips it) — never recorded as a `collection_errors` entry, per this task's explicit instruction.
- [x] Kernel-thread edge cases (`VmRSS` absent, `cmdline` empty) degrade gracefully to `0`/`""` rather than raising.
- [x] `owner` resolution degrades gracefully to the raw UID string when no username can be resolved.
- [x] No unnecessary intermediate data is kept — only the six fields needed for the summary are read per process; no `maps`, `environ`, `fd`, `mem`, `io`, or `task/` data is ever touched (see `docs/process_collector_design.md` Section 4).
- [x] Sends only a summary onward (`process_count`, `zombie_count`, `blocked_process_count`, top 10 by memory) — never every process's data, per `docs/process_collector_design.md` Section 8.
- [x] Field names use `snake_case`; no collector-invented redaction, logging, retries, or presentation logic.
- [x] Unit tests cover parsing, discovery, per-process reading (including disappearance and malformed data), summarization, and `collect()` end-to-end; an integration test verifies real behavior on the Multipass VM.
- [ ] *(Deferred, not yet reconciled)* Field names/units and `memory_percent`/`top_by_cpu` fully match `docs/snapshot_schema.md`'s original `processes` section — see "A Note on Naming and Schema Alignment" above.
- [ ] *(Deferred, per design)* `/proc/<pid>/stat` and per-process CPU utilization — see "Why `stat` Was Intentionally Deferred" above.
