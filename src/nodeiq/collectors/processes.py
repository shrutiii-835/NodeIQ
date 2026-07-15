"""Process collector: a summarized view of currently running processes.

Answers "what is consuming memory?" and "is anything stuck?" at the
process level. Follows the same `CollectorContext` -> `collect()` ->
`CollectorResult` pattern established by `system.py` and `cpu_memory.py`,
reading only `/proc/<pid>/status`, `/proc/<pid>/cmdline`, and
`/proc/<pid>/comm` directly — no commands (`ps`) are ever run. See
docs/process_collector_design.md for the full design rationale and
docs/process_collector.md for this implementation's specifics.

v1 scope is intentionally narrow and summarized, not per-process detail:
`process_count`, `zombie_count`, `blocked_process_count` (state `D`), and
the top 10 processes by memory (`top_by_memory`). `/proc/<pid>/stat` is
not parsed in v1 — see docs/process_collector.md, "Why `stat` Was
Intentionally Deferred."
"""

import pwd
import time
from pathlib import Path

from nodeiq.core.collector import CollectorContext, CollectorResult

_PROC_ROOT = Path("/proc")
_TOP_N = 10
_ZOMBIE_STATE = "Z"
_BLOCKED_STATE = "D"


def collect(context: CollectorContext) -> CollectorResult:
    """Gather a summarized view of every currently running process.

    Discovers every PID under `/proc`, reads each one's `status`, `comm`,
    and `cmdline`, and returns only a summary — `process_count`,
    `zombie_count`, `blocked_process_count`, and the top 10 processes by
    memory — never every process's raw data (see
    docs/process_collector_design.md, "Recommended Process Summarization
    Strategy"). A process that exits between being discovered and being
    read is skipped silently: that's an expected race, not a collector
    failure (see docs/process_collector.md, "Race Conditions When
    Scanning Processes").
    """
    start_time = time.monotonic()
    errors: list[dict] = []

    try:
        pids = _discover_pids()
    except ValueError as exc:
        errors.append(_error_entry(exc))
        return CollectorResult(
            collector_name="processes",
            data={
                "process_count": None,
                "zombie_count": None,
                "blocked_process_count": None,
                "top_by_memory": None,
            },
            errors=errors,
            duration_ms=(time.monotonic() - start_time) * 1000,
        )

    processes: list[dict] = []
    for pid in pids:
        entry = _read_process(pid)
        if entry is not None:
            processes.append(entry)

    return CollectorResult(
        collector_name="processes",
        data=_summarize(processes),
        errors=errors,
        duration_ms=(time.monotonic() - start_time) * 1000,
    )


def _error_entry(exc: ValueError) -> dict:
    """Build one collection_errors-shaped entry from a caught ValueError.

    See docs/snapshot_schema.md Section 12 for the shape this matches.
    """
    return {
        "message": str(exc),
        "severity": "error",
        "exception_type": type(exc).__name__,
    }


def _discover_pids() -> list[int]:
    """List every currently-running PID by reading `/proc`'s numbered
    directory entries.

    Raises `ValueError` if `/proc` itself can't be listed at all (e.g. on
    a system with no `/proc`, such as macOS) — this is the one failure
    mode that means nothing about processes can be collected at all, so
    it's the only case this collector treats as a real error rather than
    a per-process skip.
    """
    try:
        return sorted(
            int(entry.name) for entry in _PROC_ROOT.iterdir() if entry.name.isdigit()
        )
    except OSError as exc:
        raise ValueError(f"could not list {_PROC_ROOT}: {exc}") from exc


def _read_process(pid: int) -> dict | None:
    """Gather one process's state, memory, owner, name, and command line.

    Returns `None` if the process no longer exists by the time we get
    around to reading it — a process can legitimately exit between being
    listed by `_discover_pids` and having its files read here. This is an
    expected race (see docs/process_collector.md), not an error: the
    caller simply skips this PID and keeps scanning the rest.
    """
    pid_dir = _PROC_ROOT / str(pid)
    try:
        status_text = (pid_dir / "status").read_text()
        comm_text = (pid_dir / "comm").read_text()
        cmdline_text = (pid_dir / "cmdline").read_text()
    except OSError:
        return None

    try:
        status_fields = _parse_status(status_text)
    except ValueError:
        return None

    return {
        "pid": pid,
        "process_name": comm_text.strip(),
        "memory_rss_bytes": status_fields["memory_rss_bytes"],
        "owner": _resolve_owner(status_fields["uid"]),
        "state": status_fields["state"],
        "command": _parse_cmdline(cmdline_text),
    }


def _parse_status(raw_text: str) -> dict:
    """Pure function: `/proc/<pid>/status`'s text in, this collector's
    three status-derived fields (`state`, `memory_rss_bytes`, `uid`) out.

    `state` and `uid` are required for every process and raise
    `ValueError` if missing. `memory_rss_bytes` defaults to `0` rather
    than raising when absent, since kernel threads (e.g. `kthreadd`)
    legitimately have no `VmRSS` line at all — they have no memory
    address space to report.
    """
    state = None
    memory_rss_bytes = None
    uid = None

    for line in raw_text.splitlines():
        if line.startswith("State:"):
            state = _parse_state(line)
        elif line.startswith("VmRSS:"):
            memory_rss_bytes = _parse_vmrss(line)
        elif line.startswith("Uid:"):
            uid = _parse_uid(line)

    if state is None:
        raise ValueError("State not found in /proc/<pid>/status")
    if uid is None:
        raise ValueError("Uid not found in /proc/<pid>/status")

    return {
        "state": state,
        "memory_rss_bytes": memory_rss_bytes if memory_rss_bytes is not None else 0,
        "uid": uid,
    }


def _parse_state(line: str) -> str:
    """Pure function: a status line like `State:\tS (sleeping)` in, the
    single-letter state code (`S`) out.
    """
    _, _, rest = line.partition(":")
    rest = rest.strip()
    if not rest:
        raise ValueError(f"could not parse process state from: {line!r}")
    return rest.split()[0]


def _parse_vmrss(line: str) -> int:
    """Pure function: a status line like `VmRSS:\t    3120 kB` in, RSS
    memory in bytes out.
    """
    _, _, rest = line.partition(":")
    tokens = rest.split()
    if not tokens:
        raise ValueError(f"could not parse VmRSS from: {line!r}")
    try:
        return int(tokens[0]) * 1024
    except ValueError as exc:
        raise ValueError(f"could not parse VmRSS value {tokens[0]!r}") from exc


def _parse_uid(line: str) -> int:
    """Pure function: a status line like `Uid:\t1000\t1000\t1000\t1000` in,
    the real UID (the first of the four values) out.
    """
    _, _, rest = line.partition(":")
    tokens = rest.split()
    if not tokens:
        raise ValueError(f"could not parse Uid from: {line!r}")
    try:
        return int(tokens[0])
    except ValueError as exc:
        raise ValueError(f"could not parse Uid value {tokens[0]!r}") from exc


def _parse_cmdline(raw_text: str) -> str:
    """Pure function: `/proc/<pid>/cmdline`'s NUL-separated text in, a
    space-joined command string out. Empty for kernel threads, which
    legitimately have no command line at all — not treated as an error.
    """
    return " ".join(part for part in raw_text.split("\0") if part)


def _resolve_owner(uid: int) -> str:
    """Resolve a UID to a username via the system's user database.

    Falls back to the numeric UID as a string if no username can be
    resolved (e.g. an LDAP-backed UID with no local mapping) — a raw UID
    is still useful evidence, so this degrades gracefully rather than
    omitting `owner` entirely.
    """
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def _summarize(processes: list[dict]) -> dict:
    """Turn the full per-process list into the summarized snapshot shape:
    total counts plus the top N by memory.

    Per docs/process_collector_design.md's "Recommended Process
    Summarization Strategy," NodeIQ never sends every process's data
    onward — only this summary, which is what this collector actually
    returns.
    """
    zombie_count = sum(1 for process in processes if process["state"] == _ZOMBIE_STATE)
    blocked_process_count = sum(
        1 for process in processes if process["state"] == _BLOCKED_STATE
    )
    top_by_memory = sorted(
        processes, key=lambda process: process["memory_rss_bytes"], reverse=True
    )[:_TOP_N]

    return {
        "process_count": len(processes),
        "zombie_count": zombie_count,
        "blocked_process_count": blocked_process_count,
        "top_by_memory": top_by_memory,
    }
