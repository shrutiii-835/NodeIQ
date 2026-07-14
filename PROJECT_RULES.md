# PROJECT_RULES.md — NodeIQ Engineering Standards

This document defines the permanent engineering standards for NodeIQ. It is
intentionally generic — every future task, in every future phase, should be
able to follow these rules without needing new ones invented per-task.

For *why* the project is built this way, see [CONTEXT.md](CONTEXT.md). This
document covers *how* we write and organize the code.

---

## 1. Project Folder Structure

```
NodeIQ/
├── README.md
├── CONTEXT.md
├── PROJECT_RULES.md
├── LOGS.md
├── requirements.txt
├── .gitignore
├── docs/                     # design notes, JSON schema docs, diagrams
├── snapshots/                # JSON snapshots produced by `nodeiq scan` (gitignored)
├── src/
│   └── nodeiq/               # the installable Python package
│       ├── collectors/       # one module per collector (Phase 3+)
│       ├── cli/              # CLI entry points and command wiring (Phase 5+)
│       ├── llm/              # LLM integration (Phase 6+)
│       └── models/           # data model / schema definitions (Phase 2+)
└── tests/                    # automated tests, mirroring src/nodeiq structure
```

Notes:

- `src/nodeiq/` uses a "src layout" — this avoids accidentally importing the
  package from the current directory instead of the installed version, a
  common source of confusing bugs.
- Subfolders under `src/nodeiq/` (`collectors/`, `cli/`, `llm/`, `models/`)
  are created when the phase that needs them begins — we don't create empty
  scaffolding ahead of time.
- `snapshots/*.json` is gitignored: snapshots contain real system data from
  whoever ran a scan and should not be committed by default.

---

## 2. Naming Conventions

- Python modules and packages: `lowercase_with_underscores`.
- Classes: `PascalCase`.
- Functions and variables: `lowercase_with_underscores`.
- Constants: `UPPER_CASE_WITH_UNDERSCORES`.
- Collector modules are named after what they collect, e.g. `disk.py`,
  `services.py`, `network.py` — the filename should match the snapshot key
  it produces.
- Test files: `test_<module_name>.py`, mirroring the module under test.

---

## 3. Python Coding Style

- Target Python 3.10+ (for modern type hint syntax like `str | None`).
- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Prefer standard library over third-party dependencies. Only add a
  dependency when the standard library genuinely can't do the job well.
- Favor small, single-purpose functions over large multi-purpose ones.
- Favor explicit code over "clever" code — if a reader has to pause to
  figure out what a line does, prefer a more verbose but obvious version.
- No global mutable state. Pass data explicitly between functions.

---

## 4. Type Hint Expectations

- All function signatures (parameters and return types) must have type
  hints. This project is meant to be a learning tool as well as a working
  tool, and type hints document intent clearly.
- Use `Optional[X]` (or `X | None`) explicitly rather than leaving an
  implicit `None` default unannotated.
- Use `TypedDict` or `dataclasses` (introduced in Phase 2 — Data Model) to
  describe the shape of snapshot data, rather than passing around untyped
  `dict`s wherever practical.

---

## 5. Docstring Standards

- Every module, class, and public function has a docstring.
- Docstring style: short one-line summary, blank line, then (if useful) more
  detail — what it does, why it exists, and any non-obvious behavior.
- Because the project owner is learning Linux systems programming and CLI
  development, docstrings for collectors should briefly explain **what
  system concept is being collected and why it matters operationally** —
  not just restate the function name.

Example:

```python
def collect_disk_usage() -> DiskInfo:
    """Collect filesystem disk usage for all mounted filesystems.

    Runs `df` to find how full each mounted filesystem is. Disk usage is one
    of the most common causes of service failures on a server (a full disk
    can silently break logging, databases, and package installs), so this is
    one of the first things NodeIQ checks.
    """
```

---

## 6. Import Ordering

Group imports in this order, with a blank line between groups:

1. Standard library imports (e.g. `subprocess`, `json`, `pathlib`)
2. Third-party imports (e.g. `click`, `pydantic`)
3. Local application imports (e.g. `from nodeiq.collectors import disk`)

Within each group, sort alphabetically.

---

## 7. Error Handling Philosophy

- **A collector must never raise an unhandled exception.** Every collector
  wraps its own logic in error handling and reports failure as data, not as
  a crash.
- Prefer catching specific exceptions (e.g. `subprocess.TimeoutExpired`,
  `FileNotFoundError`, `PermissionError`) over bare `except Exception`,
  except at the single outermost boundary of a collector, whose job is
  specifically to guarantee the scan continues no matter what goes wrong
  inside it.
- Errors are recorded in the snapshot's `collection_errors` field, keyed by
  collector name, with a human-readable message. Never fail silently and
  never fail loudly by crashing the whole scan.
- Distinguish "the system has none of this" (e.g., no cron jobs configured)
  from "we couldn't check" (e.g., permission denied reading crontab) — these
  must never be conflated in the data.

---

## 8. Logging Philosophy

- Use Python's standard `logging` module — not `print()` — for anything
  that isn't the actual CLI output the user asked for.
- Collectors log at `DEBUG` for routine operational detail (e.g., "running
  command: df -h") and `WARNING` when a collector fails but the scan
  continues.
- CLI-level user-facing output (the actual report, the actual answer to a
  question) is printed directly — logging is for diagnosing NodeIQ itself,
  not for talking to the user.
- No logging of secrets, credentials, or full raw command output at a level
  the user would see by default.

---

## 9. Collector Implementation Guidelines

Every collector must:

1. Live in its own module under `src/nodeiq/collectors/`.
2. Expose one clear entry-point function (e.g. `collect() -> dict`).
3. Return structured data matching its documented schema (see `docs/`).
4. Catch all of its own errors and never propagate an exception to the
   scan coordinator.
5. Report errors distinctly from data (see Section 7).
6. Not call or depend on any other collector. Collectors are independent
   and can run in any order.
7. Avoid parsing fragile command output when a more structured source is
   available (e.g., prefer reading `/proc` files directly over parsing
   `top` output, where practical).
8. Apply a timeout to any subprocess call, so a hung command can never hang
   the whole scan (see Phase 7 — Robustness).

---

## 10. JSON Schema Conventions

- Every snapshot is a single JSON object with the top-level keys defined in
  `CONTEXT.md` Section 7 (`timestamp`, `hostname`, `metadata`, `system`,
  `cpu_memory`, `processes`, `disk`, `services`, `logs`, `network`,
  `scheduled_jobs`, `permissions`, `collection_errors`).
- Keys are `snake_case`, matching Python naming conventions.
- Timestamps are ISO 8601 strings in UTC.
- Every collector's section documents its own sub-schema in `docs/`.
- Prefer flat, explicit structures over deeply nested ones, so a human can
  read a snapshot directly and understand it.
- `collection_errors` is a dict keyed by collector name, with values
  describing what went wrong (never just `true`/`false`).

---

## 11. Testing Philosophy

- Every collector gets unit tests that mock subprocess/file-system calls —
  tests must not depend on the real state of the machine they run on, since
  that state is unpredictable and untestable.
- Test both the "happy path" (command succeeds, output parses cleanly) and
  failure paths (command missing, times out, returns unexpected output,
  permission denied).
- CLI commands get integration-style tests that run against a fixture
  snapshot file, not a live system.
- Prefer `pytest` for the test runner (added as a dependency when Phase 8
  begins, kept out of `requirements.txt` until then to honor "minimal
  dependencies" during earlier phases — or added early as a dev-only
  dependency if needed sooner; use judgment and note the decision in
  `LOGS.md`).

---

## 12. Git Workflow

- Commit frequently, in small, logical units — after each significant,
  verified, completed task.
- **Claude (the AI assistant) creates a git commit after every significant,
  verified, completed task**, using the commit message conventions in
  Section 13. This updates the project's original Phase 1 rule; see
  [DECISIONS.md](DECISIONS.md) ADR-011 for the full reasoning and the
  supersession record.
- Claude **never runs `git push`.** Pushing to any remote is performed
  manually by the project owner unless they explicitly ask otherwise.
- "Verified" means the task's Definition of Done (Section 17) is actually
  satisfied — do not commit partial or unverified work.
- **Git commits must never include AI co-author trailers or AI
  attribution.** Use only the configured Git user identity. This is a
  personal portfolio project, and the git history must reflect the
  project owner's authorship alone — no `Co-authored-by: Claude`,
  `Co-authored-by: Anthropic`, or similar trailer, in any commit.

---

## 13. Commit Message Conventions

Use short, imperative-mood summaries, optionally with a longer body:

```
<type>: <short summary>

<optional longer explanation of why, not just what>
```

Suggested `<type>` values: `feat`, `fix`, `docs`, `refactor`, `test`,
`chore`.

Example:

```
feat: add disk usage collector

Collects df output for all mounted filesystems and flags any filesystem
over 90% full, since disk exhaustion is a common root cause of service
failures.
```

---

## 14. Documentation Standards

- `README.md` is public-facing — keep it accurate and welcoming to a new
  reader who knows nothing about the project yet.
- `CONTEXT.md` is the permanent architectural record — update it only when
  the architecture or philosophy actually changes.
- `PROJECT_RULES.md` (this file) is the permanent standards record — update
  it only when a standard actually changes project-wide.
- `LOGS.md` is append-only — never rewrite history, only add new entries.
- `CHECKLIST.md` is the living, phase-by-phase progress tracker — check off
  tasks as they're verified done and keep its Progress Summary in sync.
- `DECISIONS.md` is the Architecture Decision Record — add a new ADR for
  every architectural decision made or changed; never edit a past decision
  away, supersede it instead (Section 12).
- `ROADMAP.md` is the high-level milestone view — update it when milestones
  are completed, added, or reordered.
- `LEARNING_NOTES.md` grows every session — add a beginner-friendly
  explanation of every important new concept introduced by that session's
  work.
- Any new non-trivial design decision (e.g., a JSON schema for a new
  collector) gets a short doc under `docs/`.

---

## 15. Future Contributors Guide

If someone new (human or AI) picks up this project:

1. Read `CONTEXT.md` first, in full, before writing any code.
2. Read this file (`PROJECT_RULES.md`) next.
3. Skim `LOGS.md` to understand what's already been built and why, and
   `DECISIONS.md` to understand what was decided and why.
4. Check `CHECKLIST.md` and `ROADMAP.md` to see which phase the project is
   currently in (also recorded in `CONTEXT.md` Section 8) — do not start
   work on a later phase before earlier phases are done.
5. Skim `LEARNING_NOTES.md` if you're new to any of the Linux/CLI/Python
   concepts involved — it exists precisely so you don't have to
   re-research the basics mid-task.
6. Follow the conventions in this document exactly; if a convention seems
   wrong for a specific case, raise it with the project owner rather than
   silently deviating.

---

## 16. Project Maintenance

Claude is responsible for maintaining the project's documentation and
development workflow, not just writing code. Whenever a significant task is
completed, Claude:

1. Updates `LOGS.md` by **appending** a new entry (never rewriting history).
2. Updates `CHECKLIST.md` — checks off completed tasks and adds any newly
   discovered ones, keeping the Progress Summary in sync with the
   checkboxes.
3. Updates `DECISIONS.md` if an architectural decision was made or changed
   (adding a new ADR — see Section 12 on superseding rather than editing
   old decisions away).
4. Updates `ROADMAP.md` if milestones shifted, completed, or were added.
5. Updates `LEARNING_NOTES.md` with beginner-friendly explanations of every
   important new concept introduced during that task.
6. Performs a git commit with a meaningful message once the task is
   complete and verified (Section 12).
7. Ends the session with: a summary, the files changed, which documentation
   files were updated, the git commit hash and message, and a recommended
   next task.

This keeps `README.md`, `CONTEXT.md`, `PROJECT_RULES.md`, `LOGS.md`,
`CHECKLIST.md`, `DECISIONS.md`, `ROADMAP.md`, and `LEARNING_NOTES.md` all
accurate and current across many separate development sessions, so no
session has to start by reverse-engineering what happened in the last one.

---

## 17. Definition of Done

A task is only "done" when **all** of the following are true:

- [ ] Code follows the style, naming, and type-hint conventions above.
- [ ] Every new function/class/module has a docstring.
- [ ] Error handling follows Section 7 (collectors never crash the scan).
- [ ] No secrets or raw sensitive data are logged or stored unredacted.
- [ ] Relevant tests are written and passing (once Phase 8 tooling exists;
      earlier phases should still include basic sanity checks where
      practical).
- [ ] `LOGS.md` has a new entry describing the task (date, task, files
      created/modified, reasoning, notes, future TODOs).
- [ ] `CHECKLIST.md`, `DECISIONS.md` (if applicable), `ROADMAP.md` (if
      applicable), and `LEARNING_NOTES.md` are updated per Section 16.
- [ ] `README.md` / `CONTEXT.md` / `docs/` are updated if the change affects
      what a reader of those files would need to know.
- [ ] A git commit has been made by Claude (Section 12); no push has been
      performed unless explicitly requested.
