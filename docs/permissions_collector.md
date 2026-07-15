# Permissions Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/permissions.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the
seventh real Linux collector (Collector Sprint 1, alongside
`services.py` and `scheduled_jobs.py`), and — like `processes.py` — it
needs **no commands at all**: every field comes from `pathlib.Path.stat()`
plus `pwd`/`grp` lookups.

This is intentionally the narrowest-scoped collector in NodeIQ v1.
`docs/snapshot_schema.md` Section 11 explicitly left the `permissions`
section's exact scope as an open question back in Phase 2 — this
implementation resolves it conservatively, per this task's own
instruction: **not a security audit**, just a fixed, small set of paths.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `permissions`
section, Section 11, whose field shape this implementation matches
closely — see "Schema Alignment" below).

---

## Responsibilities

For each of four fixed, conservative paths —

- `/etc/passwd`
- `/etc/shadow`
- `/etc/ssh`
- `/var/log`

— this collector reports:

- `exists` — whether the path is present on this system at all.
- `owner` / `group` — resolved to names where possible, falling back to
  the raw UID/GID as a string otherwise (the same graceful-degradation
  pattern `processes.py` already uses for process ownership).
- `mode` — the permission bits as a three-digit octal string (e.g.
  `"644"`).
- `world_writable` — `True` if *anyone* on the system can write to this
  path, regardless of ownership — the one "obviously suspicious"
  condition this v1 flags explicitly, per this task's instruction.

No recursive directory scanning, no SUID/SGID/ACL inspection, no
comparison against a "known good" baseline — any of that would start to
be the security audit this task explicitly says not to attempt.

---

## Three States, Not Two

Following `PROJECT_RULES.md` Section 7's "the system genuinely has none
of this" vs. "we couldn't check" distinction, `_check_path` distinguishes
**three** outcomes per path, not just "worked" or "failed":

| Outcome | `exists` | Other fields | Recorded as an error? |
|---|---|---|---|
| Path exists, `stat()` succeeds | `True` | Fully populated | No |
| Path genuinely doesn't exist (`FileNotFoundError`) | `False` | All `None` | **No** — a real, valid fact about this system |
| `stat()` fails for another reason (e.g. `PermissionError` on a parent directory) | `None` (unknown, not `False`) | All `None` | **Yes** — this is a genuine "we couldn't check" |

Only the third row produces a `collection_errors` entry. Conflating rows
two and three — treating "doesn't exist" and "couldn't check" as the
same `exists: False` — would be exactly the mistake `PROJECT_RULES.md`
Section 7 warns against: a report or an `ask` answer would have no way
to tell "this file genuinely isn't here" from "something blocked us from
even looking."

Every path is checked independently in its own `_check_path` call — one
path failing this way never prevents the other three from being checked
(the same per-item independence `disk.py`'s per-filesystem entries and
`processes.py`'s per-PID reads already established, just applied to a
fixed list instead of a discovered one).

---

## Why No Commands Are Needed

`stat()` is a single system call any program can make on any path it has
directory-traversal access to — there's no external tool (`ls`, `stat`
the command) that provides this information any more directly than
Python's own `pathlib.Path.stat()` already does. This mirrors
`cpu_memory.py`'s and `processes.py`'s reasoning for preferring direct
system interfaces over commands (`PROJECT_RULES.md` Section 9, item 7) —
here taken to its natural conclusion: no subprocess at all, for any
field this collector produces.

`owner`/`group` resolution (`pwd.getpwuid`/`grp.getgrgid`) is the same
pattern `processes.py` already established for UID resolution, extended
here with the equivalent GID lookup for group names.

---

## Schema Alignment

`docs/snapshot_schema.md` Section 11's `checked_paths` shape (`path`,
`owner`, `group`, `mode`, `world_writable`) is matched by this
implementation field-for-field, with one addition: an explicit `exists`
field, needed to make the three-state distinction above representable
at all (the original schema didn't anticipate a path simply not being
present). This is a genuine, useful addition rather than a divergence to
reconcile — the schema's own fields are otherwise unchanged.

---

## Testing

- **Unit tests** (`tests/collectors/test_permissions.py`, 10 tests):
  `_check_path` tested against a real `tmp_path` file (normal
  permissions, world-writable permissions, a missing path, and a
  monkeypatched `Path.stat` raising `PermissionError` to exercise the
  genuine-error path); `_resolve_owner`/`_resolve_group` tested for both
  successful and failing lookups; `collect()` tested end-to-end for the
  full-path-list happy case and for one path failing without affecting
  the others.
- **Integration test**
  (`tests/collectors/test_permissions_integration.py`, 1 test): calls
  the real `collect()` with nothing mocked, automatically skipped unless
  running on Linux. Verified on the Multipass VM (real result: all four
  paths exist, `/etc/shadow` correctly owned by `root:shadow` at mode
  `640`, no errors) as part of the full 151-test suite for this sprint.
  Also confirmed working correctly on the local macOS dev machine (no
  subprocess dependency means this collector needs no Linux-specific
  graceful degradation at all — only `/etc/shadow`, which doesn't exist
  on macOS, correctly comes back `exists: False`).

---

## Collector Review Checklist

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — every `stat()` call is individually wrapped; one path's failure never affects another.
- [x] Distinguishes "doesn't exist" from "couldn't check" as three explicit states, not two, per `PROJECT_RULES.md` Section 7.
- [x] No subprocess calls at all — every fact comes from `pathlib.Path.stat()` and `pwd`/`grp` lookups.
- [x] `owner`/`group` resolution degrades gracefully to the raw UID/GID string when no name can be resolved.
- [x] Flags exactly one "obviously suspicious" condition (`world_writable`) rather than building a broader rule engine — matches this task's explicit "not a security audit" instruction.
- [x] Checks a fixed, conservative path list — no recursive scanning, no dynamic path discovery.
- [x] Field names use `snake_case` and match `docs/snapshot_schema.md` Section 11 exactly, plus one well-justified addition (`exists`).
- [x] Unit tests cover the three-state `stat()` outcome, owner/group resolution, and `collect()` end-to-end (including one path failing without affecting others); an integration test verifies real behavior on the Multipass VM.
