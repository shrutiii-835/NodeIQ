# Process Collector Design — NodeIQ

**Status:** Design only (Phase 3.5A). No code exists yet —
`src/nodeiq/collectors/processes.py` is not implemented, and the
coordinator's `_REGISTERED_COLLECTORS` list is not touched by this task.
This document exists so implementation (a future phase) starts from a
reviewed plan, per this project's "design before implementation"
convention (see `LEARNING_NOTES.md`, "Why does design come before
implementation?").

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `processes` section,
Section 5, which this design deliberately reopens — see "Reviewing the
Existing Schema" below).

---

## 1. How Linux Represents Processes

Every running program on Linux is called a **process**, and the kernel
identifies each one with a unique number: its **PID** (Process ID). PIDs
are assigned in increasing order as processes are created and get reused
over time once a process exits and enough numbers have cycled around.

Linux exposes live information about every process through `/proc` (the
same virtual filesystem already used by `system.py` for `/proc/uptime`
and by `cpu_memory.py` for `/proc/meminfo`/`/proc/loadavg` — see
`LEARNING_NOTES.md`, "What is `/proc`?"). The difference here is scale and
shape: `/proc/uptime` is one fixed file with one fixed meaning, but
process information is a **dynamic, per-process family of directories** —
one per currently-running PID, appearing and disappearing as processes
start and exit.

## 2. Why Every PID Has a Directory

For every running process, the kernel maintains a directory
`/proc/<pid>/` containing files that describe that specific process —
its name, its state, its memory usage, its command line, and much more.
This is the "everything is a file" philosophy taken to its logical
extreme: instead of a bespoke system call for "tell me about process
1234," Linux exposes an entire directory a program can `ls`, `cat`, and
`read` with completely ordinary file operations.

On the Multipass VM (`main-cattle`), `ls /proc/1` shows some of what a
process directory contains:

```
$ ls /proc/1
cgroup  cmdline  comm  cwd  environ  exe  fd  fdinfo  io  limits
maps  mem  mounts  oom_score  root  smaps  stack  stat  statm
status  task  wchan  ...
```

`/proc` also contains other, non-PID entries (`/proc/meminfo`,
`/proc/loadavg`, `/proc/cpuinfo`, and so on) — the numbered directories
are simply the subset that represents processes specifically. A directory
disappears the instant its process exits; there is no "stale" process
directory left behind to clean up.

## 3. Important Files Inside `/proc/<pid>`

A `/proc/<pid>` directory contains dozens of files and subdirectories.
The ones actually relevant to answering NodeIQ's operational questions
("what is consuming memory/CPU?", "what's running?", "is anything stuck?")
are a small subset:

| File | Contents | Format |
|---|---|---|
| `status` | Human-readable-but-structured key-value summary: name, state, PPid, UID/GID, memory (`VmRSS`), thread count (`Threads`) | One `Key:\tvalue` pair per line |
| `stat` | The same core facts (and more) in one dense, space-separated line, including the process state as a single character and CPU-time counters (`utime`, `stime`) | One line, space-separated fields, positional |
| `cmdline` | The full command line the process was launched with | NUL-separated arguments (no spaces) |
| `comm` | Just the process's short name (typically what a program calls itself, truncated to 15 characters by the kernel) | Single line |
| `io` | Bytes read/written by this process (`rchar`, `wchar`, ...) | `Key: value` lines |

Example, pulled from the real VM for a running `bash` shell (PID 2835):

```
$ cat /proc/2835/status
Name:   bash
State:  S (sleeping)
Pid:    2835
PPid:   2834
Uid:    1000    1000    1000    1000
VmRSS:      3120 kB
Threads:        1
...

$ cat /proc/2835/stat
2835 (bash) S 2834 2835 2835 0 -1 4194304 517 114 0 0 0 0 0 0 20 0 1 0 342435 ...

$ cat /proc/2835/cmdline | tr '\0' ' '
bash -c PID=$$; echo "=== status ===" ...

$ cat /proc/2835/comm
bash
```

Notice `status` and `stat` overlap heavily (both report state, PPid,
threads) — they're two views of largely the same underlying kernel data,
one meant to be skimmed by a human (`status`) and one meant to be parsed
positionally by a program (`stat`). NodeIQ v1 reads `status` for
`state`/`memory`/`threads` (named fields — no risk of miscounting
positional columns) and `stat` only if a field isn't available elsewhere
(see "Trade-offs" below for why `status` is generally preferred).

A real edge case worth noting, also observed on the VM: kernel threads
(e.g. `/proc/2/comm` → `kthreadd`) have **no `cmdline`** at all — the file
exists but reads as empty, since a kernel thread was never launched with
command-line arguments the way a user process is. Any parser must treat
an empty `cmdline` as a legitimate, common case, not a parsing failure.

## 4. Files NodeIQ Intentionally Ignores in v1

Deliberately out of scope, to keep the collector focused on operational
questions rather than becoming a general-purpose process inspector:

- **`maps` / `smaps` / `smaps_rollup`** — detailed per-region virtual
  memory maps (used by memory-profiling tools). Far more detail than
  "how much memory is this process using" needs; expensive to read for
  every process on a busy system.
- **`environ`** — the process's full environment variables. Reading this
  broadly risks capturing secrets (API keys, passwords in env vars) —
  directly conflicts with NodeIQ's future secret-redaction goal
  (`README.md`'s Robustness phase) if collected by default with no
  redaction plan in place yet.
- **`fd` / `fdinfo`** — open file descriptors. Useful for diagnosing "why
  won't this file unmount" style problems, but a different (and noisier)
  kind of question than NodeIQ v1 targets.
- **`mem`** — raw process memory access. Not a diagnostic file at all (a
  debugger-style interface); irrelevant and privileged.
- **`io`** — per-process disk I/O counters. Plausibly useful someday
  ("what's hammering disk?"), but out of scope for v1's focus on memory
  and CPU; noted as a future candidate, not built now.
- **`task/`** — per-thread breakdowns within a multi-threaded process.
  v1's `threads` field (a count) is enough; per-thread detail is a level
  of granularity NodeIQ doesn't need yet.
- **`cwd` / `root` / `exe`** (symlinks to the process's working directory,
  chroot, and executable path) — occasionally useful for debugging, but
  not something a natural-language operational question ("what's
  consuming memory") needs.

## 5. Trade-offs: `/proc` vs. Commands Like `ps`

| | Reading `/proc/<pid>/*` directly | Running `ps` |
|---|---|---|
| **Stability** | Kernel-guaranteed interface; format has been stable for decades | Output formatting can vary by `procps` version/distribution, especially column widths and header text |
| **Cost for "all processes"** | One `listdir("/proc")` plus a few small file reads per PID — no process is spawned to gather the data | Spawns an external process (`ps` itself) — for hundreds of processes, still just one exec, but internally `ps` is doing the exact same `/proc` reads NodeIQ would do directly |
| **Parsing** | Small, well-defined per-field format (`status`'s `Key:\tvalue`, `stat`'s positional fields) | Column-aligned human text; command names containing spaces or unusual characters can shift column parsing |
| **Consistency across processes** | Same file layout for every PID, including kernel threads and zombies | `ps` already handles these cases internally, but that logic is opaque to NodeIQ — it can't be selectively told "give me only the four fields I actually want in a program-friendly shape" without `--format`/`-o`, which itself is another text format to parse |
| **Race conditions** | A process can exit between `listdir("/proc")` and reading `/proc/<pid>/status` — must handle `FileNotFoundError` per-PID, not treat it as a scan-wide failure | `ps` has the same race internally, but only reports what it managed to see, and NodeIQ has no way to distinguish "process exited mid-`ps`-run" from "this process just doesn't have this field" |

This project's standing rule (`PROJECT_RULES.md` Section 9, item 7; already
applied in `system.py` and `cpu_memory.py`) is to prefer a stable kernel
file interface over parsing a command's formatted output whenever one
exists — `/proc/<pid>` is exactly such an interface, so the Process
Collector should use it directly rather than shelling out to `ps`.

The one trade-off worth being explicit about: the **process-exits-mid-scan
race** is a real, structural difference from every previous collector.
`system.py` and `cpu_memory.py` each read one fixed, always-present file.
The Process Collector must first *discover* the current, dynamic set of
PIDs, then read files that might vanish out from under it a moment later
— this must be treated as an expected, normal condition per PID (skip that
PID, don't record a scan-wide error), not a collector-level failure.

---

## 6. Proposed NodeIQ v1 Process Schema

Each entry in the process list would look like:

```json
{
  "pid": 2835,
  "process_name": "bash",
  "command": "bash -c ...",
  "state": "S",
  "memory_rss_bytes": 3194880,
  "owner": "shruti",
  "start_time": "2026-07-15T04:45:12+00:00",
  "threads": 1
}
```

| Field | Source | Why it's useful | Required / Optional |
|---|---|---|---|
| `pid` | `/proc/<pid>` directory name itself | The unique identifier every other fact attaches to; needed to answer "which process" in any follow-up question | **Required** — without it, an entry can't be meaningfully referenced at all |
| `process_name` | `/proc/<pid>/status`'s `Name:` line (equivalently `/proc/<pid>/comm`) | Human-recognizable label ("nginx", "postgres") — this is what a person actually asks about ("what's `nginx` doing?"), not a raw PID | **Required** — the schema's `top_by_memory`/`top_by_cpu` examples already assume a `name` is always present |
| `command` | `/proc/<pid>/cmdline` (NUL-separated, joined with spaces) | Distinguishes between multiple instances of the same program run with different arguments (e.g. two `python3` processes running different scripts) — `process_name` alone can't tell them apart | **Optional** — legitimately empty for kernel threads (see Section 3); must not be treated as a parsing failure when empty |
| `state` | `/proc/<pid>/status`'s `State:` line (single-letter code, e.g. `S`) | Directly answers "is anything stuck?" — a `D` (uninterruptible sleep) or `Z` (zombie) is exactly the kind of fact an operational question would ask about; see Section 7 | **Required** — cheap to read, always present, and the single most diagnostically useful field of everything considered here |
| `memory_rss_bytes` | `/proc/<pid>/status`'s `VmRSS:` line, converted from kB to bytes | Answers "what is consuming memory?" per-process — the same operational question `cpu_memory.py` answers system-wide, now attributed to individual processes | **Required** — this is the field the `top_by_memory` summary (Section 8) is built from |
| `owner` | The process's UID (`/proc/<pid>/status`'s `Uid:` line), resolved to a username | Tells you *who* is running something — relevant for a shared or multi-user server ("is this a root process or a user process?") | **Optional** — resolving a UID to a username requires reading `/etc/passwd` or calling a system lookup, which can itself fail (e.g. an LDAP-backed UID with no local mapping); falling back to the raw UID as a string is an acceptable degrade, not a hard requirement |
| `start_time` | `/proc/<pid>/stat`'s 22nd field (`starttime`, in clock ticks since boot), combined with system boot time | Lets a report answer "how long has this process been running?" — useful for spotting an unusually long-lived or unusually recently-restarted process | **Optional, deferred** — computing an absolute timestamp from `starttime` requires the system's boot time, which `system.py` does not currently collect (`boot_time` was explicitly deferred in `docs/system_collector.md`); recommend deferring `start_time` until `boot_time` exists, rather than duplicating boot-time detection logic inside this collector |
| `threads` | `/proc/<pid>/status`'s `Threads:` line | A large or rapidly growing thread count is a real operational signal for some services (a thread-per-connection server misbehaving under load) | **Optional** — genuinely useful, cheap to read, but not essential to the headline "what's consuming memory/CPU" questions; include if it doesn't complicate the schema |

**Recommendation:** treat `pid`, `process_name`, `state`, and
`memory_rss_bytes` as the required core (cheap, always available, and
directly answer NodeIQ's stated example questions); `command`, `owner`,
and `threads` as optional-but-included (real value, small marginal cost,
graceful to omit per-process on failure); and `start_time` as explicitly
deferred until `system.py` collects `boot_time` (avoids solving the same
sub-problem twice in two different collectors).

CPU usage per process is **not** in this schema. `/proc/<pid>/stat`'s CPU
time fields (`utime`/`stime`) are cumulative counters, exactly like
system-wide CPU time in `/proc/stat` — computing a *percentage* requires
two readings apart in time, the same reason `cpu_memory.py` deferred
system-wide CPU utilization (`docs/cpu_memory_collector.md`, "Fields Not
Yet Collected"). A per-process CPU percentage would need the same
two-reading strategy, multiplied across every process — a meaningfully
larger version of an already-deferred problem, so it's deferred here too
rather than solved inconsistently for one collector and not the other.

---

## 7. Linux Process States

`/proc/<pid>/status`'s `State:` line (and `/proc/<pid>/stat`'s third
field) reports one of a small set of single-letter codes:

| Code | Name | Meaning | Operational significance |
|---|---|---|---|
| **R** | Running (or runnable) | The process is either actively using the CPU right now, or ready to run and waiting only for its turn | Normal, healthy state for active work. Many `R` processes competing at once is what drives load average up (`LEARNING_NOTES.md`, "What does load average actually mean?"). |
| **S** | Sleeping (interruptible) | The process is idle, waiting for something (a timer, input, a network event) that can wake it up at any time | The overwhelmingly common state for a healthy, idle service waiting for work — e.g. a web server waiting for the next request. Not a problem by itself. |
| **D** | Uninterruptible sleep | The process is waiting on I/O (usually disk or network filesystem) in a way that *cannot* be interrupted — not even by a signal like Ctrl-C | A process stuck in `D` for a long time is a classic sign of a struggling disk, a hung NFS mount, or a failing storage device — this is one of the most operationally important states to surface, since a `D`-state process can make a system feel "frozen" in ways that are hard to diagnose without exactly this kind of evidence. |
| **T** | Stopped (or being traced) | Execution is paused — either an operator sent `SIGSTOP` (e.g. pressed Ctrl-Z in a shell) or a debugger has attached and paused it | Usually deliberate (a suspended shell job) but occasionally a forgotten, paused process quietly consuming memory without doing any work — worth surfacing rather than ignoring. |
| **Z** | Zombie | The process has already finished running, but its exit status hasn't been collected ("reaped") by its parent process yet | A zombie itself uses essentially no resources (it's just an entry in the process table holding an exit code) — the real signal is *why* it hasn't been reaped: a parent process with a bug, or one that's itself stuck. A small number of very short-lived zombies is normal churn; a large or growing count is a real problem worth flagging. |

`state` earns its place as a **required** field (Section 6) precisely
because of `D` and `Z`: these two states are exactly the kind of fact a
person would otherwise have to know to specifically go looking for
(`ps aux | grep ' D '`) — NodeIQ collecting it unconditionally, for every
process, means that evidence is simply present in the snapshot whenever
it matters, without anyone needing to have already suspected a problem.

---

## 8. Recommended Process Summarization Strategy

Sending every process's full data to the LLM is both wasteful and
actively unhelpful: a busy server can easily have 100–300+ processes, and
an LLM prompt with hundreds of near-identical entries (dozens of
`[kworker/...]` kernel threads, for instance) drowns the few genuinely
interesting rows in noise, without adding any operational value — this
directly conflicts with the project's evidence-only *and* focused
prompting goals (`CONTEXT.md`, `README.md`).

Recommended v1 strategy — summarize, don't dump:

- **`process_count`** — the total number of processes seen in this scan.
  Cheap, always meaningful ("is this number unusually high compared to
  normal for this machine?"), and requires no ranking or filtering logic
  at all.
- **`top_by_memory`** — the N (recommend N=10) processes with the highest
  `memory_rss_bytes`, sorted descending. Directly answers "what is
  consuming memory?" without requiring the LLM to scan/rank hundreds of
  entries itself.
- **`top_by_cpu`** — deferred along with per-process CPU collection
  itself (Section 6); once CPU percentages exist, the same top-N pattern
  applies.
- **`zombie_count`** (and, ideally, the PIDs/names of a small sample, not
  every one) — zombies are rare enough in a healthy system that reporting
  *how many* and *which* is more useful than including every zombie in
  the general top-N lists, where they'd likely be crowded out anyway
  (zombies use ~0 memory, so they'd never appear in `top_by_memory`).
- **Processes in `D` state** — similarly worth calling out explicitly by
  name/count, for the same reason as zombies: a `D`-state process is
  disproportionately important relative to how rarely it shows up in a
  memory- or CPU-sorted top-N list.

**Should every process go to the LLM?** No. The recommendation is that
the **collector** still gathers full per-process data internally (so
`top_by_memory` etc. can be computed accurately), but only the
**summarized** view — total count, top-N lists, zombie/`D`-state counts
and samples — becomes part of what a report or an `ask` prompt actually
includes. This mirrors how `cpu_memory.py` already works: the collector
reads far more of `/proc/meminfo` than it exposes, and only the
computed, purposeful fields make it into the snapshot. The same
discipline — collect broadly, expose only what's operationally
meaningful — should apply here, just at the process level instead of the
field level.

This is a **recommendation for a future implementation task**, not a
decision this design task is authorized to finalize outright — see Open
Design Questions below for what's still unresolved (e.g. the exact value
of N, whether full per-process data should ever be optionally available).

---

## 9. Reviewing the Existing Schema

`docs/snapshot_schema.md` Section 5 (`processes`) was drafted in Phase 2,
before any collector existed to ground it in real `/proc` data. Its
current shape:

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

Comparing this against Sections 6–8 of this design, following this
project's established practice of flagging such tensions explicitly
rather than silently reconciling or silently diverging (the same
treatment given to `system.py`'s and `cpu_memory.py`'s divergences from
their own schema sections):

- **The existing schema already summarizes, matching this design's
  recommendation.** `process_count`, `top_by_memory`, and `top_by_cpu`
  as top-level fields already reflect exactly the "summarize, don't dump"
  strategy recommended in Section 8 — this is a point of alignment, not a
  gap, and a good sign the Phase 2 schema's instincts were sound even
  before any real `/proc` data existed to confirm it.
- **No `state` field anywhere in the existing schema.** Given Section 7's
  case for `state` as the single most operationally significant field
  (specifically for surfacing `D`/`Z` processes), this is a real, worth-
  fixing gap: as currently drafted, the schema has no way to represent
  "N processes are stuck in uninterruptible sleep" or "N zombies exist"
  at all — those signals would be entirely absent from the LLM's evidence.
  Recommend adding `zombie_count` (and ideally a small sample of zombie
  PIDs/names) and a stuck/`D`-state count, alongside the existing
  `process_count`.
- **`memory_kb` (existing) vs. `memory_rss_bytes` (this design).** Same
  units-naming tension already flagged for `cpu_memory.py` — this design
  used bytes for consistency with `cpu_memory.py`'s existing
  `memory_used_bytes`/`memory_available_bytes` fields (`docs/
  cpu_memory_collector.md`), but the existing schema uses kB, matching
  its own `cpu_memory` section's kB-based fields. Whichever unit convention
  is chosen, it should probably be applied consistently across
  `cpu_memory` and `processes` — currently neither collector exists yet
  to force that consistency question to be answered, so it's still open.
- **No `command`, `owner`, `threads`, or `start_time` fields.** The
  existing schema's `top_by_memory`/`top_by_cpu` entries only have
  `pid`/`name`/the relevant metric — narrower than this design's proposed
  optional fields. This isn't necessarily wrong: Section 8 recommends
  these richer fields belong to the collector's *internal* per-process
  data, not necessarily every top-N entry sent onward. Recommend a future
  implementation task decide whether `command`/`owner`/`threads` are
  worth including in the top-N entries specifically (probably: `command`,
  for distinguishing same-named processes — see Section 6) or only
  available in fuller, non-summarized data the collector holds internally
  but doesn't expose by default.
- **`memory_percent` (existing) has no clear source in this design.**
  The existing schema's `top_by_memory` entries include a per-process
  `memory_percent` (implicitly, percent of total system memory). This is
  straightforward to compute (`memory_rss_bytes` ÷ total memory from
  `cpu_memory.py`'s `MemTotal`) but would make the Process Collector's
  output depend on a number `cpu_memory.py` collects — a cross-collector
  dependency this project's principles (`docs/data_model_design.md`,
  "collectors don't depend on each other") explicitly avoid. Recommend
  computing `memory_percent`, if kept, in the **report generator** (Phase
  4) — which is allowed to combine multiple snapshot sections — rather
  than inside the Process Collector itself.

None of these are implemented as part of this task, per its explicit
scope — they're recorded here as a reviewed, written recommendation for
whatever future task actually builds `processes.py`.

---

## 10. Quality Review

- **Is this enough to answer operational questions?** Yes for the
  headline questions this design targets ("what is consuming memory?",
  "is anything stuck?") — `state`, `memory_rss_bytes`, `process_count`,
  and the zombie/`D`-state counts directly answer them. CPU-consumption
  questions are only partially answered until per-process CPU collection
  is built (deferred, consistent with `cpu_memory.py`'s own deferred CPU
  work).
- **Is this too much data?** Not as summarized (Section 8) — a top-10
  list plus a few counts is a small, LLM-friendly payload regardless of
  how many total processes exist. It would be too much data if every
  process's full record were sent unsummarized, which is exactly why
  Section 8 recommends against that.
- **Is this appropriate for an LLM?** Yes, in summarized form — small,
  structured, and each field maps directly to a plain-English question a
  user might ask, matching the same reasoning already validated for
  `system` and `cpu_memory` (`docs/data_model_design.md`, "why the schema
  helps the LLM").
- **Can it be implemented cleanly?** Yes, following the existing
  `CollectorContext` → `collect()` → `CollectorResult` pattern from
  `system.py`/`cpu_memory.py` — the one genuinely new complexity is the
  discover-then-read-per-PID loop and its associated race condition
  (Section 5), which needs its own explicit handling (skip a PID that
  disappears mid-read; don't treat it as a collector-wide error) but is
  not architecturally different from anything the existing contract
  already supports.
- **Is v1 intentionally focused?** Yes — Section 4 explicitly excludes
  seven categories of `/proc/<pid>` data (`maps`, `environ`, `fd`, `mem`,
  `io`, `task/`, `cwd`/`root`/`exe`) that a more general-purpose process
  inspector might include, keeping this collector aimed squarely at
  memory/state/count questions rather than becoming a `/proc` browser.

---

## Open Design Questions

These are explicitly **not** resolved by this task — recorded for
whatever future task implements `processes.py`:

1. What should N be for `top_by_memory` (and eventually `top_by_cpu`)?
   This design suggests 10 as a reasonable starting point but doesn't
   treat that as settled.
2. Should `memory_percent` be computed in the Process Collector (accepting
   a cross-collector dependency on `cpu_memory`'s `MemTotal`) or in the
   future report generator (Phase 4)? This design recommends the report
   generator, to preserve collector independence, but the final call
   belongs to whichever task actually implements it.
3. Should `owner` (UID → username resolution) fail gracefully to a raw
   UID string, or be considered optional-and-omitted entirely on lookup
   failure? Both are reasonable; not decided here.
4. Should `command` (full `cmdline`) be redacted or truncated at all, given
   NodeIQ's future secret-redaction goal (some processes are launched with
   secrets as command-line arguments, e.g. `--password=...`)? This is a
   real, non-hypothetical risk (arguably a bigger one than `environ`, which
   this design already excludes for the same reason) and deserves its own
   consideration during Phase 7 (Robustness) rather than being decided as
   a side effect of this design task.
5. Should `start_time` be added once `system.py` eventually collects
   `boot_time`, or is process age not valuable enough to revisit at all?
   Left open pending that future decision.
6. Exact unit convention (`_bytes` vs. `_kb`) across `processes` and
   `cpu_memory` — should be decided once, consistently, rather than
   per-collector.
