# Collector Guidelines — NodeIQ Collector Design Pattern

**Status:** Design only. This document defines the standard contract every
collector will follow — no collector exists yet (Phase 3.2B). Nothing here
runs a Linux command or writes any Python code.

This document is the practical, "how do I write a collector" companion to
[docs/architecture.md](architecture.md) (the execution infrastructure a
collector builds on) and [docs/snapshot_schema.md](snapshot_schema.md) (the
exact shape each collector's output must match). Read all three together
when Phase 3.2B begins.

---

## Purpose of a Collector

A collector is a small, self-contained Python module responsible for
gathering **one** category of Linux system information and turning it into
structured data matching **one** section of the snapshot schema (see
`docs/snapshot_schema.md`). For example, the future `disk.py` collector's
entire job is: find out how full every mounted filesystem is, and return
that as a `disk` object.

A collector is not a mini-application. It doesn't decide what to do with
its data (that's `report` and `ask`'s job, Phases 4 and 6), and it doesn't
know it's part of a larger scan (that's the coordinator's job — see
`docs/architecture.md`, "Why the Coordinator Owns Snapshot Assembly"). It
just answers one question: "what does this one part of the system look
like right now?"

---

## Collector Responsibilities

Every collector is responsible for, and only for:

1. Gathering whatever raw evidence it needs, using whichever of the two
   supported methods actually fits the data source (see "Two Ways to
   Gather Evidence" below): running a command via
   `nodeiq.core.runner.run_command`, or reading a file (most often
   somewhere under `/proc`) directly with plain Python file I/O.
2. Parsing that raw output into the structured shape defined for its
   section in `docs/snapshot_schema.md`.
3. Validating the parsed data is sane before returning it (e.g., a
   percentage should be between 0 and 100; a PID should be a positive
   integer).
4. Reporting anything that went wrong along the way, in enough detail that
   a human (or the coordinator, or eventually the LLM) can tell what
   couldn't be determined and why.
5. Returning its result through the standard contract below — nothing
   more, nothing less.

## What a Collector Must NOT Do

- **Must not call `subprocess` directly.** If a collector needs to run an
  external command, that always goes through
  `nodeiq.core.runner.run_command`, so every collector gets the same
  timeout/safety guarantees automatically (see `docs/architecture.md`,
  "Why the Runner Centralizes Subprocess Execution"). This doesn't apply
  to reading a file directly (e.g. `/proc/meminfo`) — that's plain file
  I/O, not a subprocess, and doesn't go through the runner at all (see
  "Two Ways to Gather Evidence" below).
- **Must not call, import, or depend on another collector.** Collectors
  are independent — see `docs/data_model_design.md`, "Why Collectors
  Should Not Depend on Each Other."
- **Must not talk to the coordinator except through its own return
  value.** A collector never reaches "up" into the coordinator or the
  snapshot being assembled.
- **Must not let an unexpected bug escape as an unhandled exception.**
  Anticipated failures (missing command, bad permissions, unparseable
  output) are handled inside the collector and turned into data, per the
  Standard Lifecycle below. (The coordinator will also catch anything a
  collector raises anyway, as a last-resort safety net — but that safety
  net existing is not permission to skip a collector's own error handling.)
- **Must not log anything.** NodeIQ does not implement application logging
  in v1 — see `DECISIONS.md` ADR-013. Anything worth knowing about a
  collector's run belongs in its returned errors, not in a log line only a
  developer would see.
- **Must not do presentation work.** No formatting for human reading, no
  natural-language phrasing, no deciding what's "important enough" to
  show — that's `report` (Phase 4) and `ask` (Phase 6)'s job. A collector
  returns facts, not sentences.
- **Must not invent its own secret-redaction scheme.** Which fields need
  redaction and how is a Phase 7 (Robustness) decision — see
  `docs/snapshot_schema.md`'s Open Questions. Scattering ad hoc redaction
  logic across collectors now would make that future decision harder to
  apply consistently.
- **Must not write to the snapshot file.** A collector returns data in
  memory; only the coordinator (eventually the CLI's `scan` command)
  writes the final assembled snapshot to disk.
- **Must not add retries, caching, or other performance optimizations**
  unless a real, observed problem calls for it. Simple and obvious beats
  speculative — see the Quality Check at the end of this document.

---

## Standard Lifecycle

Every collector follows the same four steps, in the same order:

```
collect()  →  run_command()  →  parse  →  validate  →  return structured JSON
```

1. **`collect()`** is the collector's one public entry point — the only
   function anything outside the module ever calls.
2. **`run_command()`** (one or more calls) gathers raw evidence from the
   real system, via `nodeiq.core.runner` — or, for data that lives in a
   file rather than a command's output, a direct file read (see "Two Ways
   to Gather Evidence" below). Either way, this step produces nothing but
   raw text; it decides nothing about what that text means.
3. **Parse** turns that raw text into intermediate Python data (lists,
   dicts, numbers) — see "Separation of Command Execution and Parsing"
   below.
4. **Validate** sanity-checks the parsed data before it's trusted enough
   to return (e.g., "did every filesystem row actually have a percentage
   field").
5. **Return** the finished result through the standard contract below.

### Two Ways to Gather Evidence

Not every collector needs to run an external command. `PROJECT_RULES.md`
Section 9 (item 7) already prefers reading a file directly over parsing a
command's output when a file is available — most commonly, information
under `/proc` (e.g. `/proc/loadavg`, `/proc/meminfo`) is a plain text file
the kernel keeps up to date, not something you need `df` or `top` to ask
for. Both are valid, and a collector picks whichever fits its data source:

- **Running a command** (`ss`, `systemctl`, `crontab -l`, ...) always goes
  through `nodeiq.core.runner.run_command`, never raw `subprocess`.
- **Reading a file** (most `/proc` entries) is plain Python file I/O
  (e.g. `Path("/proc/loadavg").read_text()`) — there's no subprocess
  involved at all, so `run_command` doesn't come into it, but the same
  "catch anticipated failures, never raise" expectation still applies
  (e.g. the file might not exist, or might not be readable).

Either way, the step produces only raw text — parsing it is always a
separate step (see "Separation of Command Execution and Parsing" below).

### The Standard Contract

Every collector module exposes exactly one function:

```python
def collect() -> tuple[dict, list[dict]]:
    """Returns (data, errors).

    `data` matches this collector's section of docs/snapshot_schema.md —
    as fully as could be determined, possibly partially filled if some
    (but not all) of the underlying commands failed.

    `errors` is a list of error-detail dicts (see docs/snapshot_schema.md
    Section 12, collection_errors) — empty if nothing went wrong.
    """
```

Returning a `(data, errors)` tuple — rather than raising an exception for
every anticipated failure — is what lets a collector report "I got most of
this, but here's the one part I couldn't determine" instead of an
all-or-nothing success/failure. This is a deliberate, minimal choice: a
plain tuple of two built-in types, not a new class or framework (see the
Quality Check section).

---

## Separation of Command Execution and Parsing

Gathering raw evidence (running a command, or reading a file) and making
sense of it are two different jobs, and a collector keeps them in two
different functions:

- **Gathering** (calling `run_command`, or reading a file directly) only
  ever produces raw text — a `CommandResult`'s `stdout`, or a file's
  contents. It has no idea what that text *means*.
- **Parsing** turns that raw text into structured data, and knows nothing
  about how the text was obtained — it could just as easily be handed a
  hard-coded string in a test, whether the real text came from a command
  or a file.

Keeping these separate means a parsing function can be tested with a
literal string of sample output, with no subprocess involved at all (see
Testing Expectations below) — and means the same parsing logic could later
be reused if the same information ever became available a different way
(e.g., a future structured/`--json` version of a command), without
touching how the command was run.

---

## Error Handling Expectations

- Check whether each `run_command()` call actually succeeded
  (`CommandResult.succeeded`) before attempting to parse its output.
- Wrap parsing itself in a narrow `try`/`except` for the specific errors
  bad or unexpected input could realistically cause (e.g. `ValueError`,
  `IndexError`, `KeyError`) — not a bare `except Exception` around the
  whole function.
- Every error goes into the `errors` list as a dict shaped like
  `docs/snapshot_schema.md` Section 12's `collection_errors` entries:
  `{"message": str, "severity": "warning" | "error", "exception_type": str | None}`.
- Never conflate "the system genuinely has none of this" with "we
  couldn't determine this." An empty list because there are truly no
  failed services is valid data with no error entry. An empty list because
  `systemctl` timed out is an error entry *and* a `services` section that
  clearly reflects it wasn't actually checked (e.g. via a field like
  `systemd_available`, per `docs/snapshot_schema.md` Section 7).
- When one command among several fails, still return whatever data the
  *other* commands produced, plus one error entry describing what didn't
  work — partial data beats no data, and the error entry ensures nobody
  mistakes the gap for "everything's fine."

---

## JSON Output Expectations

- `data` must be a plain `dict` (or nested dicts/lists of plain values:
  `str`, `int`, `float`, `bool`, `None`) — nothing that `json.dumps` can't
  serialize directly. No custom objects, no `datetime` objects (convert to
  ISO 8601 strings explicitly).
- Field names are `snake_case` and match `docs/snapshot_schema.md` for
  that section exactly — no extra ad hoc fields, no renamed fields. The
  schema is the contract; a collector doesn't get to amend it unilaterally
  (per `docs/data_model_design.md`, "What is a Contract Between Software
  Components").
- If a field's real-world value is genuinely unknown (not zero, not
  empty — actually unknown), prefer `None` and an accompanying error entry
  over guessing a placeholder value.

---

## Helper Function Conventions

- Parsing logic lives in small, private helper functions prefixed with an
  underscore: `_parse_<something>`, e.g. `_parse_df_output`,
  `_parse_systemctl_units`. The underscore is Python's convention for
  "internal to this module" — nothing outside the collector should ever
  import or call one of these directly.
- Prefer one helper per distinct parsing job rather than one large
  function that does everything — small, single-purpose functions, per
  `PROJECT_RULES.md` Section 3.
- Helpers should be **pure functions**: given the same input text, they
  always return the same result, with no side effects (no subprocess
  calls, no file I/O, no network access) — everything they need is passed
  in as an argument. This is what makes them trivially testable (see
  below).
- If validation is non-trivial, it can live in its own
  `_validate_<something>` helper, kept separate from `_parse_<something>`
  for the same reason parsing is kept separate from execution: two
  different jobs, two different functions.

---

## Testing Expectations

- Test every `_parse_*` (and `_validate_*`) helper directly, by passing it
  a literal string of realistic sample output and asserting on the
  structured result. No mocking needed — these are pure functions.
- Test `collect()` itself by replacing `run_command` with a stand-in
  (e.g. `monkeypatch` or `unittest.mock.patch`) that returns a
  hand-constructed `CommandResult`, so tests never depend on the real
  state of the machine running them — matching `PROJECT_RULES.md` Section
  11 and how `tests/core/test_runner.py` already avoids relying on
  Linux-only tools.
- Cover both the happy path (command succeeds, output parses cleanly) and
  failure paths (command missing, non-zero exit, timeout, malformed
  output) for every collector, per `PROJECT_RULES.md` Section 11.
- A collector's tests should never need a real Linux system, real
  `systemctl`, or real `/proc` — if a test can only pass on Ubuntu, it's
  testing the wrong layer (that's what manual verification in the
  Multipass VM is for, per `DECISIONS.md` ADR-002).

---

## Examples (Pseudo-code Only)

The following is illustrative only — no such file exists yet, and none of
this runs. It exists to show how the pieces above fit together, using the
future `disk` collector as a concrete stand-in.

```python
# src/nodeiq/collectors/disk.py  (illustrative — not a real implementation)

from nodeiq.core.runner import run_command


def collect() -> tuple[dict, list[dict]]:
    errors = []

    result = run_command(["df", "-P", "-k"])
    if not result.succeeded:
        errors.append({
            "message": f"df failed: {result.error or result.stderr}",
            "severity": "error",
            "exception_type": None,
        })
        return {"filesystems": []}, errors

    try:
        filesystems = _parse_df_output(result.stdout)
    except ValueError as exc:
        errors.append({
            "message": f"could not parse df output: {exc}",
            "severity": "error",
            "exception_type": type(exc).__name__,
        })
        return {"filesystems": []}, errors

    return {"filesystems": filesystems}, errors


def _parse_df_output(raw_output: str) -> list[dict]:
    """Pure function: df's text table in, a list of filesystem dicts out.
    No subprocess calls, no I/O — just string parsing."""
    ...
```

```python
# tests/collectors/test_disk.py  (illustrative — not a real test file)

def test_parse_df_output_handles_a_normal_row():
    sample = "Filesystem 1024-blocks Used Available Capacity Mounted\n" \
             "/dev/sda1  10000       4000 6000      40%       /\n"
    result = _parse_df_output(sample)
    assert result[0]["mount_point"] == "/"
    assert result[0]["used_percent"] == 40.0


def test_collect_reports_an_error_when_df_is_missing(monkeypatch):
    monkeypatch.setattr("nodeiq.collectors.disk.run_command", _fake_missing_df)
    data, errors = collect()
    assert data == {"filesystems": []}
    assert len(errors) == 1
```

---

## Quality Check

This design was reviewed against the same standard the project holds every
piece of NodeIQ to: is it as simple as it can be while still being
correct?

- **No inheritance hierarchies.** Every collector is a plain module with
  one function, `collect()`. There is no `BaseCollector` class for a
  collector to extend.
- **No abstract base classes.** Nothing in this design requires a
  collector to implement an interface beyond "have a function named
  `collect` with this signature." Python doesn't need an ABC to enforce
  that for eight or so collector modules.
- **No plugin system.** The coordinator (Phase 3.2B) will call each
  collector's `collect()` directly, by import — there's no dynamic
  discovery, registration, or configuration mechanism, because NodeIQ's
  set of collectors is small and known ahead of time, not something users
  add at runtime.
- **No unnecessary framework.** The entire contract is: one function, a
  two-item tuple, and a handful of underscore-prefixed helpers. This is
  practical for all nine planned collectors (`system`, `cpu_memory`,
  `processes`, `disk`, `services`, `logs`, `network`, `scheduled_jobs`,
  `permissions`) without forcing any of them into a shape that doesn't fit
  — a collector that only needs to read one `/proc` file (no parsing of
  command-line tool output at all) still fits this pattern exactly as well
  as one that runs several commands.
