# CLI Design — NodeIQ

**Status:** Design only (Phase 5A). No code exists yet — `src/nodeiq/cli/`
is not created, `pyproject.toml` gains no new entry point, and nothing in
`nodeiq.core`, `nodeiq.summary`, or `nodeiq.report` changes as a result of
this document. This exists so implementation (Phase 5B, presumably)
starts from a reviewed plan, per this project's established "design
before implementation" convention (`docs/process_collector_design.md`,
`docs/summary_engine_design.md`).

Read this alongside [architecture.md](architecture.md) (the execution
layers the CLI sits on top of), [summary_engine_design.md](summary_engine_design.md)
(what `report` and `ask` read), and [report_formatter.md](report_formatter.md)
(what `report` prints). The backend this CLI exposes is otherwise
unchanged: `run_scan()`, `save_snapshot()`, `load_snapshot()`,
`load_latest_snapshot()`, `summarize_snapshot()`, and `format_report()`
all already exist and are already tested — this phase is only about how
a user reaches them from a terminal.

---

## 1. Purpose and Scope

Every piece of NodeIQ's backend is complete and independently verified:
9 collectors, `run_scan()`, snapshot persistence, the Summary Engine,
and the Report Formatter. `dev_summary.py` has proven the whole pipeline
works end to end, but it is a fixed, non-configurable developer script —
it always scans, always saves, always summarizes, always prints the
full report, with no way to ask a question, re-read an old snapshot, or
look at just one section.

The production CLI's job is to expose exactly what already exists —
`scan`, `report`, `ask` — as three real subcommands, cleanly, with no
new business logic invented at this layer. Every decision "what counts
as healthy," "how does this look formatted," and (later, Phase 6) "how
does the LLM answer" already belongs to a lower layer; the CLI only
parses arguments, calls the right functions in the right order, and
prints or exits appropriately.

This document designs the CLI. It does not implement it, and it does
not touch Phase 6 (real LLM wiring) beyond describing the shape `ask`
needs to fit around it later.

---

## 2. Guiding Principle: The CLI Is a Thin Orchestration Layer

Every command below is describable as "parse arguments, call 1–4
already-existing functions in order, print their result, choose an exit
code." None of the three commands compute a status, format a number, or
decide what's noteworthy — that would duplicate work `nodeiq.summary`
and `nodeiq.report` already do. This mirrors a pattern used at every
other layer of this project: collectors don't do presentation work,
the Summary Engine doesn't gather its own facts, the Report Formatter
doesn't summarize. The CLI is the fourth application of the same "one
layer, one job" discipline, applied at the outermost boundary this time.

Concretely, this means:

- `scan` calls `run_scan()` and `save_snapshot()` — nothing else exists
  yet for it to call.
- `report` calls `load_latest_snapshot()` (or `load_snapshot(path)`),
  `summarize_snapshot()`, and `format_report()` — in that order, every
  time.
- `ask` calls the same snapshot-loading functions, plus (optionally)
  `run_scan()`/`save_snapshot()` first for `--fresh`, then hands the
  evidence to a Phase 6 LLM-interpretation function not yet built.

The one piece of CLI-specific logic this design does introduce —
filtering `report --section disk` down to one section — is deliberately
kept as plain dict filtering at the CLI layer (see Section 4.2), not a
new parameter threaded into `nodeiq.summary` or `nodeiq.report`. Both of
those modules already work on an arbitrary subset of sections without
any change, which is a direct payoff of `format_report()`'s existing
"iterate whatever `summary['sections']` has, no hardcoded list" design
(`docs/report_formatter.md`).

---

## 3. Entry Point

`README.md`'s own Phase-5 forward-reference already anticipates
`python -m nodeiq scan` as the invocation style (see its "(Future) Run a
scan" example) — this design follows that precedent rather than
introducing a competing convention. Concretely:

- `src/nodeiq/__main__.py` — lets `python -m nodeiq <command>` work,
  delegating immediately to the CLI's argument parser.
- `src/nodeiq/cli/` (already reserved, empty, in
  `PROJECT_RULES.md` Section 1's folder structure) — holds the argparse
  setup and one small dispatch function per command.

A `[project.scripts]` entry in `pyproject.toml` (so an editable install
would additionally let a user type bare `nodeiq scan` instead of
`python -m nodeiq scan`) is a trivial, low-risk addition on top of this
— but not required for v1, and left as an explicit open question
(Section 9) rather than assumed.

Per `DECISIONS.md` ADR-004, argument parsing uses `argparse`'s
subparsers — one subparser per command, dispatching to a small handler
function. Illustrative sketch (not implementation):

```python
parser = argparse.ArgumentParser(prog="nodeiq")
subparsers = parser.add_subparsers(dest="command", required=True)

scan_parser = subparsers.add_parser("scan")

report_parser = subparsers.add_parser("report")
report_parser.add_argument("--section")
report_parser.add_argument("--snapshot")

ask_parser = subparsers.add_parser("ask")
ask_parser.add_argument("question")
ask_group = ask_parser.add_mutually_exclusive_group()
ask_group.add_argument("--snapshot")
ask_group.add_argument("--fresh", action="store_true")
```

`--snapshot` and `--fresh` are mutually exclusive by construction
("read this specific file" and "scan again first" are contradictory
requests) — argparse rejects passing both automatically, with its own
standard "invalid arguments" behavior (Section 5.4), so no custom
validation code is needed for that case.

---

## 4. Command Reference

### 4.1 `nodeiq scan`

| | |
|---|---|
| **Syntax** | `nodeiq scan` |
| **Arguments** | none |
| **Flags** | none proposed for v1 (see Section 9 for a considered-but-deferred `--quiet`) |
| **Exit codes** | `0` success (including partial collector failure — see below); `4` if `save_snapshot()` itself fails (Section 5) |

**Expected behavior:** calls `run_scan()`, then `save_snapshot(snapshot)`,
then prints a short confirmation (Section 6.1). Nothing about `scan` is
new logic — it is the exact two-line sequence `docs/snapshot_persistence.md`
already documents as the intended usage, now reachable from a terminal.

**Interaction with snapshots:** writes exactly one new snapshot file to
`snapshots/`, via the existing, unchanged `save_snapshot()`.

**Interaction with the Summary Engine:** none. `scan` never summarizes —
that's `report`'s job, and CONTEXT.md's `scan → report → ask` pipeline
already keeps these as separate steps for a reason (a snapshot is a
reusable artifact independent of whether it's ever summarized).

**Interaction with OpenAI:** none.

**A key distinction this command's exit code must respect:** one or
more *individual collectors* failing (e.g. `systemctl` missing) is
normal, expected, and already handled — it's recorded in
`collection_errors` and the scan still completes successfully
(`PROJECT_RULES.md` Section 7). That is not a `scan` command failure and
must not produce a non-zero exit code. A genuine `scan` command failure
is a different, narrower thing: `run_scan()` itself raising (which its
own last-resort safety net should already prevent — `docs/coordinator.md`)
or `save_snapshot()` failing for a real OS-level reason (disk full,
permission denied writing to `snapshots/`). Only those should exit
non-zero.

### 4.2 `nodeiq report`

| | |
|---|---|
| **Syntax** | `nodeiq report [--snapshot PATH] [--section NAME]` |
| **Arguments** | none positional |
| **Flags** | `--snapshot PATH` (load a specific snapshot file instead of the latest); `--section NAME` (print only one section) |
| **Exit codes** | `0` success; `1` no usable snapshot (Section 5.1/5.2); `2` invalid arguments (Section 5.5) |

**Expected behavior:** loads a snapshot (`load_latest_snapshot()` by
default, or `load_snapshot(path)` if `--snapshot` is given), calls
`summarize_snapshot(snapshot)`, optionally filters the result to one
section (below), calls `format_report(summary)`, and prints the result
verbatim — no extra header/footer beyond what `format_report()` already
produces, keeping `report` a thin pass-through.

**`--section NAME` behavior:** the CLI validates `NAME` against the
Summary's own `sections` keys (not a separate hardcoded list — reading
`summary["sections"].keys()` after summarization already gives the
authoritative, current set) and, if valid, replaces `summary["sections"]`
with a one-entry dict containing just that section before calling
`format_report()`. An unrecognized name (e.g. `--section disk_typo`) is
reported as an invalid-argument error (Section 5.5), listing the valid
names, rather than silently printing nothing. This filtering is plain
dict manipulation at the CLI layer — neither `nodeiq.summary` nor
`nodeiq.report` needs a new parameter, since `format_report()` already
renders whatever subset of sections it's given.

**Interaction with snapshots:** read-only. `report` never writes
anything — it only ever reads a snapshot file, per CONTEXT.md's
non-negotiable snapshot-first rule ("`report` and `ask` never talk to
the live system directly").

**Interaction with the Summary Engine:** calls `summarize_snapshot()`
exactly once per invocation, unconditionally — every `report` run
recomputes the Summary from the loaded snapshot rather than caching one,
consistent with `docs/summary_engine_design.md` Section 15's
"regenerate, don't persist" lean (still an open question there, not
re-litigated here).

**Interaction with OpenAI:** none.

### 4.3 `nodeiq ask "question"`

| | |
|---|---|
| **Syntax** | `nodeiq ask [--snapshot PATH \| --fresh] "question"` |
| **Arguments** | `question` (required, positional, free-text — the user quotes it in their shell) |
| **Flags** | `--snapshot PATH` (ask against a specific snapshot); `--fresh` (scan first, then ask against that new snapshot) — mutually exclusive with each other |
| **Exit codes** | `0` success; `1` no usable snapshot; `2` invalid arguments; `3` OpenAI/LLM unavailable; `4` unexpected internal failure |

**Expected behavior:** resolves which snapshot to use — `--fresh` runs
`run_scan()` + `save_snapshot()` first and uses that result; `--snapshot
PATH` loads that specific file; the default (neither flag) is
`load_latest_snapshot()` — then hands the evidence and the question to
Phase 6's not-yet-built LLM-interpretation function, and prints its
answer.

**On `--fresh` and the snapshot-first rule:** `--fresh` does not give
`ask` any new ability to talk to the live system. It orchestrates two
already-existing, already-safe pieces at the CLI layer — first `scan`'s
own sequence (`run_scan()` → `save_snapshot()`), then `ask`'s normal
load-a-snapshot-and-interpret flow, applied to the snapshot that scan
just produced. `ask` itself still only ever reads a snapshot dict; it
never gains a code path to a collector or `subprocess` directly. This is
the same distinction CONTEXT.md Section 2 already draws between Layer 1
(collection) and Layer 2 (interpretation) — `--fresh` composes both
layers through the CLI, it does not blur them.

**Interaction with snapshots:** read-only in the default and
`--snapshot` cases; read-and-write in the `--fresh` case (via the same
`scan` sequence, reused rather than reimplemented).

**Interaction with the Summary Engine:** genuinely open — Question 1 in
`docs/summary_engine_design.md` Section 17 ("should `ask` consume only
the Summary, only the raw snapshot, or both depending on the question")
is a Phase 6 design decision this document does not resolve. Whatever
that decision turns out to be, the CLI's shape here is stable: `ask`
loads a snapshot, hands it (and/or its Summary) to one Phase 6 function,
and prints whatever text comes back — the CLI does not need to know
which evidence shape that function ultimately wants.

**Interaction with OpenAI:** the entire point of this command. Per
CONTEXT.md Section 4 and `DECISIONS.md` ADR-005/ADR-008: the API key is
read from `.env` via `python-dotenv` (already decided, not implemented
yet); the LLM receives only the evidence already in the snapshot/Summary
plus the user's question; it never executes commands and never answers
from outside that evidence. If evidence is missing (a `collection_errors`
entry, or a section reporting `status: "unknown"`), the answer must say
so rather than guess — this is an existing, non-negotiable rule the CLI
doesn't need to enforce itself, since it's a property of what gets
handed to the LLM, not of the CLI's argument parsing.

---

## 5. Error Handling

**General approach:** the CLI is the outermost boundary — every
exception a lower layer can raise (`SnapshotError` today; an LLM-layer
error in Phase 6) is caught at this one layer, translated into a short,
specific, user-facing message on `stderr`, and mapped to one of a small,
fixed set of exit codes. No raw Python traceback should reach a user by
default. This is the same "boundary translates, internals raise
specifically" discipline `PROJECT_RULES.md` Section 7 already applies
one layer down (collectors never raise; the coordinator's own
last-resort net exists so a bug can't crash a scan) — applied here one
layer further out, where user-facing clarity matters even more.

### 5.1 Snapshot not found

`load_latest_snapshot()` raises `SnapshotError` when `snapshots/` is
missing or empty (already implemented, unchanged — `snapshot.py`).
`report`/`ask` (without `--fresh`) catch this and print something like:

```
No snapshot found. Run `nodeiq scan` first.
```

Exit code `1`.

### 5.2 Malformed snapshot

`load_snapshot()`/`load_latest_snapshot()` raise `SnapshotError` for a
file that isn't valid JSON or doesn't look like a snapshot (missing
`metadata`) — already implemented, unchanged. Caught the same way as
5.1, printing `SnapshotError`'s own message (already specific — e.g.
`"snapshot <path> is not valid JSON: ..."`) rather than a generic one.
Exit code `1` — the same code as "not found," since both mean "there is
no usable snapshot to proceed with," a distinction the exit code itself
doesn't need to carry (the printed message already differs).

### 5.3 OpenAI unavailable

Covers a missing/invalid API key, a network failure, a timeout, or a
rate limit — all "the external LLM service didn't answer," a
categorically different failure from "no snapshot" (5.1/5.2). This
needs a Phase 6 exception (naming TBD — likely `LLMError` in
`nodeiq.core.exceptions`, alongside `SnapshotError`, following the exact
same pattern) that `ask` catches and reports as:

```
Could not reach OpenAI: <specific, non-sensitive reason>.
```

Never printing the API key or raw provider-internal exception details
(`PROJECT_RULES.md` Section 8 — no secrets logged, extended here to "no
secrets printed"). Exit code `3`.

### 5.4 Scan failure

As established in Section 4.1: individual collector failures are not
scan failures and never affect `scan`'s exit code. A genuine failure —
`run_scan()` itself raising unexpectedly, or `save_snapshot()` hitting a
real OS error — is caught at the CLI boundary and printed plainly (e.g.
`"Could not save snapshot: <reason>."`). Exit code `4`.

### 5.5 Invalid arguments

Handled entirely by `argparse` itself — an unknown flag, a missing
required `question`, or (per Section 3) passing both `--snapshot` and
`--fresh` together all already produce a clear usage message on `stderr`
and argparse's own conventional exit code, `2`, with zero custom code
needed. This is worth stating explicitly: "invalid arguments" is not a
case this design has to build anything for.

### Exit Code Summary

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | No usable snapshot (not found or malformed) |
| `2` | Invalid arguments (argparse's own default) |
| `3` | OpenAI/LLM unavailable (`ask` only) |
| `4` | Unexpected internal failure (`run_scan()`/`save_snapshot()` crash) |

This exact scheme (which codes exist, and which numbers) is proposed,
not final — flagged explicitly in Section 9 as something the project
owner should confirm before Phase 5B implementation, since an exit-code
contract is worth deliberate sign-off rather than being guessed once and
left unquestioned.

---

## 6. Output

### 6.1 `scan`

```
Scan complete: 9/9 collectors succeeded.
Snapshot saved to: snapshots/snapshot_20260716T090000000000.json
```

Or, with partial collector failure (still exit code `0`):

```
Scan complete: 7/9 collectors succeeded (2 errors — see snapshot for details).
Snapshot saved to: snapshots/snapshot_20260716T090000000000.json
```

Both counts come directly from the snapshot's own `metadata` and
`collection_errors` fields — no new computation, just reading numbers
that already exist.

### 6.2 `report` (and `report --section NAME`)

Exactly `format_report()`'s own output, printed verbatim — see
`docs/report_formatter.md`'s "Report Shape" section for a full example.
`--section NAME` produces the same visual shape, just with only that one
section's block present, since the CLI filters the Summary before
formatting rather than changing how formatting itself works.

### 6.3 `ask`

Prints the LLM's answer text — exact formatting (whether to echo the
question back, whether to cite which snapshot/timestamp was used) is
deliberately left to Phase 6 (Section 9), since it depends on how that
phase decides to prompt and structure a response. At minimum, the
answer should be printed as plain, undecorated text — consistent with
`report`'s "just print already-computed text" philosophy, and friendly
to scripting/piping.

---

## 7. Complete User Flow

A first-time user, after `pip install -e .` (already the documented
one-time setup step — see `LOGS.md`'s packaging-fix entry):

```
$ python -m nodeiq scan
Scan complete: 9/9 collectors succeeded.
Snapshot saved to: snapshots/snapshot_20260716T090000000000.json

$ python -m nodeiq report
======================================================================
NodeIQ Report
Host: main-cattle
Snapshot: 2026-07-16T09:00:00.000000+00:00
======================================================================

System [HEALTHY]
Ubuntu 24.04.4 LTS, kernel 6.8.0-134-generic, up 6h 21m
  ...

$ python -m nodeiq report --section disk
======================================================================
NodeIQ Report
Host: main-cattle
Snapshot: 2026-07-16T09:00:00.000000+00:00
======================================================================

Disk [HEALTHY]
Fullest filesystem at 60.0%
  - 8 filesystem(s) checked

$ python -m nodeiq ask "What service failed?"
No services have failed. 54 services are currently running.

$ python -m nodeiq ask --fresh "Is memory usage a concern right now?"
Scan complete: 9/9 collectors succeeded.
Memory usage is at 24.5%, well below any concerning threshold.
```

(`ask`'s exact answer text is illustrative — Phase 6 decides the real
prompting/response shape. Note `ask --fresh` printing the same scan
confirmation line as a standalone `scan` would — reusing that command's
own output is simpler and more consistent than inventing a different
message for the same underlying action, though this is listed as an
open question in Section 9 in case a quieter `--fresh` is preferred.)

---

## 8. Future Extensibility

- **A new snapshot section** (a 10th collector, someday) needs zero CLI
  changes to appear in `report`'s output or become a valid `--section`
  value — both already read the Summary's actual keys rather than a
  hardcoded list (Section 4.2). This is the same "add one collector, one
  summarizer, done" ergonomics already established at the two layers
  below the CLI, now proven to reach all the way up to the user-facing
  surface.
- **`report --format json`** (print the raw Summary as JSON instead of
  formatted text, for scripting) is a small, additive flag that could be
  added later without changing existing behavior — not proposed for v1,
  since no current consumer needs it.
- **More subcommands** (`nodeiq history`, `nodeiq diff` — both already
  listed as unscheduled "Future Roadmap" items in CONTEXT.md Section 9)
  fit naturally as additional `argparse` subparsers, per ADR-004's whole
  rationale for choosing subparsers in the first place.
- **A `[project.scripts]` entry point** (Section 3) so `nodeiq scan`
  works without the `python -m` prefix is a packaging-only addition, not
  an argument-parsing change.

---

## 9. Open Questions

Recorded explicitly, per this project's practice of writing down a
genuine unresolved tension rather than guessing at a confident answer:

1. **Exact exit code numbers** (Section 5's summary table) are proposed,
   not confirmed — the project owner should sign off on this scheme (or
   propose a different one) before Phase 5B implementation.
2. **Should `report` also support `--fresh`**, for symmetry with `ask
   --fresh`? Not proposed here, since CONTEXT.md's own pipeline diagram
   treats `report` as strictly read-only, and no requirement mentioned
   it — but the asymmetry (only `ask` can trigger a scan) is worth the
   project owner confirming is intentional.
3. **Should `scan` support a `--quiet` flag** (suppressing the
   confirmation output, for future cron/scheduled-scan use per
   CONTEXT.md Section 9's Future Roadmap)? Plausible, but no current
   consumer needs it yet — deferred rather than speculatively added.
4. **`ask --fresh`'s exact output** (Section 7's note): should it print
   `scan`'s own confirmation line before the answer, print nothing extra
   about the scan, or something in between? Left to Phase 6, since it
   depends on how that phase structures `ask`'s overall output.
5. **The Phase 6 LLM-interpretation function's exact signature** (what
   it takes — snapshot, Summary, or both; what it returns) is
   deliberately not designed here — this document only commits to "the
   CLI hands it evidence and a question, and prints back text," which
   holds regardless of how Phase 6 resolves `docs/summary_engine_design.md`
   Section 17's still-open Question 1.
6. **Whether a `[project.scripts]` console-script entry point should be
   added now or deferred** (Section 3) — a genuine "nice to have, not
   required" call, not made here.

---

## 10. Quality Review

Applying the same three-question test used in every prior design/review
in this project (`docs/collector_guidelines.md`, `docs/summary_engine_design.md`
Section 18):

- **Does each proposed structure simplify the code, or add ceremony?**
  Three subparsers, three thin handler functions, and one small dict
  filter for `--section` is the entire proposed surface — no command
  base class, no plugin registry for subcommands, no configuration
  file. A `CliContext` object (mirroring `CollectorContext`) was
  considered and rejected: unlike `CollectorContext`, which solved two
  concrete, current problems (shared timeout, shared scan-start time),
  no shared parameter across `scan`/`report`/`ask` has been identified —
  inventing one now would be exactly the kind of speculative structure
  this project's quality reviews have rejected before.
- **Is each choice based on real evidence, or a guess?** The
  `--section` filtering approach is based on a real, already-verified
  property of `format_report()` (it already renders an arbitrary subset
  of sections correctly, per its own test suite) — not an assumption.
  Where evidence doesn't exist yet (exact exit codes, whether `report`
  needs `--fresh`), Section 9 records that honestly rather than
  asserting a confident guess.
- **Would this decision still make sense with far less at stake** (a
  smaller version of this problem)? The "no CLI framework beyond
  argparse, no command class hierarchy" choice is explicitly this
  project's existing ADR-004 decision, not reopened here — with only 3
  commands, plain subparsers plus 3 functions is already the simplest
  structure that satisfies the requirement.

No abstraction proposed in this document failed this review; the one
speculative idea considered (a shared `CliContext`) was identified and
explicitly rejected rather than included "just in case."
