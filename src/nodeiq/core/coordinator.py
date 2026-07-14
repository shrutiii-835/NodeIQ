"""The scan coordinator.

**Not implemented yet.** This module is a documented placeholder for
Phase 3.2, once individual collectors exist for it to orchestrate. It
exists now so the rest of `nodeiq.core` (runner, result, exceptions) can be
built and tested against a stable package layout, without pretending
scanning itself is already working.

Future responsibilities
------------------------
When implemented, the coordinator will:

- Discover and run every collector in `nodeiq.collectors` (Phase 3.2).
- Call each collector's single entry-point function, catching anything it
  raises so that one collector's failure never stops the others from
  running (see PROJECT_RULES.md Section 7, Error Handling Philosophy) —
  this is a last-resort safety net; each collector is expected to catch
  its own anticipated failures first (see docs/collector_guidelines.md).
- Assemble every collector's returned `data` half into the top-level
  snapshot envelope defined in CONTEXT.md Section 7 and
  docs/snapshot_schema.md (`timestamp`, `hostname`, `metadata`, `system`,
  `cpu_memory`, ...).
- Populate `metadata` itself — schema version, scan timing, which
  collectors ran or were skipped — since that data is about the scan
  process, not about the machine, and isn't any individual collector's job
  (see docs/snapshot_schema.md Section 2).
- Populate `collection_errors` by gathering the `errors` half of every
  collector's return value, rather than collectors writing to it directly
  (see docs/snapshot_schema.md Section 12 and docs/collector_guidelines.md).
- Eventually write the finished snapshot to `snapshots/` as JSON, once the
  CLI's `scan` command (Phase 5) calls into this module.

Orchestration role
-------------------
The coordinator is the *only* piece of code that knows about every
collector at once. Each collector only knows about its own job and the
shared `nodeiq.core` infrastructure — collectors never know about each
other, and never know they're part of a larger scan. The coordinator is
what turns "a pile of independent collectors" into "one coherent
snapshot."

Interaction with collectors
-----------------------------
The coordinator will call each collector's entry-point function
(`collect() -> tuple[dict, list[dict]]`, per PROJECT_RULES.md Section 9
and docs/collector_guidelines.md), catch anything unexpected it raises,
and record its `(data, errors)` result. Collectors never call each other,
and never talk to the coordinator except through that one return value —
this is what makes it possible to add, remove, or fix one collector
without ever touching another.

Snapshot assembly
-------------------
"Assembly" means combining every collector's independently-produced
section under the fixed top-level keys from CONTEXT.md Section 7. The
coordinator is the one place that actually builds the final JSON object;
no individual collector ever sees or produces the full snapshot itself.
"""


def run_scan() -> dict:
    """Run every collector and assemble one snapshot.

    Not implemented yet — see the module docstring above for what this
    will do once collectors exist to orchestrate (Phase 3.2).
    """
    raise NotImplementedError(
        "run_scan() is a placeholder — no collectors exist yet (Phase 3.2)."
    )
