# Snapshot Persistence — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/core/snapshot.py`), with
a real save/load round trip verified against the Multipass Ubuntu 24.04
VM (`DECISIONS.md` ADR-002). This is Phase 3.8 — the first time a
NodeIQ snapshot is written to disk at all. No CLI, no report generator,
and no LLM integration exist yet; this phase is deliberately narrow.

Read this alongside [coordinator.md](coordinator.md) (which produces the
in-memory snapshot this module saves) and
[snapshot_schema.md](snapshot_schema.md) (the shape of what gets saved).

---

## Why Snapshots Are Stored

`nodeiq.core.coordinator.run_scan()` has always produced a complete
snapshot — but only in memory, discarded the moment the calling process
exits. That was correct for validating the collector architecture
(Phases 3.1–3.7), but it means a snapshot was never actually usable for
anything beyond the one Python process that happened to call
`run_scan()`.

`CONTEXT.md`'s snapshot-first philosophy depends on a snapshot being a
durable, standalone artifact: `report` (Phase 4) needs to read a
snapshot that was captured by an earlier `scan` run, possibly minutes,
hours, or days before; `ask` (Phase 6) needs the same. Neither can exist
until a snapshot can outlive the process that produced it — this phase
is what makes that possible.

---

## Snapshot Lifecycle

```
run_scan()  →  save_snapshot(snapshot)  →  snapshots/snapshot_<timestamp>.json
                                                     │
                                                     ▼
                                    load_snapshot(path) / load_latest_snapshot()
                                                     │
                                                     ▼
                                    a plain dict, identical to what was saved
```

1. **Produce** — `run_scan()` builds a snapshot entirely in memory, as it
   always has. Nothing about this phase changes that.
2. **Save** — `save_snapshot(snapshot)` creates `snapshots/` if it
   doesn't exist, writes the snapshot as formatted JSON to a new,
   timestamped file, and returns the path it wrote.
3. **Load** — `load_snapshot(path)` reads one specific snapshot file back
   into a plain dict, or `load_latest_snapshot()` finds and loads the
   newest one in `snapshots/` without needing to know its exact filename.

Every snapshot file is independent and self-contained, per
`docs/snapshot_schema.md` — loading one never depends on any other
snapshot existing.

---

## Naming Convention

```
snapshot_20260715T083446389181.json
         │        │      │
         │        │      └── microseconds (6 digits)
         │        └────────── HHMMSS
         └─────────────────── YYYYMMDD
```

The timestamp is taken from the snapshot's own `metadata.scan_timestamp`
(an ISO 8601 string every snapshot already has — see
`docs/snapshot_schema.md` Section 1), not the wall-clock time at the
moment of saving. This makes the filename **deterministic**: the same
snapshot content always produces the same filename, regardless of when
or how many times it's saved, and the filename reflects *when the scan
actually happened*, not some unrelated later moment.

Microsecond precision (not just seconds) means two snapshots captured
within the same second — realistic in tests, or in rapid successive
scans — still get distinct filenames rather than silently overwriting
one another.

**Why this makes `load_latest_snapshot()` simple:** because the
timestamp components are fixed-width and zero-padded, sorting filenames
*alphabetically* is the same as sorting them *chronologically*.
`load_latest_snapshot()` takes advantage of this directly — it sorts
the filenames in `snapshots/` and takes the last one, rather than
`stat()`-ing every file to compare modification times. This is also more
robust than relying on filesystem timestamps, which can change for
reasons that have nothing to do with when a scan happened (a backup
restore, a `git checkout`, copying files between machines).

If a snapshot's own `metadata.scan_timestamp` is missing or unparseable
(e.g. a hand-constructed test fixture), the filename falls back to the
current time — a snapshot is still worth saving even without a usable
embedded timestamp, per this project's "partial data beats no data"
philosophy (`PROJECT_RULES.md` Section 7), just without the
determinism guarantee in that one degraded case.

---

## Why Persistence Is Separated From Scanning

`nodeiq.core.coordinator.py` and `nodeiq.core.snapshot.py` don't import
each other in either direction. This is a deliberate application of the
same separation-of-concerns principle already used throughout NodeIQ
(collectors don't know about the coordinator; the coordinator doesn't
know about the CLI):

- **The coordinator's job is producing a correct, complete snapshot** —
  running every registered collector, aggregating errors, building
  metadata. It has no opinion about *what happens to that snapshot
  afterward*: whether it gets saved, printed, discarded, or sent
  somewhere else entirely.
- **This module's job is turning a snapshot into a durable file, and
  back.** It has no opinion about *how* a snapshot was produced — it
  would work identically on a hand-constructed test fixture or a real
  `run_scan()` result, since both are just dicts matching the same
  shape.

Keeping these independent means either one can change without touching
the other: a future "quick scan" mode that changes what `run_scan()`
collects doesn't need to touch `snapshot.py` at all, and a future change
to *where* snapshots are stored (a different directory, compression, a
retention policy) doesn't need to touch `coordinator.py` at all. The
connection between them is exactly one line, left for the caller to
write — the CLI (Phase 5) will eventually be that caller:

```python
from nodeiq.core.coordinator import run_scan
from nodeiq.core.snapshot import save_snapshot

snapshot = run_scan()
saved_path = save_snapshot(snapshot)
```

---

## Error Handling

- **`save_snapshot`** creates `snapshots/` if missing (`Path.mkdir(parents=True,
  exist_ok=True)`) rather than requiring it to already exist — the
  common case (first scan ever run) shouldn't require a separate setup
  step.
- **`load_snapshot`** raises `SnapshotError` (a new exception in
  `nodeiq.core.exceptions`, alongside `InvalidCommandError`) for every
  way a snapshot file can be broken: unreadable (`OSError`), not valid
  JSON (`json.JSONDecodeError`), or valid JSON that doesn't look like a
  snapshot (not an object, or missing `metadata`). Unlike a collector's
  own failures — which are absorbed into `collection_errors` so a scan
  never crashes — loading a snapshot from disk isn't a scan; there's no
  partial result to gracefully degrade to, so a genuinely broken file is
  a real, raised error the caller must handle.
- **`load_latest_snapshot`** treats a missing `snapshots/` directory and
  an empty one identically — both mean "nothing to load yet," reported
  as the same `SnapshotError`, rather than a missing-directory case
  crashing differently than an empty-directory case.
- **Validation is deliberately shallow.** `load_snapshot` only confirms
  the loaded JSON is an object with a `metadata` key — it does *not*
  check for every collector section the way
  `nodeiq.core.coordinator._validate_snapshot` does for snapshots it
  just assembled. That fuller check is the coordinator's responsibility
  for snapshots it produces; this module's job is only to catch "this
  file clearly isn't a snapshot at all," keeping the two modules'
  responsibilities from blurring together.

---

## Testing

`tests/core/test_snapshot.py` (16 tests) — every test redirects
`_SNAPSHOTS_DIR` to `tmp_path`, so nothing touches the real project's
`snapshots/` directory:

- `save_snapshot` creates the directory when missing, writes valid,
  indented JSON, returns the path it wrote, and derives its filename
  from `metadata.scan_timestamp` (with two tests covering the fallback
  when that field is missing or malformed).
- `load_snapshot` restores byte-for-byte identical data (both from a
  `Path` and a plain string), and raises `SnapshotError` for a missing
  file, malformed JSON, valid JSON that isn't an object, and valid JSON
  missing `metadata`.
- `load_latest_snapshot` correctly picks the newest of several saved
  snapshots by filename, raises gracefully for both a missing and an
  empty `snapshots/` directory, and ignores unrelated non-snapshot files
  in the same directory.

Verified for real, beyond the test suite: a genuine `run_scan()` result
was saved, reloaded, and compared for exact equality — both on macOS and
on the Multipass VM (`DECISIONS.md` ADR-002) — confirming the whole
`run_scan() → save_snapshot() → load_snapshot()` round trip works with a
real 9-collector snapshot, not just hand-built test fixtures.

---

## Collector Review Checklist

*(Adapted for a persistence module rather than a collector — the same
underlying standard applies.)*

- [x] Exposes exactly the three functions this phase asked for:
  `save_snapshot`, `load_snapshot`, `load_latest_snapshot` — no extra
  public surface.
- [x] Never silently swallows a broken snapshot file — every failure
  mode raises a specific, catchable `SnapshotError`.
- [x] No dependency on `nodeiq.core.coordinator` in either direction —
  persistence and scanning remain fully independent.
- [x] Filenames are deterministic (derived from snapshot content, not
  wall-clock save time) and sort chronologically by construction.
- [x] JSON is written indented, for a human to read directly if needed —
  not minified.
- [x] No unnecessary abstractions — no snapshot "repository" class, no
  configurable storage backend, no caching layer; three plain functions
  operating on a fixed `snapshots/` directory, matching this phase's
  explicit scope.
- [x] Unit tests cover every documented behavior (directory creation,
  valid JSON, round-trip fidelity, latest-selection, missing-directory
  and malformed-JSON handling); verified for real on the Multipass VM
  with an actual `run_scan()` result.
