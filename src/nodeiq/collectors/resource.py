"""Resource collector: memory and CPU load.

Answers "how loaded is this machine right now?" — one of NodeIQ's
headline example questions ("what is consuming memory?", "is this system
under load?"). Follows the same `CollectorContext` -> `collect()` ->
`CollectorResult` pattern established by `system.py`
(docs/system_collector.md), but needs no commands at all: every field
comes from reading `/proc/meminfo` and `/proc/loadavg` directly.

v1 scope is intentionally narrow: memory usage (from `/proc/meminfo`) and
load averages (from `/proc/loadavg`). CPU utilization percentages are not
collected yet — see docs/resource_collector.md.
"""

import time
from pathlib import Path

from nodeiq.core.collector import CollectorContext, CollectorResult

_MEMINFO_PATH = Path("/proc/meminfo")
_LOADAVG_PATH = Path("/proc/loadavg")

_REQUIRED_MEMINFO_KEYS = {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}


def collect(context: CollectorContext) -> CollectorResult:
    """Gather memory usage and CPU load average.

    Memory and load average are two independent data sources
    (`/proc/meminfo` and `/proc/loadavg`) — if one can't be read or
    parsed, its fields are recorded as `None` and the failure is added to
    `errors`, but the other data source is still collected. See
    PROJECT_RULES.md Section 7 and docs/collector_guidelines.md for why
    partial data always beats no data.
    """
    start_time = time.monotonic()
    data: dict = {}
    errors: list[dict] = []

    try:
        data.update(_get_memory_fields())
    except ValueError as exc:
        data["memory_used_bytes"] = None
        data["memory_available_bytes"] = None
        data["memory_usage_percent"] = None
        data["swap_used_bytes"] = None
        data["swap_usage_percent"] = None
        errors.append(_error_entry(exc))

    try:
        data.update(_get_load_average_fields())
    except ValueError as exc:
        data["load_average_1m"] = None
        data["load_average_5m"] = None
        data["load_average_15m"] = None
        errors.append(_error_entry(exc))

    return CollectorResult(
        collector_name="resource",
        data=data,
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


def _read_proc_file(path: Path) -> str:
    """Read a `/proc` file's full text content.

    Shared by `_get_memory_fields` and `_get_load_average_fields`, since
    both read a `/proc` file the same way. Raises `ValueError` (not
    `OSError`) if the file can't be read, matching every other
    anticipated-failure path in this collector.
    """
    try:
        return path.read_text()
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc


def _get_memory_fields() -> dict:
    """Read `/proc/meminfo` and compute memory/swap usage fields.

    Raises `ValueError` if the file can't be read, or if it's missing one
    of the four values this collector needs.
    """
    raw_text = _read_proc_file(_MEMINFO_PATH)
    raw_kb = _parse_meminfo(raw_text)
    return _compute_memory_fields(raw_kb)


def _parse_meminfo(raw_text: str) -> dict:
    """Pure function: `/proc/meminfo`'s text in, a dict of the four raw
    kB values this collector needs (`MemTotal`, `MemAvailable`,
    `SwapTotal`, `SwapFree`) out. No file I/O — just string parsing, so it
    can be tested with a literal sample string.
    """
    values = {}
    for line in raw_text.splitlines():
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        if key not in _REQUIRED_MEMINFO_KEYS:
            continue
        tokens = rest.strip().split()
        if not tokens:
            raise ValueError(f"{key} has no value in /proc/meminfo")
        try:
            values[key] = int(tokens[0])
        except ValueError as exc:
            raise ValueError(
                f"could not parse {key} value in /proc/meminfo: {tokens[0]!r}"
            ) from exc

    missing = _REQUIRED_MEMINFO_KEYS - values.keys()
    if missing:
        raise ValueError(f"missing required /proc/meminfo fields: {sorted(missing)}")
    return values


def _compute_memory_fields(raw_kb: dict) -> dict:
    """Pure function: raw kB values from `/proc/meminfo` in, the five
    computed memory/swap fields (bytes and percentages) out.
    """
    mem_used_kb = raw_kb["MemTotal"] - raw_kb["MemAvailable"]
    swap_used_kb = raw_kb["SwapTotal"] - raw_kb["SwapFree"]

    return {
        "memory_used_bytes": mem_used_kb * 1024,
        "memory_available_bytes": raw_kb["MemAvailable"] * 1024,
        "memory_usage_percent": _percent(mem_used_kb, raw_kb["MemTotal"]),
        "swap_used_bytes": swap_used_kb * 1024,
        "swap_usage_percent": _percent(swap_used_kb, raw_kb["SwapTotal"]),
    }


def _percent(part: int, whole: int) -> float:
    """Pure function: what percentage `part` is of `whole`, rounded to two
    decimal places. Returns `0.0` if `whole` is zero or negative (e.g. a
    machine with no swap configured at all has `SwapTotal == 0`) rather
    than raising a division-by-zero error.
    """
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100, 2)


def _get_load_average_fields() -> dict:
    """Read `/proc/loadavg` and return the three load average fields.

    Raises `ValueError` if the file can't be read or doesn't have the
    expected fields.
    """
    raw_text = _read_proc_file(_LOADAVG_PATH)
    return _parse_loadavg(raw_text)


def _parse_loadavg(raw_text: str) -> dict:
    """Pure function: `/proc/loadavg`'s text in, the three load average
    fields out. No file I/O — just string parsing, so it can be tested
    with a literal sample string.
    """
    tokens = raw_text.split()
    if len(tokens) < 3:
        raise ValueError(f"/proc/loadavg did not have the expected fields: {raw_text!r}")
    try:
        return {
            "load_average_1m": float(tokens[0]),
            "load_average_5m": float(tokens[1]),
            "load_average_15m": float(tokens[2]),
        }
    except ValueError as exc:
        raise ValueError(f"could not parse /proc/loadavg values: {raw_text!r}") from exc
