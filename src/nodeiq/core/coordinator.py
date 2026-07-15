"""The scan coordinator.

Runs every registered collector, times the whole scan, aggregates
whatever went wrong, and assembles one in-memory snapshot dict. This is
the MVP implementation (Phase 3.4) — it never writes anything to disk and
knows nothing about the CLI; both are later phases (5). See
docs/coordinator.md for the full design, including where this MVP
deliberately simplifies the fuller envelope in docs/snapshot_schema.md.

Orchestration role
-------------------
The coordinator is the *only* piece of code that knows about every
collector at once. Each collector only knows about its own job and the
shared `nodeiq.core` infrastructure — collectors never know about each
other, and never know they're part of a larger scan (see
docs/collector_guidelines.md). The coordinator is what turns "a pile of
independent collectors" into one coherent snapshot.

Interaction with collectors
-----------------------------
The coordinator builds exactly one `CollectorContext` per scan and passes
the same instance to every registered collector's
`collect(context: CollectorContext) -> CollectorResult`. It also catches
anything a collector raises — a last-resort safety net; each collector is
already expected to catch its own anticipated failures first, per
docs/collector_guidelines.md, so this should rarely trigger in practice.

Snapshot assembly
-------------------
Every registered collector's `CollectorResult.data` is stored under its
own `collector_name` key; every non-empty `CollectorResult.errors` is
stored under the same key in `collection_errors`. The coordinator also
builds `metadata` itself, since that's a fact about the scan process, not
about the machine, and isn't any individual collector's job.
"""

import time
from datetime import datetime, timezone

from nodeiq import __version__ as _NODEIQ_VERSION
from nodeiq.collectors import cpu_memory, disk, processes, system
from nodeiq.core.collector import CollectorContext

_REGISTERED_COLLECTORS = [system, cpu_memory, processes, disk]
"""Every collector the coordinator runs, in the order they run. A plain
list — no registry object, no discovery mechanism, no plugin system.
Adding a collector to a future scan means adding one line here."""

_REQUIRED_SECTIONS = (
    "metadata",
    "system",
    "cpu_memory",
    "processes",
    "disk",
    "collection_errors",
)


def run_scan() -> dict:
    """Run every registered collector and assemble one in-memory snapshot.

    Builds one `CollectorContext`, calls every collector in
    `_REGISTERED_COLLECTORS` with it, and combines the results into a
    single dict shaped like:

        {
            "metadata": {...},
            "collection_errors": {...},
            "system": {...},
            "cpu_memory": {...},
            "processes": {...},
            "disk": {...},
        }

    Never writes to disk — returns a plain dict.
    """
    scan_start_time = datetime.now(timezone.utc)
    scan_start = time.monotonic()

    context = CollectorContext(scan_start_time=scan_start_time)

    sections: dict = {}
    collection_errors: dict = {}

    for collector_module in _REGISTERED_COLLECTORS:
        fallback_name = collector_module.__name__.rsplit(".", 1)[-1]
        try:
            result = collector_module.collect(context)
        except Exception as exc:
            # Last-resort safety net: a collector raising at all means it
            # didn't catch its own anticipated failures, per
            # docs/collector_guidelines.md. One collector crashing must
            # never stop the rest of the scan.
            sections[fallback_name] = None
            collection_errors[fallback_name] = [
                {
                    "message": f"collector crashed: {exc}",
                    "severity": "error",
                    "exception_type": type(exc).__name__,
                }
            ]
            continue

        sections[result.collector_name] = result.data
        if result.errors:
            collection_errors[result.collector_name] = result.errors

    scan_duration_ms = (time.monotonic() - scan_start) * 1000

    system_data = sections.get("system") or {}
    metadata = {
        "scan_timestamp": scan_start_time.isoformat(),
        "scan_duration_ms": scan_duration_ms,
        "collector_count": len(_REGISTERED_COLLECTORS),
        "nodeiq_version": _NODEIQ_VERSION,
        "hostname": system_data.get("hostname"),
    }

    snapshot = {
        "metadata": metadata,
        "collection_errors": collection_errors,
        **sections,
    }

    _validate_snapshot(snapshot)
    return snapshot


def _validate_snapshot(snapshot: dict) -> None:
    """Sanity-check that the assembled snapshot has every section this
    MVP coordinator is expected to produce.

    This is a defensive check on the coordinator's *own* output, not on
    external input — with the current registered collectors, every
    section is always populated (successfully or as a recorded crash), so
    this should never actually fail. If it ever does, that means a bug in
    `run_scan()` itself (e.g. a registered collector whose declared
    `collector_name` doesn't match what was expected), which is exactly
    the kind of mistake this check exists to catch loudly rather than
    silently return an incomplete snapshot. No external validation
    library is used — this is a plain key-presence check.
    """
    missing = [key for key in _REQUIRED_SECTIONS if key not in snapshot]
    if missing:
        raise ValueError(
            f"assembled snapshot is missing required section(s): {missing}"
        )
