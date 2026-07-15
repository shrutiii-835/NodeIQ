# LOGS.md — NodeIQ Development Diary

This file is an **append-only** record of development work on NodeIQ. Never
edit or delete previous entries — only add new ones at the bottom. This is
the project's institutional memory across sessions.

---

## 2026-07-14 — Project Initialization

**Task**

Initialize the NodeIQ repository: create the folder structure and populate
the core documentation files (`README.md`, `CONTEXT.md`, `PROJECT_RULES.md`,
`LOGS.md`), plus `requirements.txt` and `.gitignore`. No Python modules,
collectors, or CLI code were written — this is Phase 1 (Project
architecture) only.

**Files created**

- `README.md`
- `CONTEXT.md`
- `PROJECT_RULES.md`
- `LOGS.md` (this file)
- `requirements.txt` (empty)
- `.gitignore`
- `docs/` (empty directory)
- `snapshots/` (empty directory)
- `src/nodeiq/` (empty package directory)
- `tests/` (empty directory)

**Files modified**

None — this was the first commit-worthy state of the repository.

**Reasoning**

The project specification requires a snapshot-first, two-layer architecture
(collection, then AI interpretation) built in strict, incremental phases,
with permanent documentation maintained throughout. Before any code is
written, the project needs:

- A clear, durable statement of *why* the project is built this way
  (`CONTEXT.md`), so future sessions don't have to re-derive the
  architecture from scratch or drift from it.
- A clear, durable statement of *how* code should be written
  (`PROJECT_RULES.md`), so style and structure stay consistent across many
  sessions and possibly multiple contributors.
- A public-facing overview (`README.md`) for anyone encountering the project
  from the outside.
- An append-only diary (`LOGS.md`) so future sessions can see what's been
  done and why without re-reading every prior conversation.

The folder structure follows a standard Python "src layout"
(`src/nodeiq/`), which keeps the installable package separate from
top-level project files and avoids accidental local-import bugs later.
Subfolders inside `src/nodeiq/` (e.g. `collectors/`, `cli/`, `llm/`,
`models/`) were intentionally **not** created yet — they'll be added when
the phase that needs them (Phase 2 onward) actually begins, per the
project's principle of not building ahead of need.

**Important implementation notes**

- `requirements.txt` was left empty, per instructions — no dependencies
  have been chosen yet.
- `.gitignore` excludes `__pycache__/`, `*.pyc`, `.env`, `.venv/`, and
  `snapshots/*.json` — snapshots contain real system data and should not be
  committed by default.
- No git commit or push was performed — per project rules, all git
  operations are performed manually by the project owner.

**Future TODOs**

- Phase 2: design the snapshot JSON schema (data model) and document it in
  `docs/`.
- Decide on the CLI framework (e.g. `argparse` vs. `click`) when Phase 5
  begins — not yet decided.
- Decide on the LLM provider/SDK when Phase 6 begins — not yet decided.

---

## 2026-07-14 — Project Operating Rules, Extended Documentation Set, and First Git Commit

**Task**

Adopt new, permanent project operating rules for ongoing documentation and
git maintenance, create four new permanent documentation files
(`CHECKLIST.md`, `DECISIONS.md`, `ROADMAP.md`, `LEARNING_NOTES.md`), update
`README.md` and `PROJECT_RULES.md` to match, record 11 initial architecture
decisions, and initialize the git repository with its first commit. Still
Phase 1 (Project architecture) — no application code was written.

**Files created**

- `CHECKLIST.md`
- `DECISIONS.md`
- `ROADMAP.md`
- `LEARNING_NOTES.md`

**Files modified**

- `README.md` — added a "Project Documentation" section linking to every
  permanent doc file.
- `PROJECT_RULES.md` — updated Section 12 (Git Workflow) to reflect that
  Claude now commits after each verified task (see ADR-011 below); added a
  new Section 16, "Project Maintenance," describing the ongoing
  documentation/workflow responsibilities; renumbered the old Section 16
  ("Definition of Done") to Section 17 and updated it to reference the new
  maintenance duties; updated Sections 14 and 15 to reference the new doc
  files.

**Reasoning**

The project is explicitly meant to span many development sessions, so from
this point on, documentation upkeep and git history are treated as part of
"done," not optional extras:

- `CHECKLIST.md` gives a single place to see exactly what's finished and
  what's next, broken down by the phases already defined in `CONTEXT.md`.
- `DECISIONS.md` (an Architecture Decision Record / ADR log) captures *why*
  each foundational technology choice was made, what alternatives were
  considered, and what trade-offs were accepted — so future sessions don't
  need to re-litigate settled questions.
- `ROADMAP.md` gives a milestone-level view (current / upcoming / long-term
  / eventually completed) that's easier to skim than the full checklist.
- `LEARNING_NOTES.md` exists because the project owner is explicitly
  learning Linux systems programming, observability, and CLI development
  through this project — every new concept gets a beginner-friendly
  explanation as it's introduced, rather than being assumed as background
  knowledge.

Eleven initial architecture decisions were recorded as ADRs in
`DECISIONS.md`: target OS (Ubuntu 24.04 LTS), development environment
(Multipass VM), Python version (3.12), CLI framework (`argparse`), LLM
provider (OpenAI API), testing framework (`pytest`), package management
(`venv` + `pip`), configuration management (`python-dotenv` + `.env`),
formatting/linting (Black + Ruff), system support strategy (graceful
degradation without systemd), and git strategy (frequent commits by
Claude). The CLI framework and LLM provider decisions resolve the two open
TODOs from the previous log entry.

ADR-011 (Git Strategy) explicitly **supersedes** the original Phase 1 rule
that Claude never commits. This is a deliberate, explicit change from the
project owner, not an oversight — `PROJECT_RULES.md` Section 12 was updated
to match, and the supersession itself is recorded in the ADR rather than
silently overwriting the old rule.

**Important implementation notes**

- Verified all eight documentation files have consistent, non-overlapping
  markdown heading numbering (no gaps or duplicates).
- Verified `CHECKLIST.md`'s Progress Summary numbers match its checkboxes
  by counting directly (`grep -c` for `- [x]` and `- [ ]`): 11 complete, 48
  remaining, 59 total (~19%).
- The git repository did not exist yet in this working directory — it was
  initialized (`git init`) as part of this task, since the new operating
  rules require ongoing commits going forward.
- Claude still never runs `git push` — only `git commit`, per the updated
  Section 12.

**Future TODOs**

- Phase 2: design the snapshot JSON schema (data model) and document it in
  `docs/` (unchanged from previous entry).
- When Phase 3 begins, decide whether `pytest` is added to `requirements.txt`
  immediately (per `PROJECT_RULES.md` Section 11 and `DECISIONS.md`
  ADR-006) rather than waiting for Phase 8.
- When Phase 5 setup instructions are written, include the Multipass launch
  steps referenced in `DECISIONS.md` ADR-002.

---

## 2026-07-14 — Removed AI Co-Author Trailer from Git History

**Task**

This is the project owner's personal portfolio project, and the git
history must show only their own authorship — with no AI co-author
attribution anywhere in it. The most recent commit
(`8adaa22470ff5992d97416950fcb40aef6a0c1c1`) contained a
`Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` trailer, added
automatically as part of the standard commit process in the previous
session. That trailer was removed, the corrected commit was force-pushed to
the existing GitHub remote (`origin/main`), and a new permanent rule was
added to `PROJECT_RULES.md` to prevent this from happening again.

**Files created**

None.

**Files modified**

- `PROJECT_RULES.md` — added a new bullet to Section 12 (Git Workflow):
  "Git commits must never include AI co-author trailers or AI attribution.
  Use only the configured Git user identity."
- `LOGS.md` — this entry.

**Reasoning**

Since this was the only commit in the repository (a root commit, already
pushed to `origin/main`), it was safe to rewrite: `git commit --amend` was
used to replace the commit message with an identical one minus the
`Co-Authored-By` trailer, which produced a new commit hash
(`71ac5249435d043e244ac4fa773cea3984e50abc`) but kept the same tree
contents, author identity (`shrutiii-835 <shruti.jain@calfus.com>`), and
message body. `git push --force-with-lease` was then used instead of a
plain `git push --force` — `--force-with-lease` refuses to overwrite the
remote if it has changed since the local repository last saw it, which
protects against clobbering someone else's work in between. This was a
one-time, explicitly requested corrective action, not a change to the
standing rule that Claude never pushes to a remote on its own initiative
(`PROJECT_RULES.md` Section 12) — future pushes still require the project
owner to ask explicitly.

**Important implementation notes**

- Verified via `git log` on `origin/main` after the force-push that the new
  commit contains no `Co-authored-by` trailer of any kind (checked with a
  case-insensitive match on `^co-authored-by`).
- The word "Claude" still appears once in the commit body, but only as
  ordinary prose describing the project's git workflow ("Update git
  workflow so Claude commits after each verified task") — not as an
  attribution trailer. This is expected and not a violation of the new
  rule, since the rule concerns *attribution*, not any mention of the
  assistant's name in descriptive text.
- Because this rewrote a commit that was already pushed, anyone who had
  already pulled `main` before this fix would need to re-sync (e.g.
  `git fetch && git reset --hard origin/main`) — not a concern here since
  the project owner is the sole contributor.

**Future TODOs**

- None new. Existing TODOs from the previous entry (Phase 2 schema design,
  `pytest` timing decision, Multipass setup docs) are still open.

---

## 2026-07-14 — Phase 2: Snapshot Data Model Designed

**Task**

Design the snapshot's top-level JSON schema — the contract every future
collector (Phase 3) will write to and every future consumer (`report`,
`ask`) will read from. This is a design-only task: no collectors, CLI code,
or LLM integration were written, no Linux commands were executed, and no
Python model classes were implemented, per the Phase 2 scope.

**Files created**

- `docs/snapshot_schema.md` — the complete top-level snapshot schema: one
  section per top-level key (`metadata`, `system`, `cpu_memory`,
  `processes`, `disk`, `services`, `logs`, `network`, `scheduled_jobs`,
  `permissions`, `collection_errors`), each with its purpose, description,
  responsible collector, consuming report(s), mandatory/optional status,
  and a placeholder example structure. Also includes a Design Review
  (quality self-check) and a written resolution for a mismatch between
  CONTEXT.md's collector list (Section 6) and its JSON envelope (Section
  7).
- `docs/data_model_design.md` — the philosophy behind the schema: why JSON,
  why snapshot-first matters for the data model specifically, why
  collectors don't depend on each other, why every section has exactly one
  owning collector, how the schema helps the LLM and maintainability, and
  future extensibility considerations.

**Files modified**

- `CHECKLIST.md` — checked off 13 of 14 Phase 2 tasks (all schema-design
  tasks); left "decide on schema representation in code (dataclasses vs.
  TypedDict)" unchecked, since that's an implementation decision deferred
  to the next task; updated the Progress Summary to 24/59 (~41%).
- `ROADMAP.md` — moved the Current Milestone to Phase 2 (now described as
  schema-designed, one decision open) and the Upcoming Milestone to Phase
  3; added a Phase 1 summary to the previously empty "Eventually Completed"
  section; removed a duplicate description of Phase 3 in the Long-Term
  Milestones list.
- `LEARNING_NOTES.md` — added beginner-friendly explanations of: what a
  data model is, what a schema is, why design comes before implementation,
  why JSON is common for system tools, and what a "contract" between
  software components means.

**Reasoning**

`CONTEXT.md` Section 7 already fixed the top-level key set as a hard
requirement; this task's job was to go one level deeper and decide, for
each key, exactly what fields it contains, who's responsible for
populating it, who will consume it, and whether it's always present. Two
design tensions came up and were resolved explicitly rather than silently:

1. **`cpu_memory` and `disk` each correspond to two informally-listed
   collectors in CONTEXT.md Section 6** (CPU + Memory; Disk + Inodes), but
   only one top-level key each in Section 7. Resolved by giving each
   section exactly one owning collector module with one entry point
   (`collectors/cpu_memory.py`, `collectors/disk.py`), on the reasoning
   that CPU/Memory are always read together operationally and Disk/Inodes
   come from the exact same underlying tool (`df`). This preserves the
   "every section has a single owner" principle without adding
   functionally pointless extra top-level keys. Full write-up in
   `docs/snapshot_schema.md` Section 14 and `docs/data_model_design.md`.
2. **`permissions` was the vaguest data source in the original project
   spec** ("filesystem metadata — permissions and ownership," with no
   specifics). Rather than guessing at a shape that might not match real
   operational needs, this section was deliberately given the loosest,
   most conservative placeholder shape and marked **optional** (the only
   optional section) — explicitly flagged as an open question for Phase 3
   rather than pretending it's settled.

`metadata` and `collection_errors` were both defined as sections owned by
the scan coordinator itself, not by any individual collector — `metadata`
describes the scan process (schema version, timing, which collectors ran),
while `collection_errors` aggregates every collector's own reported
failures into one predictable place. This distinction (facts about the
scan vs. facts about the machine vs. failures during collection) is the
core of what makes the schema self-describing enough for both human
reports and LLM prompts to rely on without ambiguity.

No Python package scaffolding (`src/nodeiq/models/`) was created. Per
`PROJECT_RULES.md` Section 1 ("we don't create empty scaffolding ahead of
need") and this task's explicit instruction not to implement models or
classes yet, an empty folder with no code would serve no purpose — it's
deferred to whenever the dataclass-vs-TypedDict decision is made and the
first model file is actually written.

**Important implementation notes**

- Verified the schema's Design Review section (Section 13 of
  `docs/snapshot_schema.md`) explicitly against all five quality-check
  questions posed in this task (extensibility, independence, beginner
  clarity, data/error separation, dual report+LLM fitness) before
  finishing.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count (`grep -c` for `- [x]` / `- [ ]`): 24 complete, 35 remaining, 59
  total (~41%).
- `metadata.schema_version` was set to `"1.0"` (draft) as the mechanism for
  handling any future breaking change to this schema explicitly rather than
  silently.
- This task did not touch `CONTEXT.md` — the collector-count/envelope-key
  mismatch was resolved by *interpretation* in the new docs, not by editing
  CONTEXT.md's existing text, since Phase 2 scope was documentation under
  `docs/` plus the four tracking files, and `PROJECT_RULES.md` Section 14
  says CONTEXT.md should only be updated when the architecture/philosophy
  actually changes (this was a clarification, not a change). A small
  clarifying note in CONTEXT.md is recommended as a future task — see
  Future TODOs.

**Future TODOs**

- Decide schema representation in code: `dataclasses` vs. `TypedDict` (the
  one remaining unchecked Phase 2 task in `CHECKLIST.md`).
- Consider a small clarifying note in `CONTEXT.md` Section 6 noting that
  `cpu_memory` and `disk` each have one owning collector covering two
  related data sources — optional, since `docs/snapshot_schema.md` Section
  14 already documents this in detail.
- Phase 3: implement `collectors/system.py` first (the simplest collector,
  good for validating the scan-coordinator pattern end to end).
- Phase 3: finalize the exact scope of the `permissions` collector (which
  paths, what counts as noteworthy) — currently an open question per
  `docs/snapshot_schema.md` Section 11.
- Existing open TODOs from prior entries (`pytest` timing decision,
  Multipass setup docs in `README.md`) remain open.

---

## 2026-07-14 — Phase 3.1: Core Execution Infrastructure

**Task**

Build the reusable execution foundation every future collector will run on
top of: a safe command runner, its result type, minimal project-specific
exceptions, and a documented (not implemented) scan coordinator placeholder.
Introduce `pytest` and write focused tests for the runner. This closes the
`pytest` timing TODO from earlier entries — added now, in Phase 3, rather
than waiting for Phase 8. No Linux collectors, CLI, or LLM integration were
written, per Phase 3.1 scope.

**Files created**

- `src/nodeiq/__init__.py` — package docstring (previously missing; needed
  now that real code lives under `src/nodeiq/`).
- `src/nodeiq/core/__init__.py`, `src/nodeiq/core/result.py`,
  `src/nodeiq/core/exceptions.py`, `src/nodeiq/core/runner.py`,
  `src/nodeiq/core/coordinator.py` — the execution infrastructure package.
- `src/nodeiq/collectors/__init__.py` — empty package scaffolding for
  Phase 3.2's collectors.
- `tests/core/test_runner.py` — 5 focused tests for the runner.
- `pyproject.toml` — pytest configuration (`pythonpath = ["src"]` so tests
  can import `nodeiq` without an editable install).
- `docs/architecture.md` — diagram, dependency flow, and per-layer
  explanation of the Phase 3.1 code.
- `.venv/` (local only, gitignored) — created to install and run `pytest`.

**Files modified**

- `requirements.txt` — added `pytest>=9.1,<10` (was empty).
- `.gitignore` — added `.pytest_cache/`.
- `README.md` — updated the folder-structure diagram to include
  `pyproject.toml`, `docs/architecture.md` and friends, `src/nodeiq/core/`,
  and `src/nodeiq/collectors/`; updated Setup Instructions to include
  running the test suite.
- `CHECKLIST.md` — split Phase 3 into "Phase 3.1 — Core Execution
  Infrastructure" (all 7 tasks checked) and "Phase 3.2 — Collectors" (all
  unchecked, and updated to match the Phase 2 schema decisions —
  `cpu_memory` and `disk` each listed as one collector, not two); Progress
  Summary updated to 31/64 (~48%).
- `ROADMAP.md` — Current Milestone moved to Phase 3.1 (complete); Upcoming
  Milestone moved to Phase 3.2.
- `LEARNING_NOTES.md` — added beginner-friendly explanations of:
  `subprocess`, why `shell=True` is avoided, stdout vs. stderr, exit codes,
  timeouts, command execution abstraction, and orchestration.

**Reasoning**

Every future collector needs to run Linux commands and handle whatever can
go wrong doing so (missing programs, timeouts, permission errors). Building
this once, centrally, in `nodeiq.core.runner`, means every collector in
Phase 3.2 gets the same safety guarantees automatically instead of each
one re-implementing (and potentially getting slightly wrong) its own
subprocess handling. This is a direct, concrete application of the
"collectors don't depend on each other" principle from
`docs/data_model_design.md`: collectors will depend on this one shared,
generic layer, never on each other.

`CommandResult` is a small, immutable dataclass rather than a bare dict, so
every field (`returncode`, `stdout`, `stderr`, `duration_seconds`,
`timed_out`, `error`) is named and typed. `exceptions.py` was kept to just
two classes: `NodeIQError` (a base class for future use) and
`InvalidCommandError` (raised only for a genuine programmer mistake —
passing something that isn't a list of strings — since that's an API
misuse, not a system-level failure the runner is designed to absorb).

`coordinator.py` is a documented placeholder, not a real implementation —
its module docstring records the coordinator's future responsibilities
(running every collector, assembling the snapshot, owning `metadata` and
`collection_errors`) in detail, so Phase 3.2 has a clear target without
this phase pretending collectors already exist to orchestrate.

`pytest` was introduced now rather than waiting for Phase 8, per
`PROJECT_RULES.md` Section 11 ("added early as a dev-only dependency if
needed sooner; use judgment and note the decision"). A `.venv` was created
locally (gitignored) and `pytest` installed into it, matching
`DECISIONS.md` ADR-007 (`venv` + `pip`). Tests use the currently-running
Python interpreter itself as the "external command" (`sys.executable`)
rather than a Linux-only tool like `df`, so the test suite runs
identically on any OS Python supports — the runner itself is
general-purpose; only future collectors will be Linux-specific.

**Important implementation notes**

- **Self-review caught a real gap, not just style:** the initial
  `subprocess.run(..., text=True)` call had no defense against a command
  printing bytes that aren't valid UTF-8 (a realistic risk for real
  system/log output), which would have raised `UnicodeDecodeError` and
  defeated the "never crash the application" requirement. Fixed by adding
  `errors="replace"`, which substitutes invalid bytes instead of raising —
  a one-line, low-complexity fix rather than an added exception branch.
- `FileNotFoundError` is technically a subclass of `OSError`, so it could
  have been handled by one `except OSError` block — it's deliberately kept
  as its own, earlier `except` clause so the two failure modes ("the
  program doesn't exist" vs. "some other OS-level failure launching it")
  get distinct, more useful `error` messages, per `PROJECT_RULES.md`
  Section 7's preference for catching specific exceptions.
- Verified all 5 runner tests pass locally (`python -m pytest`): successful
  execution, stdout/stderr captured separately, non-zero exit code,
  timeout handling, and rejection of a non-list command.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count: 31 complete, 33 remaining, 64 total (~48%).
- `src/nodeiq/__init__.py` did not exist before this task (only its
  subdirectories did) — added now since it's genuinely needed for
  `nodeiq.core...` imports to work, not scope creep.

**Future TODOs**

- Phase 3.2: implement `collectors/system.py` first, per the previous
  entry's recommendation — it's the simplest collector and will validate
  the whole `runner` → collector → (eventually) `coordinator` pattern
  end-to-end.
- Phase 3.2: once at least one real collector exists, implement
  `coordinator.run_scan()` for real, replacing the `NotImplementedError`
  placeholder.
- Still open: `dataclasses` vs. `TypedDict` decision for snapshot section
  shapes (Phase 2's one remaining task); `permissions` collector scope;
  `CONTEXT.md` Section 6 clarifying note (optional); Multipass setup docs
  in `README.md`.

---

## 2026-07-14 — Phase 3.2A: Collector Design Pattern

**Task**

Define the standard contract every collector will implement, before
writing any actual collector. This is a design-only task: no Linux
collectors, CLI code, or LLM integration were written, per Phase 3.2A
scope.

**Files created**

- `docs/collector_guidelines.md` — the full collector contract: purpose,
  responsibilities, what a collector must never do, the standard lifecycle
  (`collect()` → `run_command()` → parse → validate → return), the
  `collect() -> tuple[dict, list[dict]]` return contract, separation of
  command execution and parsing, error handling expectations, JSON output
  expectations, `_parse_*`/`_validate_*` helper conventions, testing
  expectations, and an illustrative (non-functional) pseudo-code example
  based on a hypothetical `disk` collector.

**Files modified**

- `PROJECT_RULES.md` — Section 9 (Collector Implementation Guidelines),
  items 2 and 5, updated to reflect the `collect() -> tuple[dict,
  list[dict]]` contract (previously said `collect() -> dict`, written
  before this contract was formally decided) and to point to
  `docs/collector_guidelines.md`.
- `src/nodeiq/core/coordinator.py` — docstring only, no logic changed:
  updated the "Interaction with collectors" and "Future responsibilities"
  sections to describe the `(data, errors)` return contract instead of the
  earlier, less precise `collect() -> dict`.
- `docs/architecture.md` — one sentence in the `nodeiq.collectors`
  description updated to mention the `(data, errors)` return shape and
  reference `docs/collector_guidelines.md`.
- `DECISIONS.md` — added ADR-012 (parsing belongs in collectors, not the
  runner) and ADR-013 (no application logging in v1; collector errors
  live in `collection_errors` instead).
- `CHECKLIST.md` — split the former "Phase 3.2 — Collectors" into "Phase
  3.2A — Collector Design Pattern" (all 9 tasks checked) and "Phase 3.2B —
  Collectors (Implementation)" (unchanged, still unstarted); Progress
  Summary updated to 40/73 (~55%).
- `ROADMAP.md` — Current Milestone moved to Phase 3.2A (complete);
  Upcoming Milestone renamed to Phase 3.2B; added Phase 3.1 and Phase 3.2A
  summaries to "Eventually Completed."
- `LEARNING_NOTES.md` — added beginner-friendly explanations of:
  separation of concerns, why contracts between modules matter, why
  parsing is different from execution, and why application logging is
  being delayed.

**Reasoning**

Nine collectors are about to be built (Phase 3.2B), each by essentially
the same recipe. Writing that recipe down once, and reviewing it
critically, before the first collector exists, means all nine end up
consistent with each other by construction, rather than by
after-the-fact cleanup once small inconsistencies have already crept in —
the same "design before implementation" reasoning already applied to the
snapshot schema in Phase 2 (see `LEARNING_NOTES.md`, "Why does design come
before implementation?").

The central design decision was the `collect() -> tuple[dict, list[dict]]`
contract. Earlier documentation (`PROJECT_RULES.md` Section 9, written
during Phase 1, and `core/coordinator.py`'s docstring, written during
Phase 3.1) both said `collect() -> dict`, without specifying *how* a
collector would communicate a partial or total failure back to the
coordinator — `coordinator.py`'s docstring already said "a collector never
writes directly into `collection_errors` itself; it returns its errors to
the coordinator," but never said through what mechanism. This task closes
that gap: a plain two-item tuple, `(data, errors)`, rather than a new
class, a raised exception for expected failures, or a reserved-key
convention inside a single dict. This was chosen specifically for being
the least additional machinery that still lets a collector report "I got
most of this, but not that part" — directly serving this task's Quality
Check requirement to avoid unnecessary abstraction.

Two ADRs were added rather than one, despite the task listing both points
together, because `DECISIONS.md`'s own stated convention is "each entry
captures one decision" — parsing location and logging strategy are
unrelated decisions that happen to have been requested in the same
message, not one decision with two parts.

ADR-013 (no v1 logging) surfaced a real tension with `PROJECT_RULES.md`
Section 8 (Logging Philosophy), which was written in Phase 1 and already
describes a logging setup NodeIQ doesn't have and, per this decision,
won't have in v1. This task's declared scope for file updates didn't
include `PROJECT_RULES.md` Section 8 specifically (only Section 9 needed a
factual correction for the return-type mismatch), so rather than silently
editing Section 8's standing content, the tension is recorded explicitly
in ADR-013's Future Impact and flagged below as a follow-up — the same
approach taken for the CONTEXT.md Section 6 collector-count mismatch found
during Phase 2.

**Important implementation notes**

- Verified the guidelines document's own Quality Check section explicitly
  against this task's constraint: no inheritance hierarchies, no abstract
  base classes, no plugin system, no unnecessary framework. The entire
  contract is one function name, a two-item tuple of built-in types, and a
  naming convention for private helpers.
- Verified the `(data, errors)` contract is practical for every one of the
  nine planned collectors, including the simplest ones (e.g. `system`,
  which may only need one `/proc` read and no command-output parsing at
  all) — the contract doesn't force unnecessary structure onto a simple
  collector.
- Re-ran the full test suite after the `coordinator.py` docstring edit
  (docstring-only, no logic changed) to confirm nothing broke: all 5
  existing runner tests still pass.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count: 40 complete, 33 remaining, 73 total (~55%).

**Future TODOs**

- Phase 3.2B: implement `collectors/system.py` first, following
  `docs/collector_guidelines.md`, to validate the whole pattern
  end-to-end before the remaining eight collectors.
- Follow-up: reconcile `PROJECT_RULES.md` Section 8 (Logging Philosophy)
  with ADR-013's "no v1 logging" decision — either update Section 8 to
  describe v1's actual behavior, or implement logging properly. Currently
  the two documents describe different things and that's flagged, not
  silently resolved.
- Still open from prior entries: `dataclasses` vs. `TypedDict` decision
  for snapshot section shapes; `permissions` collector scope; `CONTEXT.md`
  Section 6 clarifying note (optional); Multipass setup docs in
  `README.md`.

---

## 2026-07-14 — Phase 3.2B: Collector Infrastructure Refinement

**Task**

Refine the collector contract designed in Phase 3.2A before implementing
any collector: replace `collect() -> tuple[dict, list[dict]]` with
`collect(context: CollectorContext) -> CollectorResult`, two small
dataclasses in a new `nodeiq.core.collector` module. This is still a
design/infrastructure task — no Linux collectors, CLI code, or LLM
integration were written. This task is itself named "Phase 3.2B" (per the
instructions that requested it), which collided with the existing
checklist naming for the collector-implementation phase — resolved by
renaming that phase to "Phase 3.2C" (see Files Modified below).

**Files created**

- `src/nodeiq/core/collector.py` — `CollectorContext` (`scan_start_time`,
  `default_timeout`, both `@dataclass(frozen=True)`) and `CollectorResult`
  (`collector_name`, `data`, `errors`, `duration_ms`, plus a computed
  `success` property that's `False` only when `errors` contains an
  `"error"`-severity entry — warnings alone don't count as failure).
- `tests/core/test_collector.py` — 7 focused tests: context default
  timeout matches the runner's constant, timeout override, immutability
  (both dataclasses), and `success` under no errors / warnings-only /
  error-severity conditions.

**Files modified**

- `docs/collector_guidelines.md` — replaced the tuple contract throughout
  ("The Standard Contract," the lifecycle diagram, the pseudo-code
  examples, testing expectations) with `collect(context) ->
  CollectorResult`; added a new "Why a Structured Result Instead of a
  Tuple" subsection; added a revision note at the top; updated the Quality
  Check to explicitly re-verify no inheritance/ABCs/plugin system/DI crept
  in with the refinement.
- `docs/architecture.md` — diagram updated to show the coordinator building
  one `CollectorContext` and each collector returning a `CollectorResult`;
  added a new "`nodeiq.core.collector`" entry to "The Layers, Explained";
  updated remaining `(data, errors)`/bare-`dict` mentions and stale
  "Phase 3.2" references to match.
- `DECISIONS.md` — added ADR-014: why a structured `CollectorResult` beats
  a tuple (named fields, room to grow), and why `CollectorContext` is
  justified now even with only two fields (both already solve a real,
  current problem — shared timeout default, shared scan start time — not
  a speculative extension point).
- `src/nodeiq/core/coordinator.py` — docstring only, no logic changed:
  updated every mention of the tuple contract to describe
  `CollectorContext`/`CollectorResult`.
- `PROJECT_RULES.md` — Section 9, items 2, 3, 5, and 8 updated to the new
  contract and to mention `context.default_timeout`.
- `CHECKLIST.md` — added "Phase 3.2B — Collector Infrastructure
  Refinement" (all 6 tasks checked) and renamed the former "Phase 3.2B —
  Collectors (Implementation)" to "Phase 3.2C" to resolve the naming
  collision; Progress Summary updated to 46/79 (~58%).
- `ROADMAP.md` — Current Milestone moved to Phase 3.2B (this task);
  Upcoming Milestone renamed to Phase 3.2C; added a Phase 3.2B summary to
  "Eventually Completed."
- `LEARNING_NOTES.md` — added beginner-friendly explanations of: what a
  dataclass is, why a result object beats a tuple, why design for
  reasonable extensibility without over-engineering, and what a context
  object is.

**Reasoning**

The tuple contract from Phase 3.2A worked, but had a real, concrete
weakness: `(data, errors)` only means "data first, errors second" by
convention — nothing about the type itself names or documents that, and
there was nowhere to attach genuinely useful additional facts (which
collector produced this, how long it took) without growing the tuple's
arity or tracking those facts separately, disconnected from the result
they describe. `CollectorResult` fixes this by naming every field.

`CollectorContext` was added even though it currently carries only two
fields, because both already solve a concrete, present problem rather
than anticipating a hypothetical one: every collector already needs *some*
timeout value for `run_command`, and centralizing it in a context object
(instead of each collector hardcoding its own default) means a future scan
mode could change every collector's timeout at once, from one place.
`scan_start_time` similarly gives every collector one agreed-upon "now"
for the scan. Both are documented explicitly as "solving a real problem
now," specifically to distinguish this from adding an unused
"extensibility" field just in case — which was deliberately *not* done
(see the Quality Check in `docs/collector_guidelines.md` and ADR-014).

`CollectorResult.success` was implemented as a computed `@property` (not a
stored constructor field, even though the task's suggested field list
included it) to mirror `CommandResult.succeeded` (already a property in
`core/result.py`) and to make an inconsistent state (e.g. `success=True`
with an error-severity entry present) structurally impossible rather than
relying on every caller to keep the two in sync by convention.

**Important implementation notes**

- Verified via `PYTHONPATH=src python3 -c "..."` that both dataclasses
  behave as designed before writing formal tests: default timeout
  resolution, and `success` under no-errors / warnings-only / has-error
  conditions.
- Verified all 12 tests pass (7 new + 5 existing from Phase 3.1) after
  every documentation-only edit to `coordinator.py`.
- Swept the repository for stale `tuple[dict, list[dict]]` references
  after the edits — the only remaining mentions are in `LOGS.md`'s
  historical Phase 3.2A entry (correctly describing what was true then)
  and `docs/collector_guidelines.md`'s own revision note (intentional).
- The Phase 3.2B naming collision (this task self-identified as "Phase
  3.2B," which was already in use for collector implementation) was
  resolved by renaming the implementation phase to "Phase 3.2C" — flagged
  explicitly here rather than silently overwritten, consistent with how
  this project handles naming/documentation tensions elsewhere (e.g. the
  CONTEXT.md Section 6 collector-count mismatch from Phase 2).

**Future TODOs**

- Phase 3.2C: implement `collectors/system.py` first, following the
  now-refined `docs/collector_guidelines.md`, to validate the whole
  `CollectorContext` → `collect()` → `CollectorResult` → (eventually)
  coordinator pattern end-to-end.
- Still open from prior entries: `PROJECT_RULES.md` Section 8
  (Logging Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs.
  `TypedDict` decision for snapshot section shapes; `permissions`
  collector scope; `CONTEXT.md` Section 6 clarifying note (optional);
  Multipass setup docs in `README.md`.

---

## 2026-07-14 — Phase 3.2C: System Collector v1

**Task**

Implement `system.py`, the first real Linux collector, following the
`CollectorContext` → `collect()` → `CollectorResult` pattern designed in
Phases 3.2A/3.2B. Scope deliberately narrow — `hostname`,
`operating_system`, `kernel_version`, `architecture`, `uptime_seconds` —
to validate the whole collector pattern with real Linux commands and real
files before building the remaining eight collectors. Per this task's
scope, no other collector and no scan coordinator implementation were
written.

**Files created**

- `src/nodeiq/collectors/system.py` — `collect(context) -> CollectorResult`
  plus private helpers: `_error_entry` (shared error-dict builder),
  `_run_and_capture` (shared command-wrapper for the three trivial
  single-line commands), `_get_hostname`/`_get_kernel_version`/
  `_get_architecture` (via `hostname`, `uname -r`, `uname -m`), and
  `_get_os_release`/`_get_uptime` with their own pure `_parse_os_release`/
  `_parse_uptime` helpers (reading `/etc/os-release` and `/proc/uptime`
  directly).
- `tests/collectors/test_system.py` — 17 unit tests: pure parsing
  functions tested with literal sample text; command-based getters tested
  with `run_command` monkeypatched; file-based getters tested via
  monkeypatched module-level path constants and `tmp_path`; `collect()`
  tested end-to-end for both "everything succeeds" and "one field fails,
  the rest don't."
- `tests/collectors/test_system_integration.py` — 1 integration test
  calling the real `collect()` with nothing mocked, skipped automatically
  unless `platform.system() == "Linux"`.
- `docs/system_collector.md` — responsibilities, a table of why each data
  source was chosen, why machine-readable files beat parsing formatted
  command output (with a real `uptime` vs. `/proc/uptime` comparison), and
  an explicit "Fields Intentionally Deferred" section.

**Files modified**

- `src/nodeiq/collectors/__init__.py` — updated from "no collectors yet"
  to note `system.py` is the first.
- `docs/architecture.md` — status line, diagram caption, and five
  "Phase 3.2B" mentions left over from the previous task's phase rename
  corrected to "Phase 3.2C" (one, in "Why the Coordinator Owns Snapshot
  Assembly," also had an awkward line-wrap left over from a prior edit,
  fixed as part of the same pass); `nodeiq.collectors` entry in "The
  Layers, Explained" updated from "empty so far" to describe `system.py`.
- `docs/collector_guidelines.md` — two remaining "Phase 3.2B" mentions
  (status line, Quality Check) corrected to "Phase 3.2C"; status line
  updated to point at `docs/system_collector.md`.
- `README.md` — folder-structure diagram updated to list
  `collector_guidelines.md`/`system_collector.md` under `docs/` and to
  note `system.py` as the first collector.
- `CHECKLIST.md` — checked off the `system` collector task (noting the
  deferred fields inline); Progress Summary updated to 47/79 (~59%),
  Phase 3.2C marked in progress (1 of 10 tasks done).
- `ROADMAP.md` — Current Milestone updated to describe `system.py` as
  built and verified; Upcoming Milestone renamed to "Phase 3.2C
  continued" for the remaining eight collectors.
- `LEARNING_NOTES.md` — added beginner-friendly explanations of: what
  `/proc` is, what `/etc/os-release` is, why Linux exposes system
  information through files, and the difference between machine-readable
  and human-readable interfaces.

**Reasoning**

Five fields were chosen deliberately narrow, per this task's explicit
scope — not the full `system` section already defined in
`docs/snapshot_schema.md` Section 3 (which also has `os_name`/`os_version`
as two fields and a `boot_time` field this collector doesn't produce).
Rather than silently matching or silently diverging from the existing
schema, the gap is documented explicitly in `docs/system_collector.md`'s
"Fields Intentionally Deferred" section and called out in `CHECKLIST.md` —
the same approach this project has taken for every previous
documentation/scope tension (CONTEXT.md Section 6, PROJECT_RULES.md
Section 8 vs. ADR-013).

Three of the five fields (`hostname`, `kernel_version`, `architecture`)
come from trivial single-line commands (`hostname`, `uname -r`,
`uname -m`) where a single `.strip()` is the only "parsing" involved — this
was deliberately kept inline in a shared `_run_and_capture` helper rather
than split into a further pure `_parse_*` function per field, since a
dedicated function for one `.strip()` call would be the over-engineering
this project's Quality Checks have repeatedly warned against. The other
two (`operating_system`, `uptime_seconds`) come from files with genuinely
non-trivial parsing (`/etc/os-release`'s multi-line `KEY=value` format,
`/proc/uptime`'s two-number line), so those got their own pure, directly
testable `_parse_os_release`/`_parse_uptime` functions, per
`docs/collector_guidelines.md`'s "Separation of Command Execution and
Parsing."

`_get_os_release`/`_get_uptime` read their file paths from module-level
constants (`_OS_RELEASE_PATH`, `_UPTIME_PATH`) looked up fresh inside the
function body (not bound as default parameter values) specifically so
`monkeypatch.setattr(system, "_OS_RELEASE_PATH", ...)` works correctly
even when the function is called indirectly through `collect()` —
binding the path as a literal default parameter value would have been
fixed at module-import time and unaffected by monkeypatching afterward.

**Important implementation notes**

- **Verified genuinely, not just written to spec:** a Multipass VM
  (`main-cattle`, Ubuntu 24.04 LTS, matching `DECISIONS.md` ADR-001/002)
  was already running. Real sample output was pulled from it first
  (`hostname`, `uname -r`, `uname -m`, `/etc/os-release`, `/proc/uptime`)
  to confirm the parsing plan before writing code. The `python3-venv`
  package had to be installed on the VM (`apt install python3.12-venv`)
  before a venv could be created there. The full project (`src/`, `tests/`,
  `pyproject.toml`, `requirements.txt`) was then copied to the VM via
  `multipass transfer`, a venv created, `pytest` installed, and the full
  30-test suite run for real — all 30 passed, including the integration
  test actually executing (not skipped) since `platform.system() ==
  "Linux"` there. The temporary copy was removed from the VM afterward
  (`rm -rf ~/nodeiq_test`); the VM itself was left running as found.
- Verified the collector also runs correctly on the local macOS dev
  machine (used for day-to-day development): `hostname`, `kernel_version`,
  and `architecture` succeed there too (macOS has all three commands),
  while `operating_system` and `uptime_seconds` correctly come back as
  `None` with clear error entries, since macOS has neither
  `/etc/os-release` nor `/proc/uptime` — demonstrating the graceful
  per-field degradation working exactly as designed, not just in tests.
- Re-verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count: 47 complete, 32 remaining, 79 total (~59%).

**Future TODOs**

- Phase 3.2C: implement the `cpu_memory` collector next, following
  `system.py` as the template (two `/proc` files, `/proc/loadavg` and
  `/proc/meminfo`, no commands needed at all).
- Phase 3.2C (later): once at least a couple more collectors exist,
  implement `coordinator.run_scan()` for real.
- Phase 3.2C (later, or a dedicated follow-up): consider extending
  `system.py` to add the deferred `os_name`/`os_version` split and
  `boot_time`, to fully match `docs/snapshot_schema.md` Section 3.
- Still open from prior entries: `PROJECT_RULES.md` Section 8 (Logging
  Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs. `TypedDict`
  decision for snapshot section shapes; `permissions` collector scope;
  `CONTEXT.md` Section 6 clarifying note (optional); Multipass setup docs
  in `README.md`.

---

## 2026-07-14 — Phase 3.3: Resource Collector (Memory & Load) v1

**Task**

Implement `resource.py`, the second real Linux collector, following the
`CollectorContext` → `collect()` → `CollectorResult` pattern established
by `system.py`. Gathers memory/swap usage from `/proc/meminfo` and load
averages from `/proc/loadavg` — no commands at all, since a stable kernel
interface already exists for everything in scope. Per this task's scope,
no other collector and no scan coordinator implementation were written.

**Files created**

- `src/nodeiq/collectors/resource.py` — `collect(context) ->
  CollectorResult` plus private helpers: `_error_entry` (error-dict
  builder, matching `system.py`'s), `_read_proc_file` (shared file-read
  wrapper for the two `/proc` files), `_get_memory_fields` (with pure
  `_parse_meminfo` and `_compute_memory_fields`/`_percent` helpers), and
  `_get_load_average_fields` (with a pure `_parse_loadavg` helper).
- `tests/collectors/test_resource.py` — 17 unit tests: pure parsing and
  computation functions tested with literal sample text/dicts (including
  the real `SwapTotal == 0` edge case observed on the Multipass VM);
  file-based getters tested via monkeypatched module-level path constants
  and `tmp_path`; `collect()` tested end-to-end for "everything succeeds,"
  "memory source fails, load average doesn't," and vice versa.
- `tests/collectors/test_resource_integration.py` — 1 integration test
  calling the real `collect()` with nothing mocked, skipped automatically
  unless `platform.system() == "Linux"`.
- `docs/resource_collector.md` — responsibilities, why `/proc/meminfo`
  beats `free` and `/proc/loadavg` beats `uptime` (with real command
  comparisons), a field-by-field explanation table, explicitly deferred
  fields (CPU utilization percentages), a "Fields Not Yet Collected"
  section, an explicit naming/schema-alignment note, and a reusable
  Collector Review Checklist.

**Files modified**

- `src/nodeiq/collectors/__init__.py` — updated to note `resource.py` is
  now built alongside `system.py`.
- `README.md` — folder-structure diagram updated to list
  `resource_collector.md` and to note `resource.py`.
- `CHECKLIST.md` — checked off the collector task (renamed inline from
  "CPU + memory collector" to reflect what was actually built, with the
  naming/schema divergence noted); Progress Summary updated to 48/79
  (~61%), Phase 3.2C now 2 of 10 tasks done.
- `ROADMAP.md` — Current Milestone updated to describe both `system.py`
  and `resource.py` as built and verified.
- `LEARNING_NOTES.md` — added beginner-friendly explanations of: what
  `/proc/meminfo` contains, what load average actually means, why
  available memory is often more useful than free memory, and the
  difference between memory usage and CPU load.

**Reasoning**

This collector needed **zero** `run_command` calls — the task explicitly
required using kernel-provided machine-readable interfaces (`/proc/meminfo`,
`/proc/loadavg`) instead of commands (`free`, `uptime`) wherever a stable
one already exists, per `PROJECT_RULES.md` Section 9 (item 7). This is a
useful confirmation of the collector pattern's flexibility: `collect()`'s
signature and `CollectorResult`'s shape don't care whether a collector
uses `run_command` at all, only that it returns the right type.

Error handling granularity here is per **data source**, not per
individual field, unlike `system.py`. `system.py` had five genuinely
independent fields (each from its own command or file); `resource.py` has
two data sources (`/proc/meminfo`, `/proc/loadavg`), each producing
*several related fields together* — there's no such thing as reading
`MemTotal` successfully but `MemAvailable` failing, since both come from
one file read. So `collect()` has two `try`/`except` blocks (one per
file), not eight, directly matching this task's own instruction: "if one
data source fails, continue collecting any remaining information."

The naming and shape divergence from `docs/snapshot_schema.md` Section
4's existing `cpu_memory` section (module name `resource.py` vs.
`cpu_memory.py`; flat byte-denominated fields vs. nested kB fields; no
`core_count`) is documented explicitly in `docs/resource_collector.md`
rather than silently reconciled either way — the same treatment given to
`system.py`'s `operating_system` field divergence from `os_name`/
`os_version` in the previous entry. This is now the project's established
pattern for handling a real implementation task's explicit instructions
that don't quite match an earlier, more abstractly-designed document.

**Important implementation notes**

- **Verified genuinely, not just written to spec:** real `/proc/meminfo`
  and `/proc/loadavg` content was pulled from the Multipass VM
  (`main-cattle`) *before* writing the parsing code, to confirm the format
  assumptions (the VM had `SwapTotal: 0`, a genuine no-swap-configured
  case that directly exercised the division-by-zero guard in `_percent`).
  The VM had been stopped since the last session and was restarted
  automatically by `multipass exec`. The full project was then copied to
  the VM via `multipass transfer`, a venv created, `pytest` installed, and
  the full 48-test suite run for real — all 48 passed, including both
  integration tests (`system` and `resource`) actually executing. The
  temporary copy was removed afterward (`rm -rf ~/nodeiq_test`).
- **Quality review caught one real, worth-fixing duplication:**
  `_get_memory_fields` and `_get_load_average_fields` initially repeated
  an identical three-line "read a `/proc` file, wrap `OSError` as
  `ValueError`" block *within the same module* — simplified by
  extracting a shared private `_read_proc_file` helper, mirroring how
  `system.py`'s three command-based getters already share
  `_run_and_capture`. This is a within-module simplification, not a new
  cross-collector abstraction.
- **Quality review also identified, but deliberately did not fix,**
  duplication *across* collectors: `_error_entry` is now duplicated
  verbatim between `system.py` and `resource.py`, and the "read file, wrap
  as ValueError" shape (now factored inside each module) is conceptually
  duplicated across both modules too. Per `DECISIONS.md` ADR-012's
  explicit threshold ("three or more collectors" before extracting a
  shared helper from evidence), this is noted but not yet extracted into
  `nodeiq.core` — tracked as a Future TODO for when the third collector is
  built.
- Verified the collector also runs correctly on the local macOS dev
  machine: with no `/proc` at all, both data sources fail gracefully (all
  eight fields `None`, two clear error entries), confirming the two
  `try`/`except` blocks are genuinely independent, not just in theory.
- Re-verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count: 48 complete, 31 remaining, 79 total (~61%).

**Future TODOs**

- Phase 3.2C: implement the `processes` collector next.
- Phase 3.2C (later): once a third collector is built, revisit whether
  `_error_entry` and/or the "read file, wrap as ValueError" pattern have
  shown up often enough (per ADR-012's threshold) to justify extracting a
  shared helper into `nodeiq.core`.
- Phase 3.2C (later, or a dedicated follow-up): reconcile `resource.py`'s
  field names/shape with `docs/snapshot_schema.md` Section 4's original
  `cpu_memory` section — either update the schema doc to match what was
  built, or refactor the collector to match the schema.
- A future increment of `resource.py` could add CPU utilization
  percentages (from `/proc/stat`, requiring two readings apart in time —
  a meaningfully different collection strategy from everything else this
  collector does) — see `docs/resource_collector.md`'s "Fields Not Yet
  Collected."
- Still open from prior entries: `PROJECT_RULES.md` Section 8 (Logging
  Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs. `TypedDict`
  decision for snapshot section shapes; `permissions` collector scope;
  `CONTEXT.md` Section 6 clarifying note (optional); Multipass setup docs
  in `README.md`.

---

## 2026-07-15 — Phase 3.4: Coordinator MVP

**Task**

Prove the whole architecture works end to end for the first time:
`CollectorContext → collectors → CollectorResult → coordinator →
snapshot`. Rename `resource.py` to `cpu_memory.py`, implement
`run_scan()` for real (replacing the `NotImplementedError` placeholder
from Phase 3.1), and verify with both mocked unit tests and a real
end-to-end integration test on the Multipass VM. Per this task's scope:
no CLI, no writing snapshots to disk, no additional collectors.

**Files created**

- `src/nodeiq/core/coordinator.py` — rewritten from a documented
  placeholder to a real implementation: `run_scan()` builds one
  `CollectorContext`, runs every module in `_REGISTERED_COLLECTORS =
  [system, cpu_memory]`, aggregates `collection_errors` (both the normal
  path — a collector's own reported errors — and a crash path, wrapping
  each collector call in `try`/`except Exception` as a last-resort safety
  net), builds `metadata` (`scan_timestamp`, `scan_duration_ms`,
  `collector_count`, `nodeiq_version`, `hostname`), assembles the
  snapshot, and validates it with `_validate_snapshot` before returning.
- `tests/core/test_coordinator.py` — 11 unit tests using fake "collector
  modules" (plain objects with a `collect(context)` function and a dotted
  `__name__`) instead of the real collectors: every registered collector
  executes, data assembles under the right key, errors aggregate
  correctly (both reported and crash paths), a crash in one collector
  doesn't stop the next, metadata is populated correctly (including the
  `hostname` fallback to `None`), and `_validate_snapshot` both passes and
  raises as expected.
- `tests/core/test_coordinator_integration.py` — 1 integration test
  calling the real `run_scan()` with the real `system`/`cpu_memory`
  collectors, no mocking at all, skipped automatically unless
  `platform.system() == "Linux"`.
- `docs/coordinator.md` — responsibilities, why collectors remain
  independent (now provable in running code, not just documented), why
  the coordinator owns orchestration, the snapshot assembly process,
  error aggregation, metadata generation, an explicit "MVP
  Simplifications" section, and a Coordinator Review Checklist.

**Files modified**

- **Rename:** `src/nodeiq/collectors/resource.py` → `cpu_memory.py`
  (`git mv`), `tests/collectors/test_resource.py` →
  `test_cpu_memory.py`, `tests/collectors/test_resource_integration.py` →
  `test_cpu_memory_integration.py`, `docs/resource_collector.md` →
  `docs/cpu_memory_collector.md` — module docstring, `collector_name`
  (now `"cpu_memory"`, matching the module name), all test imports/
  monkeypatch targets, and the doc's own content updated throughout.
  `docs/cpu_memory_collector.md`'s "A Note on Naming and Schema Alignment"
  was rewritten to reflect that the module name is now aligned with
  `docs/snapshot_schema.md` Section 4 — only the field-shape divergence
  (flat bytes vs. nested kB, no `core_count`) remains open.
- `src/nodeiq/__init__.py` — added `__version__ = "0.1.0"`, the canonical
  source for `metadata.nodeiq_version`.
- `src/nodeiq/collectors/__init__.py` — updated to describe both
  collectors and the rename.
- `docs/architecture.md` — status line, diagram, and every remaining
  "placeholder" / stale "Phase 3.2C" mention describing the coordinator
  updated to reflect `run_scan()` as implemented (Phase 3.4); the
  "`nodeiq.collectors`" entry in "The Layers, Explained" updated to
  mention `cpu_memory.py`.
- `README.md` — folder-structure diagram updated to list
  `docs/cpu_memory_collector.md`, `docs/coordinator.md`, and
  `cpu_memory.py`.
- `LEARNING_NOTES.md` — Phase 3.3 section's `resource.py` mentions updated
  to `cpu_memory.py` for accuracy (this file is a living reference, not
  an append-only historical diary like this one — see PROJECT_RULES.md
  Section 14).
- `CHECKLIST.md` — updated the collector task's inline note to reflect
  the rename (module name divergence now resolved; field-shape divergence
  still open); added a new "Phase 3.4 — Coordinator MVP" section (all 7
  tasks checked); Progress Summary updated to 55/85 (~65%).
- `ROADMAP.md` — Current Milestone moved to Phase 3.4 (complete);
  Upcoming Milestone updated to describe registering future collectors
  with the coordinator as they're built; added Phase 3.2C/3.3 and Phase
  3.4 summaries to "Eventually Completed," in chronological order.

**Reasoning**

The rename (`resource.py` → `cpu_memory.py`) was done first, before
touching the coordinator, because the coordinator's own registered-list
and validation logic needed to reference the collector by its *correct*,
final name (`cpu_memory`) rather than building against a name already
known to be a temporary placeholder. This closes the module-name half of
the divergence flagged in the Phase 3.3 entry above — the field-shape
half (flat bytes vs. nested kB, no `core_count`) remains open and is
still tracked.

The coordinator's error-handling design directly mirrors what every
collector already does, one level up: `system.py` and `cpu_memory.py`
each wrap their own internal failure points in narrow `try`/`except`
blocks and report failures as data rather than crashing; `run_scan()`
does the same thing for whole *collectors* — wrapping each
`collector_module.collect(context)` call so that one collector crashing
can never stop the loop from reaching the next one. This is explicitly
a **last-resort** safety net, not a substitute for a collector's own
error handling — both collectors built so far already handle every
anticipated failure internally and have never needed this catch to
actually trigger outside of the coordinator's own crash-path unit tests.

`_REGISTERED_COLLECTORS` is a plain list of imported modules, deliberately
not a registry class, decorator-based registration, or dynamic
discovery mechanism — directly following this task's own instruction to
avoid plugin systems. Adding a collector to a future scan will mean
adding one import and one list entry, nothing more.

`_validate_snapshot` is similarly minimal: a list-comprehension key check
and a `ValueError` with the missing keys named. With only two collectors
registered, every code path in `run_scan()` already guarantees `system`
and `cpu_memory` are populated (successfully or as a recorded crash with
`None`), so this check is a forward-looking defensive measure — a safety
net for a *coordinator* bug, not something today's collectors can
actually trigger.

**Important implementation notes**

- **Verified genuinely, not just written to spec:** `run_scan()` was run
  locally on macOS first (no `/proc`, no `hostname`-adjacent Linux tools
  missing) to confirm graceful degradation end to end — both collectors'
  fields correctly came back partially `None` with clear
  `collection_errors`, and `metadata.hostname` still correctly resolved
  from whatever `system` managed to determine. The full project was then
  copied to the Multipass Ubuntu 24.04 VM (`main-cattle`), a venv created,
  `pytest` installed, and the full 60-test suite run for real — all 60
  passed, including both new coordinator tests and the full integration
  test. A genuine, complete, zero-error sample snapshot was captured from
  the VM and saved locally to `snapshots/sample_snapshot.json` (gitignored
  per `PROJECT_RULES.md` Section 1 — not committed) for inspection. The
  temporary copy was removed from the VM afterward.
- **A test bug, caught and fixed during this task:** the first unit test
  for "every registered collector executes" used arbitrary fake names
  (`"alpha"`, `"beta"`) for the fake collectors, which correctly *failed*
  `_validate_snapshot`'s required-section check (since neither name is
  `system` or `cpu_memory`) — proving the validation check actually works,
  but also revealing the test itself was checking the wrong thing. Fixed
  by using `"system"`/`"cpu_memory"` as the fake names for that specific
  test, while a separate pair of tests exercises `_validate_snapshot`
  directly with deliberately-wrong section names.
- Quality review confirmed via `grep` that neither `system.py` nor
  `cpu_memory.py` imports the other or the coordinator — the only
  dependency in either direction is coordinator → collectors, which is
  the designed, expected relationship (see `docs/architecture.md`,
  "Dependency Flow"), not a violation of collector independence.
- Re-verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count: 55 complete, 30 remaining, 85 total (~65%).

**Future TODOs**

- Phase 3.2C: implement the `processes` collector next, and register it
  with the coordinator (`_REGISTERED_COLLECTORS`) as part of that task.
- Follow-up: decide whether to grow `run_scan()`'s `metadata` and
  top-level snapshot shape to fully match `docs/snapshot_schema.md`
  Sections 1–2 (top-level `timestamp`/`hostname`, `schema_version`, two
  scan timestamps, `collectors_run`/`collectors_skipped` lists), or update
  that schema doc to reflect the simpler MVP shape actually built — see
  `docs/coordinator.md`'s "MVP Simplifications."
- Phase 5 (CLI): wire `nodeiq scan` to call `run_scan()` and write the
  result to `snapshots/` as JSON — the first time a snapshot actually
  gets persisted to disk.
- Still open from prior entries: `_error_entry`/"read file, wrap as
  ValueError" duplication across collectors (revisit once a third
  collector exists, per ADR-012's threshold); `cpu_memory.py`'s
  field-shape divergence from `docs/snapshot_schema.md` Section 4;
  `PROJECT_RULES.md` Section 8 (Logging Philosophy) vs. ADR-013
  reconciliation; `dataclasses` vs. `TypedDict` decision for snapshot
  section shapes; `permissions` collector scope; `CONTEXT.md` Section 6
  clarifying note (optional); Multipass setup docs in `README.md`.

---

## 2026-07-15 — Phase 3.5A: Process Collector Design

**Task**

A design-and-learning-only phase, explicitly not an implementation task:
study how Linux exposes process information through `/proc`, and design
the Process Collector for NodeIQ v1 before writing any code. No
`src/nodeiq/collectors/processes.py`, no tests, and no change to
`_REGISTERED_COLLECTORS` were written, per this task's explicit scope.

**Files created**

- `docs/process_collector_design.md` — how Linux represents processes and
  why every PID gets a `/proc/<pid>` directory; a table of the
  `/proc/<pid>` files NodeIQ should use (`status`, `stat`, `cmdline`,
  `comm`) versus files intentionally ignored in v1 (`maps`/`smaps`,
  `environ`, `fd`/`fdinfo`, `mem`, `io`, `task/`, `cwd`/`root`/`exe`), each
  with a stated reason; a `/proc` vs. `ps` trade-off table; a proposed v1
  process schema (`pid`, `process_name`, `command`, `state`,
  `memory_rss_bytes`, `owner`, `start_time`, `threads`), each field with
  its Source, why it's useful, and whether it's required or optional; a
  full explanation of the five Linux process states (`R`, `S`, `D`, `T`,
  `Z`) and their operational significance; a recommended
  summarize-don't-dump strategy for feeding process data to the LLM
  (`process_count`, `top_by_memory`, zombie/`D`-state counts, explicitly
  *not* sending every process's full data); a review of
  `docs/snapshot_schema.md` Section 5's existing `processes` schema
  against this design, with recommended (not implemented) improvements; a
  Quality Review section; and a list of six explicit Open Design
  Questions left for whatever future task implements `processes.py`.

**Files modified**

- `README.md` — folder-structure diagram updated to list
  `docs/process_collector_design.md`.
- `CHECKLIST.md` — added a new "Phase 3.5A — Process Collector Design"
  section (all 5 tasks checked); updated the still-unchecked `processes`
  collector line under Phase 3.2C to note the design is now complete and
  point at the new doc; Progress Summary updated to 60/90 (~67%).
- `ROADMAP.md` — Current Milestone moved to Phase 3.5A (complete);
  Upcoming Milestone updated to "implement `processes.py` following the
  new design doc," then continue with the remaining collectors; added a
  Phase 3.5A summary to "Eventually Completed."
- `LEARNING_NOTES.md` — added beginner-friendly explanations of: what a
  PID is, what `/proc/<pid>` is and why every process gets a directory,
  the five Linux process states, and why a process collector is
  structurally more complex than every previous collector.

**Reasoning**

This design closes a real gap the previous two collectors didn't have to
deal with: `system.py` and `cpu_memory.py` each read a small, fixed set
of always-present files. The Process Collector instead has to *discover*
a dynamic, changing set of PIDs first, then read per-PID files that can
legitimately vanish between the discovery step and the read step (a
process exiting mid-scan) — this is a structurally new kind of failure
mode, and the design document calls it out explicitly (Section 5) as
something to handle per-PID (skip and move on), not as a collector-wide
error, consistent with this project's existing "partial data beats no
data" philosophy (`PROJECT_RULES.md` Section 7) but applied one level
more granular than any previous collector needed.

Following this project's established pattern for handling a real
divergence between a new design and an earlier, more abstractly-drafted
document (the same treatment given to `system.py`'s and `cpu_memory.py`'s
schema divergences), Section 9 of the new doc explicitly compares this
design against `docs/snapshot_schema.md` Section 5's existing `processes`
schema rather than silently matching or silently ignoring it. The
existing schema's summarize-first shape (`process_count`,
`top_by_memory`, `top_by_cpu`) turned out to already agree with this
design's own recommendation — a genuine point of alignment, not just a
gap to flag. The real gap found: the existing schema has no field at all
for zombie or `D`-state processes, despite Section 7 of the new design
making the case that `state` is the single most operationally significant
fact a process can report. This is recorded as a recommended (not
applied) schema improvement.

The proposed schema also deliberately does **not** include a per-process
CPU percentage, for the same reason `cpu_memory.py` deferred system-wide
CPU utilization (`docs/cpu_memory_collector.md`): a percentage requires
two `/proc` readings taken apart in time and a difference computed
between them, a meaningfully different collection strategy than every
other field in this design, which come from a single point-in-time read.
Deferring it here keeps the deferred-CPU-utilization decision consistent
across both collectors, rather than solving the same sub-problem
differently in two places.

**Important implementation notes**

- Real sample data was pulled from the Multipass Ubuntu 24.04 VM
  (`main-cattle`) before writing any of the design's file-format claims:
  `/proc/<pid>/status`, `/proc/<pid>/stat`, `/proc/<pid>/cmdline`,
  `/proc/<pid>/comm`, and `/proc/<pid>/io` were read for a real running
  process (PID 2835, a `bash` shell), and `/proc/1`'s directory listing
  and `ps aux` output were captured to ground the `/proc` vs. `ps`
  comparison in actual output rather than assumed formatting. A real,
  useful edge case was found this way: kernel threads (e.g. PID 2, `[kthreadd]`)
  have an empty `cmdline` file — recorded in the design doc as something
  a future parser must treat as a normal, expected case, not a parsing
  failure.
- No zombie process happened to exist on the VM at the time of this
  session (checked with `ps -eo pid,ppid,stat,comm`), which is itself
  expected — zombies are normally short-lived, and their absence doesn't
  change anything about the design (the `Z` state's behavior and
  operational significance are documented from Linux's own, well-defined
  semantics, not from having captured a live example).
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count (`grep -c` for `- [x]`/`- [ ]`): 60 complete, 30 remaining, 90
  total (~67%).
- Swept `docs/process_collector_design.md`'s own headings (`grep -n
  '^#'`) to confirm sequential, non-duplicated numbering before finishing.

**Future TODOs**

- Phase 3.2C: implement `collectors/processes.py`, following
  `docs/process_collector_design.md`'s recommended schema and
  summarization strategy, and register it with the coordinator
  (`_REGISTERED_COLLECTORS`) as part of that task.
- Phase 3.2C (as part of implementing `processes.py`, or a dedicated
  follow-up): resolve `docs/process_collector_design.md`'s six Open
  Design Questions — exact top-N value, whether `memory_percent` belongs
  in the collector or the future report generator, `owner` lookup-failure
  behavior, whether `command` needs redaction/truncation ahead of Phase
  7, whether to add `start_time` once `system.py` collects `boot_time`,
  and the `_bytes` vs. `_kb` unit convention across `processes` and
  `cpu_memory`.
- Recommend updating `docs/snapshot_schema.md` Section 5 to add a
  zombie/`D`-state count field once `processes.py` is actually
  implemented, per this design's review (Section 9) — not done now, since
  this task's scope was design and review, not schema edits.
- Still open from prior entries: `_error_entry`/"read file, wrap as
  ValueError" duplication across collectors (revisit once a third
  collector exists, per ADR-012's threshold — implementing `processes.py`
  would make this the third); `cpu_memory.py`'s field-shape divergence
  from `docs/snapshot_schema.md` Section 4; `PROJECT_RULES.md` Section 8
  (Logging Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs.
  `TypedDict` decision for snapshot section shapes; `permissions`
  collector scope; `CONTEXT.md` Section 6 clarifying note (optional);
  Multipass setup docs in `README.md`.

---

## 2026-07-15 — Phase 3.5B: Process Collector Implementation

**Task**

Implement the first version of the Process Collector, following the
design approved in Phase 3.5A (`docs/process_collector_design.md`). The
third real Linux collector: `process_count`, `zombie_count`,
`blocked_process_count` (state `D`), and the top 10 processes by memory
(`top_by_memory`), reading only `/proc/<pid>/status`, `cmdline`, and
`comm` directly — `ps` is never invoked, and `/proc/<pid>/stat` is
intentionally not parsed in v1. Registered with the coordinator and
verified end to end on the Multipass VM.

**Files created**

- `src/nodeiq/collectors/processes.py` — `collect(context) ->
  CollectorResult` plus private helpers: `_error_entry` (matching
  `system.py`/`cpu_memory.py`'s), `_discover_pids` (lists `/proc`'s
  numbered directory entries, raising `ValueError` only if `/proc`
  itself can't be listed at all), `_read_process` (reads one PID's
  `status`/`comm`/`cmdline`, returning `None` if the process has
  disappeared or its `status` is malformed), pure parsing helpers
  `_parse_status`/`_parse_state`/`_parse_vmrss`/`_parse_uid`/
  `_parse_cmdline`, `_resolve_owner` (UID → username via `pwd.getpwuid`,
  falling back to the numeric UID string), and `_summarize` (turns the
  full per-process list into the four summary fields actually returned).
- `tests/collectors/test_processes.py` — 24 unit tests: every `_parse_*`
  function tested with literal sample text (including the kernel-thread
  edge cases — absent `VmRSS`, empty `cmdline`); `_discover_pids` and
  `_read_process` tested via a monkeypatched `_PROC_ROOT` pointing at
  `tmp_path`, including a PID directory that doesn't exist at all and a
  malformed `status` file; `_resolve_owner` tested for both a successful
  and a failing `pwd.getpwuid`; `_summarize` tested for zombie/blocked
  counts and top-10 sorting/capping with more than 10 processes;
  `collect()` tested end-to-end for the happy path, a disappearing
  process being skipped without an error entry, and total `/proc`-listing
  failure producing exactly one error with every field `None`.
- `tests/collectors/test_processes_integration.py` — 1 integration test
  calling the real `collect()` with nothing mocked, skipped automatically
  unless `platform.system() == "Linux"`.
- `docs/process_collector.md` — responsibilities; why `/proc` was used
  instead of `ps` (with a real command comparison); why `stat` was
  intentionally deferred; a detailed "Race Conditions When Scanning
  Processes" section explaining the discover-then-read race and how
  `_read_process` handles it; a field-by-field explanation table; "A Note
  on Naming and Schema Alignment" comparing this implementation against
  `docs/snapshot_schema.md` Section 5; and a Collector Review Checklist.

**Files modified**

- `src/nodeiq/core/coordinator.py` — `_REGISTERED_COLLECTORS` now
  `[system, cpu_memory, processes]`; `_REQUIRED_SECTIONS` now includes
  `"processes"`; `run_scan()`'s docstring example updated to show the
  `"processes"` key.
- `src/nodeiq/collectors/__init__.py` — updated to note `processes.py` is
  now built alongside `system.py` and `cpu_memory.py`.
- `tests/core/test_coordinator.py` — every test that monkeypatches
  `_REGISTERED_COLLECTORS` now includes a fake `"processes"` collector
  (needed for `_validate_snapshot`'s required-section check to keep
  passing); `collector_count` assertions updated from `2` to `3`.
- `tests/core/test_coordinator_integration.py` — updated to expect the
  real `run_scan()` to return a `"processes"` section, `collector_count
  == 3`, and added assertions on `processes`' real, sane data
  (`process_count > 0`, non-negative zombie/blocked counts, `top_by_memory`
  capped at 10).
- `docs/coordinator.md` — "MVP Simplifications" corrected from "only two
  collectors registered, `collector_count` always `2`" to three
  collectors and `3`; snapshot-assembly example, `_validate_snapshot`'s
  required-key list, and the Testing section's numbers (11 unit tests,
  now an 88-test full suite) updated for accuracy.
- `docs/architecture.md` — status line, the `nodeiq.collectors` section
  heading and body, and `_REGISTERED_COLLECTORS`'s example value updated
  from "two collectors built" to "three collectors built."
- `README.md` — folder-structure diagram updated to list
  `docs/process_collector.md` and to mention `processes.py`.
- `CHECKLIST.md` — checked off the `processes` collector task under
  Phase 3.2C (noting what was actually built); added a new "Phase 3.5B —
  Process Collector Implementation" section (all 6 tasks checked);
  Progress Summary updated to 67/96 (~70%).
- `ROADMAP.md` — Current Milestone moved to Phase 3.5B (complete);
  Upcoming Milestone updated to describe the remaining six collectors
  (`disk`, `services`, `logs`, `network`, `scheduled_jobs`,
  `permissions`); added a Phase 3.5B summary to "Eventually Completed."
- `LEARNING_NOTES.md` — added beginner-friendly explanations of: what RSS
  memory is, why zombie processes matter, why `D`-state processes matter,
  and why processes can disappear mid-scan.

**Reasoning**

Every design choice here traces directly back to a specific
recommendation in `docs/process_collector_design.md`, rather than being
decided fresh: `status`/`cmdline`/`comm` were the three files the design
recommended (Section 3); `stat` was excluded per the design's own
reasoning (positional parsing is fragier than named fields, and its main
payoff — CPU time — isn't usable without the same two-reading strategy
`cpu_memory.py` already deferred); the four summary fields
(`process_count`, `zombie_count`, `blocked_process_count`,
`top_by_memory`) match the design's "Recommended Process Summarization
Strategy" (Section 8) exactly, including the top-10 default this task's
own instructions confirmed.

The one genuinely new architectural pattern in this collector — absent
from every previous one — is the discover-then-read-per-PID structure,
and with it, a real race condition: a process can exit between
`_discover_pids` listing it and `_read_process` actually reading its
files. This is handled at exactly the point the design predicted it
would need to be (`docs/process_collector_design.md` Section 5):
`_read_process` catches `OSError` from any of its three file reads and
returns `None`, and `collect()` simply skips any `None` result — no
`collection_errors` entry is ever produced for this case, per this
task's explicit instruction. This is a deliberately different failure
handling shape from every other anticipated failure in this collector
(and from every previous collector's failures in general): a disappeared
process is not treated as data (`None` plus an error entry, the pattern
`system.py`/`cpu_memory.py` use for their own field failures) — it's
treated as if that PID was simply never seen, since the alternative
(counting it, but with the fields it never got a chance to report)
would be actively misleading.

`owner` resolution follows exactly the graceful-degradation
recommendation from `docs/process_collector_design.md`'s Open Design
Question 3: `pwd.getpwuid` is tried first, and a `KeyError` (no matching
user) falls back to the numeric UID as a string rather than omitting
`owner` or raising — a raw UID is still real, useful evidence about who
is running a process, even without a resolved name.

Field-naming/unit divergences from `docs/snapshot_schema.md` Section 5
(`process_name` vs. `name`, `memory_rss_bytes` vs. `memory_kb`) and the
two fields not implemented (`memory_percent`, `top_by_cpu`) are recorded
explicitly in `docs/process_collector.md`'s "A Note on Naming and Schema
Alignment," following the same established pattern as `system.py` and
`cpu_memory.py` — not resolved here, since resolving them wasn't part of
this task's scope and doing so silently would hide a real, still-open
question.

**Important implementation notes**

- **Verified genuinely, not just written to spec:** the full project was
  copied to the Multipass Ubuntu 24.04 VM (`main-cattle`), a venv
  created, dependencies installed, and the full 88-test suite run for
  real — all passed, including this collector's own integration test and
  the coordinator's end-to-end integration test (now covering all three
  collectors). A real sample snapshot was captured showing 91 real
  processes, a correctly memory-sorted top 10, and correct owner
  resolution for multiple real UIDs (`root`, `ubuntu`,
  `systemd-resolve`) — saved locally to `snapshots/sample_snapshot.json`
  (gitignored, not committed) for inspection. The temporary copy was
  removed from the VM afterward.
- Verified the collector also degrades gracefully on the local macOS dev
  machine, which has no `/proc` at all: `_discover_pids` raises
  `ValueError`, `collect()` returns exactly one `collection_errors` entry
  for `"processes"`, and every summary field comes back `None` — the same
  shape of graceful degradation `system.py` and `cpu_memory.py` already
  demonstrate for their own missing-`/proc` case on macOS.
- **The ADR-012 "three or more collectors" duplication threshold has now
  been crossed.** `_error_entry` is now duplicated verbatim across
  `system.py`, `cpu_memory.py`, and `processes.py` — exactly the
  condition ADR-012 named as the point to revisit extracting a shared
  helper into `nodeiq.core`, from evidence rather than speculation. This
  was noted but **not acted on** in this task, since extracting a
  cross-collector helper wasn't part of this task's explicit scope —
  flagged explicitly here as a ready-to-do follow-up rather than done
  silently or ignored.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count (`grep -c` for `- [x]`/`- [ ]`): 67 complete, 29 remaining, 96
  total (~70%).
- Swept every touched file's headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Future TODOs**

- Phase 3.2C: implement the `disk` + inodes collector next, following
  `system.py`/`cpu_memory.py`/`processes.py` as templates.
- Now ready to act on (ADR-012's threshold crossed by this task):
  extract a shared `_error_entry` helper (and consider the "read file,
  wrap as ValueError" pattern) into `nodeiq.core`, now that three
  collectors show the same duplication.
- Resolve `docs/process_collector_design.md`'s remaining Open Design
  Questions not settled by this implementation: exact top-N value
  (currently `10`, not revisited), whether `memory_percent` belongs in a
  future report generator, whether `command` needs redaction/truncation
  ahead of Phase 7, whether to add `start_time` once `system.py` collects
  `boot_time`, and the `_bytes` vs. `_kb` unit convention across
  `processes` and `cpu_memory`.
- A future increment could add per-process CPU utilization (via
  `/proc/<pid>/stat`, requiring two readings apart in time, same as
  `cpu_memory.py`'s deferred system-wide CPU work) and `top_by_cpu` — see
  `docs/process_collector.md`'s "Why `stat` Was Intentionally Deferred."
- Still open from prior entries: `cpu_memory.py`'s field-shape divergence
  from `docs/snapshot_schema.md` Section 4; `PROJECT_RULES.md` Section 8
  (Logging Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs.
  `TypedDict` decision for snapshot section shapes; `permissions`
  collector scope; `CONTEXT.md` Section 6 clarifying note (optional);
  Multipass setup docs in `README.md`.

---

## 2026-07-15 — Phase 3.6: Disk + Inodes Collector

**Task**

Implement the Disk Collector: filesystem capacity and inode usage for
every mounted filesystem, merged into one entry per filesystem, plus
scan-wide `highest_disk_usage_percent`/`highest_inode_usage_percent`.
The fourth real Linux collector, and the first that needs commands
(`df -P -B1`, `df -P -i`) rather than a `/proc` file, since no single
kernel-provided file exposes this information in machine-readable form.
Registered with the coordinator and verified end to end on the
Multipass VM.

**Files created**

- `src/nodeiq/collectors/disk.py` — `collect(context) -> CollectorResult`
  plus private helpers: `_error_entry` (matching every prior collector's),
  `_get_disk_usage`/`_parse_df_output` (runs `df -P -B1`, parses it into
  a list of per-filesystem dicts), `_get_inode_usage`/
  `_parse_df_inode_output` (runs `df -P -i`, parses it into a dict keyed
  by mount point), `_parse_percent`/`_parse_optional_int` (shared by both
  parsers, handling `df`'s `-` "not applicable" convention as `None`),
  `_merge_filesystems` (combines the two by mount point), and `_highest`
  (the scan-wide maximum of a field across every filesystem that has
  one).
- `tests/collectors/test_disk.py` — 24 unit tests: `_parse_df_output` and
  `_parse_df_inode_output` tested with literal sample text (a mount
  point containing a space, a malformed line, and the real
  `efivarfs`-style `-` inode case pulled from the VM); `_parse_percent`/
  `_parse_optional_int` tested for valid values, `-`, and garbage;
  `_merge_filesystems` tested for a full match and a missing inode
  entry; `_highest` tested for the normal case, `None`-filtering, an
  all-`None` list, and an empty list; `collect()` tested end-to-end for
  the happy path, total disk-usage-command failure, and
  inode-command-only failure.
- `tests/collectors/test_disk_integration.py` — 1 integration test
  calling the real `collect()` with nothing mocked, skipped
  automatically unless `platform.system() == "Linux"`.
- `docs/disk_collector.md` — responsibilities; what a filesystem is;
  what an inode is and why inode exhaustion matters (a filesystem can be
  mostly empty by space yet unable to create a single new file); why
  `df` was chosen (no kernel file for this exists, and why `-P` and
  `-B1` were both added); how the two command outputs are merged; error
  handling for each partial-failure mode; "A Note on Naming and Schema
  Alignment" comparing this implementation against
  `docs/snapshot_schema.md` Section 6; and a Collector Review Checklist.

**Files modified**

- `src/nodeiq/core/coordinator.py` — `_REGISTERED_COLLECTORS` now
  `[system, cpu_memory, processes, disk]`; `_REQUIRED_SECTIONS` now
  includes `"disk"`; `run_scan()`'s docstring example updated to show
  the `"disk"` key.
- `src/nodeiq/collectors/__init__.py` — updated to note `disk.py` is now
  built alongside the other three collectors.
- `tests/core/test_coordinator.py` — every test that monkeypatches
  `_REGISTERED_COLLECTORS` now includes a fake `"disk"` collector;
  `collector_count` assertions updated from `3` to `4`.
- `tests/core/test_coordinator_integration.py` — updated to expect the
  real `run_scan()` to return a `"disk"` section, `collector_count == 4`,
  and added assertions on `disk`'s real, sane data (at least one
  filesystem, `highest_disk_usage_percent` between 0 and 100).
- `README.md` — folder-structure diagram updated to list
  `docs/disk_collector.md` and to mention `disk.py`.
- `CHECKLIST.md` — checked off the `disk` collector task under Phase
  3.2C (noting what was actually built); added a new "Phase 3.6 — Disk +
  Inodes Collector" section (all 7 tasks checked); Progress Summary
  updated to 75/103 (~73%).
- `ROADMAP.md` — Current Milestone moved to Phase 3.6 (complete);
  Upcoming Milestone updated to describe the remaining five collectors
  (`services`, `logs`, `network`, `scheduled_jobs`, `permissions`); added
  a Phase 3.6 summary to "Eventually Completed."
- `LEARNING_NOTES.md` — added beginner-friendly explanations of: what a
  filesystem is, what a mount point is, what an inode is, and why a disk
  can be only 40% full by space and still fail to write a new file.

**Reasoning**

This is the first collector where `PROJECT_RULES.md` Section 9 (item
7)'s usual preference — a kernel file over a command — simply doesn't
apply: there's no `/proc` entry that reports total/used/available bytes
and inodes for every mounted filesystem the way `/proc/meminfo` does for
memory. `df` itself is built on the same `statvfs()` system call this
collector would otherwise have to call directly, so running `df` isn't
a compromise — it's the same canonical interface any other tool
(including one written from scratch) would end up using anyway,
consistent with the task's own stated reasoning.

Two separate `df` invocations were merged rather than one, because `df`
can't report both capacity and inode usage in a single call. Following
`docs/collector_guidelines.md`'s "Separation of Command Execution and
Parsing," each invocation gets its own pure parser
(`_parse_df_output`/`_parse_df_inode_output`), and a third, separate
function (`_merge_filesystems`) does only the combining — keeping "parse
this command's output" and "combine two already-parsed things" as two
distinct jobs, neither aware of the other's existence.

`-P` was added to both `df` invocations beyond what the task's literal
"Use: `df -B1`, `df -i`" instruction specified. This isn't scope
creep — `docs/collector_guidelines.md`'s own illustrative `disk.py`
pseudocode already establishes `run_command(["df", "-P", "-k"], ...)`
as this project's expected convention, specifically because `df` can
wrap a filesystem's row onto two lines when its device name is long
enough to overflow a column, and this collector's parser assumes
exactly one line per filesystem. Adding `-P` was necessary for the
parser to be reliably correct, not just a style preference, and is
flagged here explicitly per this project's practice of calling out any
implementation choice a task's literal wording didn't already spell out.

The `-` handling (`_parse_percent`/`_parse_optional_int` returning
`None` for a literal `-` token) exists because real VM output showed
`efivarfs` and the `/boot/efi` `vfat` partition reporting `-` for every
inode field — these filesystems don't support the inode concept at all.
This is the same "genuinely doesn't apply" vs. "couldn't determine"
distinction `PROJECT_RULES.md` Section 7 requires everywhere else in
this project, applied to a new kind of "not applicable" signal (a
literal dash from the tool itself, rather than a missing file or a
failed command).

**Important implementation notes**

- **Verified genuinely, not just written to spec:** real `df -P -B1`
  and `df -P -i` output was pulled from the Multipass VM
  (`main-cattle`) *before* writing the parser, confirming both the
  column layout and the real `efivarfs`/`/boot/efi` `-` inode case. The
  full project was then copied to the VM (excluding `.git` and `.venv`,
  which caused SFTP permission errors on a first attempt due to a stale
  nested transfer from an in-progress prior copy — resolved by building
  a clean, `rsync`-filtered local copy first and confirming the VM's old
  copy was fully removed, with a pause to let the removal actually
  complete, before transferring again) and the full 111-test suite was
  run for real — all passed, including this collector's own integration
  test and the coordinator's end-to-end integration test (now covering
  all four collectors), producing a real, correctly-merged 8-filesystem
  snapshot with accurate `None` handling for `efivarfs`/`/boot/efi` and
  `highest_disk_usage_percent`/`highest_inode_usage_percent` computed
  correctly (60.0/24.0). Saved locally to `snapshots/sample_snapshot.json`
  (gitignored, not committed) for inspection. The temporary copy was
  removed from the VM afterward.
- Verified the collector also degrades gracefully on the local macOS dev
  machine, whose BSD `df` doesn't support `-B1` at all
  (`df: invalid option -- B`): `_get_disk_usage` raises `ValueError`,
  `collect()` returns exactly one `collection_errors` entry, and
  `filesystems` comes back `[]` with both `highest_*` fields `None` —
  the same shape of graceful degradation every previous collector
  already demonstrates for its own platform-specific gap.
- **The ADR-012 "three or more collectors" duplication threshold,
  already flagged as crossed in the previous entry, is now even more
  clearly true.** `_error_entry` is now duplicated verbatim across all
  four real collectors (`system.py`, `cpu_memory.py`, `processes.py`,
  `disk.py`). Still not acted on in this task, for the same reason as
  before — extracting a shared helper wasn't part of this task's
  explicit scope — but it's now a more pressing, ready-to-do follow-up
  than it was last time.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count (`grep -c` for `- [x]`/`- [ ]`): 75 complete, 28 remaining, 103
  total (~73%).
- Swept every touched file's headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Future TODOs**

- Phase 3.2C: implement the `services` collector next, following
  `system.py`/`cpu_memory.py`/`processes.py`/`disk.py` as templates —
  the first collector needing an explicit "systemd not found" path per
  `DECISIONS.md` ADR-010.
- Now genuinely overdue: extract a shared `_error_entry` helper into
  `nodeiq.core`, now that all four collectors show the identical
  duplication (crossed ADR-012's "three or more" threshold two
  collectors ago).
- Consider adding `filesystem_type` (e.g. `ext4`) to `disk.py`'s output
  — would require a third command (`df -T`) or parsing `/proc/mounts`;
  not part of this task's scope.
- Still open from prior entries: field-naming/unit divergences across
  `cpu_memory.py`/`processes.py`/`disk.py` vs. `docs/snapshot_schema.md`;
  `docs/process_collector_design.md`'s remaining Open Design Questions;
  per-process CPU utilization and `top_by_cpu`; `PROJECT_RULES.md`
  Section 8 (Logging Philosophy) vs. ADR-013 reconciliation;
  `dataclasses` vs. `TypedDict` decision for snapshot section shapes;
  `permissions` collector scope; `CONTEXT.md` Section 6 clarifying note
  (optional); Multipass setup docs in `README.md`.

---

## 2026-07-15 — Collector Sprint 1: Services, Scheduled Jobs, Permissions

**Task**

Implement three collectors in one sprint, per explicit instruction to
focus on implementation/correctness/testing/integration and *not*
perform cross-collector refactoring — any duplication noticed was to be
recorded under "Refactoring Opportunities" only, deferred to a later
refactoring sprint:

1. **Services** (`services.py`) — systemd service health via `systemctl`.
2. **Scheduled Jobs** (`scheduled_jobs.py`) — cron jobs and systemd
   timers.
3. **Permissions** (`permissions.py`) — ownership/permission facts for a
   conservative, fixed path list.

All three registered with the coordinator in the same task. Per this
task's own documentation-scope instruction, only `CHECKLIST.md` and
`LOGS.md` are updated here — `README.md`, `ROADMAP.md`, and
`LEARNING_NOTES.md` are deliberately left untouched, since nothing in
this sprint constitutes the kind of major architectural change those
files are reserved for.

**Files created**

- `src/nodeiq/collectors/services.py` — `collect(context) ->
  CollectorResult` plus `_error_entry`, `_get_service_units`/
  `_parse_service_units` (runs `systemctl list-units --type=service
  --all`), `_summarize_services` (running/failed counts,
  `failed_services`, `restarting_services` via sub-state
  `auto-restart`), and `_get_unit_file_states`/`_parse_unit_files` (runs
  `systemctl list-unit-files --type=service`, for
  `enabled_services_count`). `systemd_available` (DECISIONS.md ADR-010)
  is `False` only if the first command fails outright.
- `src/nodeiq/collectors/scheduled_jobs.py` — `collect(context) ->
  CollectorResult` plus `_error_entry`, `_get_system_cron_jobs`/
  `_parse_system_crontab_line` (reads `/etc/crontab` and every file in
  `/etc/cron.d/`), `_get_user_cron_jobs`/`_parse_user_crontab_line`
  (reads every accessible file in `/var/spool/cron/crontabs/`), and
  `_get_systemd_timers`/`_parse_list_timers` (runs `systemctl
  list-timers --all`, extracting only the timer name and activated
  service — the last two tokens on each line — deliberately not parsing
  the fragile human-formatted NEXT/LAST date columns).
- `src/nodeiq/collectors/permissions.py` — `collect(context) ->
  CollectorResult` plus `_error_entry`, `_check_path` (three-outcome
  `stat()` handling: exists, genuinely doesn't exist, or a real error),
  `_entry_from_stat`/`_empty_entry`, and `_resolve_owner`/`_resolve_group`
  (UID/GID → name, falling back to the numeric ID string). Needs no
  commands at all — checks `/etc/passwd`, `/etc/shadow`, `/etc/ssh`, and
  `/var/log`.
- `tests/collectors/test_services.py` (11 tests), `test_scheduled_jobs.py`
  (16 tests), `test_permissions.py` (10 tests) — parsing, merge/summary
  logic, and `collect()` end-to-end (happy path and every partial-failure
  mode) for each collector, all mocked or redirected to `tmp_path`.
- `tests/collectors/test_services_integration.py`,
  `test_scheduled_jobs_integration.py`, `test_permissions_integration.py`
  — one real, unmocked integration test per collector each, skipped
  automatically unless `platform.system() == "Linux"`.
- `docs/services_collector.md`, `docs/scheduled_jobs_collector.md`,
  `docs/permissions_collector.md` — responsibilities, data-source
  rationale, error-handling design, schema-alignment notes, and a
  Collector Review Checklist for each.

**Files modified**

- `src/nodeiq/core/coordinator.py` — `_REGISTERED_COLLECTORS` now
  `[system, cpu_memory, processes, disk, services, scheduled_jobs,
  permissions]`; `_REQUIRED_SECTIONS` now includes `"services"`,
  `"scheduled_jobs"`, and `"permissions"`; `run_scan()`'s docstring
  example updated to show all three new keys.
- `src/nodeiq/collectors/__init__.py` — updated to note all three new
  collectors are now built.
- `tests/core/test_coordinator.py` — every test that monkeypatches
  `_REGISTERED_COLLECTORS` now includes fake `"services"`,
  `"scheduled_jobs"`, and `"permissions"` collectors; `collector_count`
  assertions updated from `4` to `7`.
- `tests/core/test_coordinator_integration.py` — updated to expect the
  real `run_scan()` to return `"services"`, `"scheduled_jobs"`, and
  `"permissions"` sections, `collector_count == 7`, and added assertions
  on each new section's real, sane data.
- `CHECKLIST.md` — checked off the `services`, `scheduled_jobs`, and
  `permissions` collector tasks under Phase 3.2C; added a new "Collector
  Sprint 1" section (all 7 tasks checked); Progress Summary updated to
  85/110 (~77%).

**Reasoning**

Each collector's data-gathering strategy follows a precedent already
established by an earlier collector, rather than inventing a new
approach: `services.py` runs two independent `systemctl` invocations and
merges them, the same "two independent command-based sources, one
whose total failure means total failure, one whose failure only costs
part of the output" shape `disk.py` already established for `df -P -B1`/
`df -P -i`. `scheduled_jobs.py` reads cron files directly rather than
shelling out to `crontab -l`, matching `PROJECT_RULES.md` Section 9
(item 7)'s standing preference for a direct interface over a command
wrapper — the same reasoning `system.py` and `cpu_memory.py` already
applied to `/proc` files, just applied here to on-disk cron files
instead. `permissions.py` needs no commands at all, extending that same
principle to its natural conclusion, and reuses `processes.py`'s
UID-resolution pattern (extended with the equivalent GID lookup).

The most interesting new design decision was in `scheduled_jobs.py`:
`systemctl list-timers`'s NEXT/LAST columns are human-formatted,
locale-dependent absolute-plus-relative time strings ("3h 48min",
"9min ago") that would be fragile to parse positionally. Rather than
attempting that parsing (or skipping timers whose format looked unusual),
`_parse_list_timers` takes advantage of a simpler, robust fact: a
timer's own name and the service it activates are *always* the last two
whitespace-separated tokens on every line, regardless of what precedes
them, since unit names never contain spaces. This sidesteps the whole
date-parsing problem entirely and is recorded as an intentional
deferral (not a silent omission) of `next_run`/`last_run`, per
`docs/snapshot_schema.md` Section 10.

`permissions.py`'s `_check_path` distinguishes **three** outcomes, not
two: a path existing (full data), a path genuinely not existing
(`exists: False`, no error — a real, valid fact), and a path that
couldn't be `stat()`-ed for another reason (`exists: None`, *with* an
error entry). Collapsing the second and third into one `exists: False`
would have repeated exactly the mistake `PROJECT_RULES.md` Section 7
warns against — conflating "the system genuinely has none of this" with
"we couldn't check."

Personal crontabs (`/var/spool/cron/crontabs/`) were read directly
rather than via `crontab -l -u <user>`, specifically because real
permissions on this directory (`drwx-wx--T root crontab`) mean even a
`crontab`-group member can't *list* it directly — only the privileged
`crontab` command can. This was verified for real on the Multipass VM:
listing the directory as the non-root `ubuntu` user genuinely fails
with `Permission denied`, confirming this is the actual, expected access
boundary this collector needed to handle gracefully, not a hypothetical
edge case.

**Important implementation notes**

- **Verified genuinely, not just written to spec:** real `systemctl
  list-units`/`list-unit-files`/`list-timers` output, real
  `/etc/crontab`/`/etc/cron.d/*` content, and real
  `/var/spool/cron/crontabs/` permissions were all pulled from the
  Multipass VM (`main-cattle`) *before* writing any parser, including
  confirming the non-root permission-denied case for the cron spool
  directory. The full project was then copied to the VM (via a clean,
  `rsync`-filtered local copy excluding `.git`/`.venv`, with an explicit
  pause after removing any stale prior copy — the same procedure
  established in the Phase 3.6 entry after an earlier transfer race) and
  the full 151-test suite was run for real — all passed, including all
  six new collector tests (unit + integration, three collectors) and the
  coordinator's end-to-end integration test (now covering all seven
  collectors). A real, complete, error-free snapshot was captured
  showing 54 running services (0 failed, 45 enabled), 8 real system cron
  jobs correctly attributed to their source files, 17 real systemd
  timers, and all four permission-checked paths present with correct
  ownership (including `/etc/shadow` at `root:shadow`, mode `640`).
  Saved locally to `snapshots/sample_snapshot.json` (gitignored, not
  committed). The temporary copy was removed from the VM afterward.
- Verified all three collectors also degrade gracefully on the local
  macOS dev machine: `services.py` correctly reports
  `systemd_available: False` (no `systemctl`); `scheduled_jobs.py`
  correctly reports zero cron jobs (no `/etc/crontab`/`/etc/cron.d` on
  this Mac) alongside a real recorded error for the failing
  `list-timers` call; `permissions.py` — needing no subprocess at all —
  works natively on macOS, correctly reporting real `/etc/passwd`,
  `/etc/ssh`, and `/var/log` data and `/etc/shadow` as `exists: False`
  (macOS has no such file).
- **A test bug caught and fixed during this task:** the first version of
  `test_collect_continues_past_a_path_that_cannot_be_checked` in
  `test_permissions.py` monkeypatched `permissions._check_path` with a
  fake that, for its non-error branch, called `permissions._check_path`
  again — which by then referred to the *replacement* itself, causing
  infinite recursion. Fixed by capturing the real function into a local
  variable before patching and calling that instead.
- Quality review performed on all three collectors per this task's
  explicit request, without refactoring — see Refactoring Opportunities
  below, all deliberately left for a later, dedicated refactoring
  sprint.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count (`grep -c` for `- [x]`/`- [ ]`): 85 complete, 25 remaining, 110
  total (~77%).
- Swept every touched file's headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Refactoring Opportunities (recorded only, not acted on this sprint)**

1. **`_error_entry` is now duplicated verbatim across all seven real
   collectors** (`system.py`, `cpu_memory.py`, `processes.py`,
   `disk.py`, `services.py`, `scheduled_jobs.py`, `permissions.py`).
   Far past ADR-012's "three or more" threshold — a strong candidate to
   extract into a shared `nodeiq.core` helper in the dedicated
   refactoring sprint.
2. **`_resolve_owner` (UID → username, falling back to the numeric UID
   string on `KeyError`) is now duplicated verbatim between
   `processes.py` and `permissions.py`.** `permissions.py`'s
   `_resolve_group` is the same shape again, one level over (GID →
   group name). All three could plausibly share one small
   `nodeiq.core` helper.
3. **The "command failed" error-message construction** (`f"{'
   '.join(command)} failed: {result.error or result.stderr.strip()}"`)
   is now duplicated across `system.py`, `disk.py`, `services.py`
   (twice), and `scheduled_jobs.py` — a candidate for a shared
   `_command_failure_message(command, result)` helper.
4. **`scheduled_jobs.py`'s `_parse_system_crontab_line` and
   `_parse_user_crontab_line` share about 10 lines of near-identical
   structure** (schedule extraction, `@special` handling) — kept
   separate deliberately for readability (`PROJECT_RULES.md` Section 3
   favors explicit over clever), but the duplication is real and worth
   revisiting.
5. **`services.py` and `disk.py` share a recurring structural shape**:
   two independent command-based data sources, where one's total
   failure means total failure and the other's failure only costs part
   of the output. Not literal code duplication, but an emerging pattern
   worth naming/documenting explicitly if a fourth collector repeats it.

**Future TODOs**

- Phase 3.2C: implement the `logs` and `network` collectors next —
  `logs` will need a bounded/truncated `journalctl` read
  (`docs/snapshot_schema.md` Section 8's `truncated` flag) and secret
  redaction is a real, non-hypothetical concern there ahead of Phase 7;
  `network` will need `ss`/`ip` parsing.
- A dedicated refactoring sprint should work through this entry's five
  Refactoring Opportunities, now that seven real collectors exist to
  draw genuine, evidence-based shared abstractions from (per ADR-012's
  own "extract from evidence, not speculation" principle).
- Still open from prior entries: field-naming/unit divergences across
  `cpu_memory.py`/`processes.py`/`disk.py` vs. `docs/snapshot_schema.md`;
  `docs/process_collector_design.md`'s remaining Open Design Questions;
  per-process CPU utilization and `top_by_cpu`; `docs/disk_collector.md`'s
  deferred `filesystem_type`; `PROJECT_RULES.md` Section 8 (Logging
  Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs. `TypedDict`
  decision for snapshot section shapes; `CONTEXT.md` Section 6
  clarifying note (optional); Multipass setup docs in `README.md`.

---

## 2026-07-15 — Collector Sprint 2: Network, Logs (NodeIQ v1 Collector Set Complete)

**Task**

Implement the final two collectors, completing NodeIQ v1's entire data
collection layer (all 9 collectors from `CONTEXT.md` Section 6 now
built):

1. **Network** (`network.py`) — interfaces, default route, listening
   ports, best-effort firewall detection.
2. **Logs** (`logs.py`) — recent warning/error entries from the systemd
   journal, bounded and summarized.

Both registered with the coordinator in the same task. Per this task's
own documentation-scope instruction, only `CHECKLIST.md` and `LOGS.md`
are updated here — `README.md`, `ROADMAP.md`, and `LEARNING_NOTES.md`
are deliberately left untouched.

**Files created**

- `src/nodeiq/collectors/network.py` — `collect(context) ->
  CollectorResult` plus `_error_entry`, `_get_interface_states`/
  `_parse_interface_states`/`_extract_flags` (runs `ip -o link show`;
  reads the `<FLAGS>` bracket for up/down, not the `state` keyword, which
  is `UNKNOWN` for loopback — a real kernel quirk), `_get_interface_addresses`/
  `_parse_interface_addresses` (runs `ip -o addr show`), `_merge_interfaces`,
  `_get_default_route`/`_parse_default_route` (runs `ip route show
  default`), `_get_listening_ports`/`_parse_ss_output`/`_parse_process_field`
  (runs `ss -tulpn`; handles scoped `%interface` addresses and IPv6
  bracket addresses via `rpartition`, and a genuinely absent process
  column when unprivileged), and `_detect_firewall`/`_parse_ufw_status`
  (tries `ufw`, then `nft`, then `iptables`, in that order; never
  contributes an error, since none being usable is normal for an
  unprivileged scan).
- `src/nodeiq/collectors/logs.py` — `collect(context) -> CollectorResult`
  plus `_error_entry`, `_get_recent_log_entries`/`_parse_journal_json`
  (runs `journalctl -p warning -n 100 --no-pager -o json`, one JSON
  object per line), `_parse_journal_record`/`_parse_timestamp`/
  `_parse_severity`/`_parse_message` (handles a missing unit field, a
  non-UTF-8 `MESSAGE` byte-array, and priority-to-severity mapping), and
  `_summarize_entries` (`warning_count`, `error_count`, and an honest
  `truncated` flag based on hitting the `_MAX_ENTRIES` cap).
- `tests/collectors/test_network.py` (25 tests), `test_logs.py` (19
  tests) — parsing, merge/summary logic, and `collect()` end-to-end
  (happy path and every partial-failure mode) for each collector, all
  mocked.
- `tests/collectors/test_network_integration.py`,
  `test_logs_integration.py` — one real, unmocked integration test per
  collector, skipped automatically unless `platform.system() ==
  "Linux"`.
- `docs/network_collector.md`, `docs/logs_collector.md` —
  responsibilities, data-source rationale, real edge cases discovered
  and handled, error-handling design, schema-alignment notes, and a
  Collector Review Checklist for each.

**Files modified**

- `src/nodeiq/core/coordinator.py` — `_REGISTERED_COLLECTORS` now
  `[system, cpu_memory, processes, disk, services, scheduled_jobs,
  permissions, network, logs]` — all 9 collectors; `_REQUIRED_SECTIONS`
  now includes `"network"` and `"logs"`; `run_scan()`'s docstring
  example updated to show both new keys.
- `src/nodeiq/collectors/__init__.py` — updated to note both new
  collectors are built and that this is now the complete NodeIQ v1
  collector set (no further collectors planned).
- `tests/core/test_coordinator.py` — every test that monkeypatches
  `_REGISTERED_COLLECTORS` now includes fake `"network"` and `"logs"`
  collectors; `collector_count` assertions updated from `7` to `9`.
- `tests/core/test_coordinator_integration.py` — updated to expect the
  real `run_scan()` to return `"network"` and `"logs"` sections,
  `collector_count == 9`, and added assertions on each new section's
  real, sane data.
- `CHECKLIST.md` — checked off the `logs` and `network` collector tasks
  under Phase 3.2C (now **complete, all 9 of 9**); added a new
  "Collector Sprint 2" section (all 6 tasks checked); Progress Summary
  updated to 93/116 (~80%), noting NodeIQ v1's data collection layer is
  now complete.

**Reasoning**

`network.py` needed four independent command-based sources merged into
one result — the most sources any single collector has combined so far.
Interfaces follow the same two-source-merge-by-key pattern already
established by `disk.py` (mount point) and now applied to interface
name; this consistency meant the merge logic itself required no new
design thinking, only a new key and new fields.

The single most important real-world finding this sprint was that
**every firewall tool requires root to report its status at all** —
verified directly on the Multipass VM as the non-root `ubuntu` user:
`ufw status`, `nft list ruleset`, and `iptables -L -n` all fail with a
permission error. This confirmed that `_detect_firewall` returning
`{"tool": None, "enabled": None}` is the *normal*, expected outcome for
most real scans, not a rare edge case — and is exactly why this path
never contributes a `collection_errors` entry, unlike every other
command failure in this collector.

`logs.py` chose `journalctl`'s own `--output=json` mode over its default
human-oriented text output — the same "prefer the machine-readable
interface" principle applied throughout this project, here taken to its
most direct form: journald's own structured export, rather than a flag
that merely makes text easier to parse (contrast with `ip -o` or
`systemctl --plain`, which reformat text that still needs parsing).
This sidestepped what would otherwise have been the hardest parsing
problem in this sprint (extracting severity, timestamp, and unit name
from free-form text) by using data journald already structures.

**Important implementation notes**

- **A real bug was found and fixed during this sprint's own quality
  review, before committing:** `_detect_firewall`'s original `ufw`
  parsing checked `"active" in first_line.lower()` — which is **wrong**,
  because the string `"inactive"` itself contains `"active"` as its last
  six characters. This meant an *inactive* firewall would have been
  incorrectly reported as `enabled: True`. Caught by manually reasoning
  through the exact-match requirements during the review pass (not by a
  failing test — the original test suite only ever exercised the
  `"active"` case), fixed by extracting a dedicated `_parse_ufw_status`
  function that compares the exact word after the colon, and two new
  tests (`test_parse_ufw_status_recognizes_inactive`,
  `test_collect_detects_ufw_inactive`) were added specifically to guard
  against this regressing silently in the future. Verified for real on
  the Multipass VM, whose `ufw` is genuinely inactive:
  `_parse_ufw_status` now correctly returns `False` for it.
- **Verified genuinely, not just written to spec:** real `ip -o link
  show`, `ip -o addr show`, `ip route show default`, `ss -tulpn` (both
  as root and as an unprivileged user), `ufw status`/`nft list
  ruleset`/`iptables -L -n` (all three, as both root and unprivileged),
  and `journalctl -o json` output were all pulled from the Multipass VM
  *before* writing any parser. The full project was copied to the VM
  twice this sprint (once before the `ufw` fix, once after, to confirm
  the fix held) using the same clean `rsync`-filtered transfer procedure
  established in Phase 3.6/Sprint 1, and the full test suite was run for
  real both times — 193 passed initially, 197 passed after the fix and
  its two new tests. A real, complete, error-free snapshot was captured
  showing 2 real interfaces, a real default route, 7 real listening
  ports (process names correctly absent — unprivileged), no firewall
  tool detected (also correctly unprivileged), and 29 real warning
  journal entries with 0 errors. Saved locally to
  `snapshots/sample_snapshot.json` (gitignored, not committed). The
  temporary copy was removed from the VM after each run.
- Verified both collectors also degrade gracefully on the local macOS
  dev machine (no `ip`, `ss`, or `journalctl` there): `network.py`
  returns empty interfaces/routes/ports with `firewall: {tool: None,
  enabled: None}` and two recorded errors; `logs.py` returns `source:
  "unavailable"` with every count `None` and one recorded error — the
  same shape of graceful degradation every previous collector already
  demonstrates for its own platform-specific gaps.
- Quality review performed on both collectors per this task's explicit
  request, focused specifically on parser readability, large-output
  handling, graceful degradation, and command failures — see
  Consolidated Refactoring Opportunities below. No shared-code
  refactoring was performed, per this task's explicit scope.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count (`grep -c` for `- [x]`/`- [ ]`): 93 complete, 23 remaining, 116
  total (~80%).
- Swept every touched file's headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Consolidated Refactoring Opportunities (recorded only, not acted on)**

Combining this sprint's findings with Collector Sprint 1's, now that
all 9 collectors exist to draw genuine, evidence-based conclusions from:

1. **`_error_entry` is duplicated verbatim across all 9 real
   collectors** — every one of `system.py`, `cpu_memory.py`,
   `processes.py`, `disk.py`, `services.py`, `scheduled_jobs.py`,
   `permissions.py`, `network.py`, and `logs.py` now has the identical
   three-line function. This is the strongest, most complete candidate
   for extraction into a shared `nodeiq.core` helper of anything found
   across either sprint.
2. **`_resolve_owner`/`_resolve_group`** (UID/GID → name, falling back
   to the numeric ID string) remain duplicated between `processes.py`
   and `permissions.py` — unchanged from Sprint 1, no new instances this
   sprint.
3. **The "command failed" error-message construction**
   (`f"{' '.join(command)} failed: {result.error or
   result.stderr.strip()}"`) now additionally appears four times in
   `network.py` (link, addr, route, `ss`) and once in `logs.py`, on top
   of its existing occurrences in `system.py`, `disk.py`, `services.py`,
   and `scheduled_jobs.py` — a strong, now-larger candidate for a shared
   `_command_failure_message(command, result)` helper.
4. **`scheduled_jobs.py`'s two crontab-line parsers** still share about
   10 lines of near-identical structure — unchanged from Sprint 1.
5. **The "two/more independent sources merged, with graduated failure
   handling" structural shape** now appears in `disk.py`, `services.py`,
   and `network.py` (interfaces) — a recurring, consistent pattern
   across three collectors, worth naming/documenting explicitly (e.g. in
   `docs/collector_guidelines.md`) even without extracting shared code,
   since new collectors keep reinventing the same shape correctly by
   imitation rather than by a named, referenceable pattern.
6. **New this sprint:** `network.py`'s `_detect_firewall` uses a
   different command-execution style than every other collector — direct
   sequential `if result.succeeded` checks with early returns, rather
   than the "raise `ValueError`, catch in `collect()`" pattern used
   everywhere else in this codebase. This is a deliberate, justified
   difference (firewall detection never produces an error either way,
   by design), not a bug, but it means the codebase now has two distinct
   "try a command, react to the outcome" styles. Worth a brief note in
   `docs/collector_guidelines.md` distinguishing "this data source can
   fail" (raise/catch) from "this data source is optional/best-effort"
   (direct check, no exception) as two recognized, equally valid shapes.

**Future TODOs**

- **Phase 4 — Report Generation** is next: design a human-readable
  report layout covering all 9 snapshot sections, per `CONTEXT.md`
  Section 8's phase ordering. All the data collection this report will
  summarize now exists.
- A dedicated refactoring sprint should work through this entry's six
  Consolidated Refactoring Opportunities — item 1 (`_error_entry`) and
  item 3 (command-failure messages) are now strong enough, evidence-wise
  (9 and 5 collectors respectively), that ADR-012's "extract from
  evidence" threshold is thoroughly met.
- Still open from prior entries: field-naming/unit divergences across
  `cpu_memory.py`/`processes.py`/`disk.py`/`network.py` vs.
  `docs/snapshot_schema.md`; `docs/process_collector_design.md`'s
  remaining Open Design Questions; per-process CPU utilization and
  `top_by_cpu`; `docs/disk_collector.md`'s deferred `filesystem_type`;
  `docs/logs_collector.md`'s and `docs/scheduled_jobs_collector.md`'s
  deferred timestamp fields; `PROJECT_RULES.md` Section 8 (Logging
  Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs. `TypedDict`
  decision for snapshot section shapes; `CONTEXT.md` Section 6
  clarifying note (optional); Multipass setup docs in `README.md`.

---

## 2026-07-15 — Phase 3.7: Refactoring Sprint

**Task**

With NodeIQ v1's entire data collection layer complete (all 9
collectors, as of Collector Sprint 2), extract only the shared utilities
that duplication across all nine collectors has actually justified —
the three candidates already named across the last two sprints'
"Refactoring Opportunities" write-ups. Explicitly not a feature
phase: no new collectors, no `CollectorContext`/`CollectorResult`/
coordinator/snapshot-schema changes, and external behavior (every
collector's output shape and every real value) must remain identical.

**Files created**

- `src/nodeiq/core/errors.py` — `error_entry(exception, *, message=None)`,
  replacing nine identical (or, for `permissions.py`, near-identical)
  private `_error_entry` functions.
- `src/nodeiq/core/identity.py` — `resolve_username(uid)` and
  `resolve_groupname(gid)`, replacing three near-identical UID/GID
  resolution implementations shared between `processes.py` and
  `permissions.py`.
- `tests/core/test_errors.py` (4 tests), `tests/core/test_identity.py`
  (4 tests) — dedicated unit tests for the two new shared modules,
  replacing the equivalent tests that previously lived inside
  `test_processes.py`/`test_permissions.py`.

**Files modified**

- `src/nodeiq/core/runner.py` — added `command_failure_message(command,
  result)`, replacing eleven identical `f"{' '.join(command)} failed:
  {result.error or result.stderr.strip()}"` constructions across six
  collectors.
- All nine collectors (`system.py`, `cpu_memory.py`, `processes.py`,
  `disk.py`, `services.py`, `scheduled_jobs.py`, `permissions.py`,
  `network.py`, `logs.py`) — replaced their own `_error_entry` with
  `nodeiq.core.errors.error_entry`; the six command-based collectors
  additionally replaced their own failure-message construction with
  `nodeiq.core.runner.command_failure_message`; `processes.py` and
  `permissions.py` additionally replaced their own UID/GID resolution
  with `nodeiq.core.identity.resolve_username`/`resolve_groupname`.
  `permissions.py` no longer imports `pwd`/`grp` directly.
- `tests/collectors/test_processes.py`,
  `tests/collectors/test_permissions.py` — removed the now-redundant
  direct tests of the old private UID/GID resolution functions (moved to
  `test_identity.py`); updated remaining tests to monkeypatch the
  imported `resolve_username`/`resolve_groupname` names instead of the
  removed `_resolve_owner`/`_resolve_group`.
- `tests/core/test_runner.py` — added two tests for
  `command_failure_message`.
- `docs/collector_guidelines.md` — status line updated to reflect all
  nine collectors built; new "Shared Helpers in `nodeiq.core`" section
  documenting all three extractions, what each replaces, and what was
  deliberately *not* extracted (the two crontab-line parsers; the
  "multi-source merge" structural shape); new "Two Command-Execution
  Patterns" section naming the raise/catch vs. best-effort shapes
  observed across the collector set; "Error Handling Expectations" and
  "Helper Function Conventions" updated to point to the shared helpers;
  the old "future `disk` collector" pseudo-code example replaced with
  pointers to the real collectors and their docs; "Quality Check"
  section updated to record this sprint's own three-question review,
  including the one parameter that was cut.
- `CHECKLIST.md` — added a new "Phase 3.7 — Refactoring Sprint" section
  (all 7 tasks checked); Progress Summary updated to 100/123 (~81%).

**Reasoning**

Every extraction was chosen from the "Refactoring Opportunities" lists
already recorded in the two prior sprints' `LOGS.md` entries — nothing
here is a new observation invented mid-sprint, exactly matching this
task's "using evidence collected during previous phases" instruction.
The three candidates were prioritized by how conclusively they'd already
met `DECISIONS.md` ADR-012's "three or more collectors" bar:
`_error_entry` (9 of 9 collectors, the strongest possible evidence),
`command_failure_message` (11 occurrences across 6 collectors), and
UID/GID resolution (technically only 2 collectors, but 3 total
near-identical implementations, since `permissions.py` alone had two).

Two candidates named in prior sprints were deliberately **not**
extracted, and this is recorded explicitly rather than silently ignored
— consistent with this project's established practice of writing down a
tension rather than resolving or dropping it quietly:

- `scheduled_jobs.py`'s two crontab-line parsers (`_parse_system_crontab_line`/
  `_parse_user_crontab_line`) share structure, but unifying them would
  require a branching function distinguishing "has an explicit user
  field" from "doesn't," which is harder to read than two separate,
  obviously-correct functions — this fails "does the abstraction
  simplify the code?" even though the duplication is real.
- The recurring "two-or-more independent sources merged, with graduated
  failure handling" shape (`disk.py`, `services.py`, `network.py`) is a
  structural *pattern*, not literal duplicated code — there's no single
  function two collectors could share, only a design idea. This is
  written down in `docs/collector_guidelines.md`'s new "Two
  Command-Execution Patterns" section instead of forced into premature
  shared code that wouldn't actually reduce anything.

**Important implementation notes**

- **The quality review caught and removed a real instance of
  over-extraction, not just theoretical risk.** `error_entry`'s first
  draft included a `severity: str = "error"` parameter, reasoning that
  `docs/snapshot_schema.md` Section 12 documents `"warning"` as a valid
  value. But grepping every one of the 19 real call sites (before this
  sprint) confirmed **zero** of them ever passed anything but the
  implicit `"error"` — the parameter was speculative, not
  evidence-based, and was removed before committing. This is recorded
  here as a concrete demonstration that the sprint's own three-question
  review (`docs/collector_guidelines.md`'s "Quality Check") was actually
  applied, not just stated.
- **A precise, evidence-first audit preceded any code change:** every
  collector file was read fresh and every `_error_entry` definition, all
  eleven `result.error or result.stderr.strip()` occurrences, and all
  three UID/GID resolution functions were located via `grep` before
  writing a single shared helper — confirming the exact scope of
  duplication rather than assuming it.
- **Verified zero behavior change, not just "tests still pass":** beyond
  the full test suite, a real `run_scan()` was captured before and after
  the refactor (on both macOS and the Multipass VM) and compared field
  by field — identical `collector_count` (9), identical set of
  collectors reporting errors on macOS's graceful-degradation paths,
  and identical real values on the VM (54 running services, disk usage
  at 60.0%, empty `collection_errors`). This is the specific evidence
  behind "external behavior must remain identical," not an assumption.
- Verified genuinely on the Multipass VM, **twice**: an initial pass
  (using the same clean `rsync`-filtered transfer procedure established
  since Phase 3.6) confirmed 202 tests passing before the quality
  review's `severity`-parameter removal (see below); after that removal
  changed the code, the VM was re-verified from scratch rather than
  trusting the earlier, now-stale run — 201 passed, exactly matching the
  201 tests collected locally (191 passed + 10 skipped, the 10 needing a
  real Linux system). A real `run_scan()` was re-captured on this final
  VM pass too, confirming identical values (`collector_count: 9`, empty
  `collection_errors`, 54 running services) to the pre-refactor
  baseline.
- Verified `CHECKLIST.md`'s Progress Summary against a direct checkbox
  count (`grep -c` for `- [x]`/`- [ ]`): 100 complete, 23 remaining, 123
  total (~81%).
- Swept every touched file's headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Before/After Duplication Reduction**

| Pattern | Before | After |
|---|---|---|
| `_error_entry`-shaped dict construction | 9 private definitions (one per collector) | 1 shared function (`nodeiq.core.errors.error_entry`) |
| Command-failure message construction | 11 inline occurrences across 6 collectors | 1 shared function (`nodeiq.core.runner.command_failure_message`) |
| UID/GID → name resolution | 3 near-identical implementations across 2 collectors | 2 shared functions (`nodeiq.core.identity.resolve_username`/`resolve_groupname`) |

**Future TODOs**

- **Phase 4 — Report Generation** is next, per `CONTEXT.md` Section 8's
  phase ordering — unchanged by this sprint, since no new functionality
  was implemented here.
- Still open from prior entries: field-naming/unit divergences across
  `cpu_memory.py`/`processes.py`/`disk.py`/`network.py` vs.
  `docs/snapshot_schema.md`; `docs/process_collector_design.md`'s
  remaining Open Design Questions; per-process CPU utilization and
  `top_by_cpu`; `docs/disk_collector.md`'s deferred `filesystem_type`;
  deferred timestamp fields in `docs/logs_collector.md`/
  `docs/scheduled_jobs_collector.md`; `PROJECT_RULES.md` Section 8
  (Logging Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs.
  `TypedDict` decision for snapshot section shapes; `CONTEXT.md`
  Section 6 clarifying note (optional); Multipass setup docs in
  `README.md`.

---

## 2026-07-15 — Phase 3.8: Snapshot Persistence

**Task**

Give snapshots a life beyond the process that produced them: save
`run_scan()`'s in-memory result to disk, and load it back. Per this
task's explicit scope, no CLI, no report generator, and no coordinator
behavior change — `run_scan()` still returns a plain in-memory dict,
exactly as it has since Phase 3.4; persistence is wired in only through
a documented usage example, never through an import in either direction.

**Files created**

- `src/nodeiq/core/snapshot.py` — `save_snapshot(snapshot) -> Path`
  (creates `snapshots/` if missing, writes indented JSON to a
  timestamped filename, returns the path), `load_snapshot(path) -> dict`
  (reads one snapshot back, raising `SnapshotError` for anything
  broken), and `load_latest_snapshot() -> dict` (finds the newest
  snapshot by filename and loads it). Plus private helpers
  `_generate_filename`/`_filename_timestamp` (pure functions deriving a
  deterministic, microsecond-precision filename from a snapshot's own
  `metadata.scan_timestamp`) and `_validate_snapshot_shape` (a
  deliberately shallow check — JSON object with a `metadata` key —
  distinct from the coordinator's own, fuller
  `_validate_snapshot`).
- `tests/core/test_snapshot.py` — 16 tests: directory creation, valid
  indented JSON, exact round-trip fidelity (both `Path` and string
  inputs), filename derivation from `metadata.scan_timestamp` (plus two
  tests for the missing/malformed fallback), `SnapshotError` for a
  missing file, malformed JSON, a JSON value that isn't an object, and
  JSON missing `metadata`; `load_latest_snapshot` selecting the newest
  of several saved snapshots, handling a missing and an empty
  `snapshots/` directory identically, and ignoring unrelated
  non-snapshot files.
- `docs/snapshot_persistence.md` — why snapshots need to outlive the
  process that produced them, the save → load lifecycle, the naming
  convention (and why it's derived from the snapshot's own timestamp
  rather than wall-clock save time), why persistence and scanning are
  kept as two independent modules with no imports between them, error
  handling, and a Collector Review Checklist adapted for a persistence
  module.

**Files modified**

- `src/nodeiq/core/exceptions.py` — added `SnapshotError(NodeIQError)`,
  alongside the existing `InvalidCommandError`, for the same reason:
  a genuine, unrecoverable problem (here, a broken snapshot file) that
  should fail loudly rather than being silently absorbed the way a
  collector's own anticipated failures are.
- `CHECKLIST.md` — added a new "Phase 3.8 — Snapshot Persistence"
  section (all 9 tasks checked); Progress Summary updated to 109/132
  (~83%).

**Reasoning**

The filename derives from the snapshot's own `metadata.scan_timestamp`
rather than the wall-clock time at the moment `save_snapshot()` happens
to be called — a small but deliberate choice. A snapshot's filename
should answer "when did this scan happen," not "when did someone get
around to saving it," and using the embedded timestamp means the same
snapshot content always produces the same filename regardless of when or
how many times it's written — genuinely deterministic, not just
timestamp-shaped. Microsecond precision (not just seconds) was chosen
specifically because the test suite itself creates several snapshots in
rapid succession — a real, observed need for collision resistance,
not a hypothetical one.

`load_latest_snapshot()` finds the newest snapshot by sorting
**filenames**, not by checking file modification times. Because the
timestamp components are fixed-width and zero-padded, lexicographic
sorting and chronological sorting are the same operation — this avoids
an `os.stat()` call per candidate file, and is more robust than
`mtime`-based comparison, which can be wrong after a backup restore, a
`git checkout`, or copying snapshot files between machines (all of
which change a file's modification time without changing when the scan
inside it actually happened).

`load_snapshot`'s validation is deliberately shallow — confirming the
loaded JSON is an object with a `metadata` key, nothing more. This was
a conscious choice to avoid duplicating (and coupling to)
`nodeiq.core.coordinator._validate_snapshot`'s full section-by-section
check: that function's job is validating a snapshot the coordinator
*just assembled* (so it should have every registered collector's
section); this module's job is only catching "this file clearly isn't a
snapshot at all" for a file that could have come from anywhere — an old
snapshot from before a collector was added, a hand-edited test fixture,
or a genuinely unrelated JSON file. Conflating the two checks would have
made `load_snapshot` needlessly rigid about snapshots from an earlier
NodeIQ version, and would have quietly re-coupled two modules this
phase's whole point was keeping independent.

`SnapshotError` was added to the existing `nodeiq.core.exceptions`
module (not a new exceptions file) since the project already has
exactly one small, shared home for "this is a genuine, must-fail-loudly
problem" exceptions (`InvalidCommandError`), and a second one belonging
to the same category obviously belongs alongside it — no new module was
justified for one class.

**Important implementation notes**

- **Verified genuinely, not just written to spec:** a real `run_scan()`
  result (all 9 collectors) was saved, reloaded, and compared for exact
  equality — first locally on macOS, then for real on the Multipass
  Ubuntu 24.04 VM (`main-cattle`) using the same clean
  `rsync`-filtered transfer procedure established since Phase 3.6. Both
  runs confirmed byte-for-byte round-trip fidelity
  (`loaded == snapshot`) and `load_latest_snapshot()` correctly finding
  the just-saved file. The full test suite passed both locally (207
  passed, 10 skipped — the 16 new snapshot tests included) and on the
  VM (217 passed, all skips lifting on real Linux). The temporary VM
  copy was removed afterward; the demo snapshot file created locally
  during manual verification was written to the scratchpad directory,
  not the project's own `snapshots/`, so nothing needed cleaning up
  there.
- Confirmed `snapshots/*.json` is already gitignored (from Phase 1), so
  any real snapshot files this module creates during manual testing or
  future real use are never accidentally committed.
- Confirmed via `grep` that `nodeiq.core.coordinator` and
  `nodeiq.core.snapshot` do not import each other in either direction —
  the independence this phase's design depends on is structural, not
  just described in prose.
- Swept every touched file's headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Future TODOs**

- **Phase 4 — Report Generation** is next, per `CONTEXT.md` Section 8's
  phase ordering — it will be the first real consumer of
  `load_latest_snapshot()`/`load_snapshot()`.
- Phase 5 (CLI) will be where `run_scan()` and `save_snapshot()` are
  actually wired together in a real command (`nodeiq scan`), per this
  phase's own usage example — not done now, since implementing the CLI
  was explicitly out of this phase's scope.
- Still open from prior entries: field-naming/unit divergences across
  `cpu_memory.py`/`processes.py`/`disk.py`/`network.py` vs.
  `docs/snapshot_schema.md`; `docs/process_collector_design.md`'s
  remaining Open Design Questions; per-process CPU utilization and
  `top_by_cpu`; `docs/disk_collector.md`'s deferred `filesystem_type`;
  deferred timestamp fields in `docs/logs_collector.md`/
  `docs/scheduled_jobs_collector.md`; `PROJECT_RULES.md` Section 8
  (Logging Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs.
  `TypedDict` decision for snapshot section shapes; `CONTEXT.md`
  Section 6 clarifying note (optional); Multipass setup docs in
  `README.md`.

---

## 2026-07-15 — Phase 4.1A: Summary Engine Design

**Task**

Design-only phase, explicitly not implementation: with the data
collection layer complete (9 collectors) and snapshots now persistable
(Phase 3.8), design the layer that will transform a raw snapshot into a
concise, structured Summary for every future downstream consumer — CLI
reports, OpenAI prompts, a future web UI, future exports — without each
one duplicating its own noise-reduction logic. No
`src/nodeiq/summary.py` (or equivalent) was written; no existing code
was touched.

**Files created**

- `docs/summary_engine_design.md` — answers to all seven assigned design
  questions (input shape, output shape, dict vs. dataclass vs.
  TypedDict, section representation, what belongs in a summary vs. what
  stays raw-snapshot-only, and how to support CLI/OpenAI/web UI
  consumers without duplication); an architecture diagram showing where
  the Summary Engine sits between `run_scan()`/snapshot persistence and
  every downstream consumer; a concrete application of the Report
  Philosophy (drawing an explicit, defensible line between deterministic
  templated headlines and forbidden interpretation, and between
  fixed-threshold "concerns" and forbidden diagnosis/recommendations); an
  illustrative Summary object shape grounded in the 9 collectors' real
  current fields; a section lifecycle diagram directly mirroring
  `docs/collector_guidelines.md`'s "Standard Lifecycle"; a module and
  naming proposal (one new `summary.py` module for v1, not a package);
  a trade-offs section; a future-extensibility section; and five
  explicitly recorded open questions.

**Files modified**

- `CHECKLIST.md` — added a new "Phase 4.1A — Summary Engine Design"
  section under Phase 4 (all 5 tasks checked); Progress Summary updated
  to 114/137 (~83%).

**Reasoning**

The central design decision — one summarizer function per snapshot
section, orchestrated by one engine function that never lets a single
section's summarizer crash the whole Summary — is not a new idea being
introduced. It's the collector/coordinator architecture (validated
structurally and through three full implementation sprints across 9
real collectors) applied a second time, one layer higher in the
pipeline. This was treated as the strongest possible design choice
specifically *because* it reuses a proven pattern rather than inventing
an unproven one — the same reasoning this project has applied
consistently since Phase 3.2A's original collector contract design.

A genuinely new observation (not available before all 9 collectors
existed): reviewing their actual current output shows most of the
"reduce noise" work described in this task's Report Philosophy is
*already done* at the collector layer — `processes.py` already returns
only a top-10 list, `logs.py` already caps at 100 entries, `disk.py`
already computes `highest_disk_usage_percent` rather than a full
per-filesystem dump for the caller to reduce. This reframes the Summary
Engine's actual job: less "compress a firehose," more "select, add a
thin deterministic framing layer, and — critically — never silently
drop evidence of a section that failed to collect," directly serving
`CONTEXT.md` Section 4's requirement that missing/failed evidence stay
visible rather than being quietly absorbed.

The most carefully-argued part of this design is the explicit line
between what a deterministic Python layer may and may not say about
data it didn't collect. `docs/collector_guidelines.md` already forbids
collectors from doing "presentation work"; this design had to decide
whether a Summary's "headline" string (e.g. `"3 services failed"`)
crosses that same line. The resolution — mechanical, fixed-template
fact statements are not interpretation; anything stating a cause or
suggesting an action is — is offered as a genuine, reasoned position,
not a hedge, while the adjacent, harder question (whether
fixed-threshold "concern" flagging belongs in this layer at all, versus
being deferred entirely to Phase 6) is recorded as the least-settled
open question in the document rather than resolved by assertion.

**Important implementation notes**

- **Quality review caught and rejected a speculative abstraction before
  it was ever proposed as settled:** a `SummaryContext` object,
  mirroring `CollectorContext`, was considered for symmetry's sake and
  explicitly rejected in the document itself — unlike `CollectorContext`
  (justified by two concrete, current needs per `DECISIONS.md` ADR-014),
  no shared parameter every summarizer function actually needs has been
  identified yet. This is recorded in the design doc's own "Quality
  Review" section (Section 18) as a demonstration that the review was
  actually applied, not just stated, mirroring how Phase 3.7's own
  quality review caught and removed a speculative `severity` parameter
  from `error_entry` before committing.
- This design deliberately does **not** resolve `CHECKLIST.md`'s
  long-open Phase 2 item ("decide on schema representation in code:
  dataclasses vs. TypedDict") — Section 16 of the new doc explicitly
  distinguishes that still-open question (how snapshot *sections*
  should be represented) from this document's narrower, now-answered
  question (how a *derived Summary* should be represented: plain dict).
  Recorded explicitly rather than silently conflating the two or
  silently deciding the older question as an unintended side effect.
- No code was written, per this phase's explicit "do not implement"
  scope — the full test suite was run only to confirm this
  documentation-only phase left the existing 217-test suite (verified
  on the Multipass VM as of Phase 3.8) genuinely untouched.
- Swept the new document's headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Future TODOs**

- **Phase 4.1B (implementation)** should build `src/nodeiq/summary.py`
  from this design: one `_summarize_<section>` function per snapshot
  section, one `_REGISTERED_SUMMARIZERS` list, one public
  `summarize_snapshot()` entry point — mirroring
  `nodeiq.core.coordinator`'s own structure closely enough that its
  existing tests can serve as a template for the new ones.
- Five open questions recorded in `docs/summary_engine_design.md`
  Section 17 need resolving before or during that implementation phase,
  most importantly: whether fixed-threshold "concerns" belong in this
  layer at all, and whether Phase 6's `ask` should consume the Summary
  alone, the raw snapshot alone, or both depending on the question asked.
- Still open from prior entries: field-naming/unit divergences across
  `cpu_memory.py`/`processes.py`/`disk.py`/`network.py` vs.
  `docs/snapshot_schema.md`; `docs/process_collector_design.md`'s
  remaining Open Design Questions; per-process CPU utilization and
  `top_by_cpu`; `docs/disk_collector.md`'s deferred `filesystem_type`;
  deferred timestamp fields in `docs/logs_collector.md`/
  `docs/scheduled_jobs_collector.md`; `PROJECT_RULES.md` Section 8
  (Logging Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs.
  `TypedDict` decision for snapshot section shapes; `CONTEXT.md`
  Section 6 clarifying note (optional); Multipass setup docs in
  `README.md`.

---

## 2026-07-15 — Phase 4.1B: Summary Engine Implementation

**Task**

Implement the Summary Engine exactly as designed in
`docs/summary_engine_design.md`, incorporating two agreed refinements:
rename the design's `facts` field (and split it into two: a concise
`evidence` dict plus a new `highlights` list), and add a deterministic
`status` field (`healthy`/`warning`/`critical`/`unknown`) to every
section, computed only from fixed, named-constant thresholds — never
AI, never an inferred cause, never a recommendation.

**Files created**

- `src/nodeiq/summary.py` — `summarize_snapshot(snapshot) -> dict` (the
  orchestrator) plus one pure `_summarize_<section>` function for each
  of the 9 sections, a `_REGISTERED_SUMMARIZERS` list of `(name,
  function)` pairs mirroring `_REGISTERED_COLLECTORS`, `_unavailable_section`
  (the shared shape for a missing/crashed/failed-to-summarize section),
  and three small presentation-only formatting helpers
  (`_format_uptime`, `_format_bytes`, `_join_names` — the last capping
  any name list at `_MAX_NAMED_ITEMS` with an "and N more" suffix).
  Named threshold constants for every section that has one:
  `_MEMORY_WARNING_PERCENT`/`_MEMORY_CRITICAL_PERCENT`,
  `_SWAP_WARNING_PERCENT`, `_ZOMBIE_WARNING_COUNT`/`_ZOMBIE_CRITICAL_COUNT`,
  `_BLOCKED_WARNING_COUNT`/`_BLOCKED_CRITICAL_COUNT`,
  `_DISK_WARNING_PERCENT`/`_DISK_CRITICAL_PERCENT`,
  `_FAILED_SERVICES_WARNING_COUNT`/`_FAILED_SERVICES_CRITICAL_COUNT`,
  `_LOG_ERROR_WARNING_COUNT`/`_LOG_ERROR_CRITICAL_COUNT`.
- `tests/test_summary.py` — 53 tests: overall Summary structure and
  section-shape conformance; determinism across two calls on the same
  snapshot (excluding the inherently-non-deterministic `generated_at`);
  confirmation that `summarize_snapshot()` never mutates its input; a
  crashed collector's section (`None`) and a section entirely absent
  from an older snapshot both reported as unavailable; missing
  `metadata` handled gracefully; a summarizer that raises isolated from
  the rest (verified both that the other sections still summarize
  correctly and that the exception is recorded in that one section's
  `errors`); every section's specific status logic exercised at, above,
  and below its own thresholds; headline/highlight generation; and the
  three formatting helpers. Plus one genuinely real, unmocked
  integration test calling the actual `run_scan()` — possible without
  any Linux-only skip marker, since `summarize_snapshot()` itself has no
  OS dependency of its own.

**Files modified**

- `CHECKLIST.md` — added a new "Phase 4.1B — Summary Engine
  Implementation" section (all 6 tasks checked); Progress Summary
  updated to 120/143 (~84%).

**Reasoning**

The refinement from the design's single `facts` dict to two separate
fields (`evidence`, a concise dict of the specific numbers a status/
concern was computed from; `highlights`, a list of short, readable
notable-point strings like the top memory consumer or the default
route) turned out to be a genuine improvement, not just a rename: it
cleanly separates "machine-oriented backing data" from "human-oriented
notable points," which is exactly the split a CLI formatter and an
OpenAI prompt builder each want for different reasons (a CLI wants
`highlights` to render directly; a prompt wants `evidence` as
verifiable ground truth) — without either one needing to parse the
other out of one mixed dict.

Every section's `status` is computed from **only** two inputs: a number
already present in the snapshot, and a threshold defined as a named
module-level constant in this file. Nothing about status determination
consults any other section, any historical data, or any inferred
context — satisfying "never use AI, never infer causes, never
recommend" as a structural property of the code, not just a stated
intention. Three sections (`system`, `scheduled_jobs`) were deliberately
left with **no** thresholds at all and an always-`"healthy"`-when-available
status, because their own data genuinely has no health signal to
threshold against — inventing one would have been exactly the kind of
speculative judgment this phase's Report Philosophy forbids.

Two specific status decisions are worth recording as deliberate,
evidence-grounded choices rather than defaults: `services`' status is
`"unknown"` (not `"healthy"`) when `systemd_available` is `False`, and
`logs`' status is `"unknown"` (not `"healthy"`) when `source` is
`"unavailable"` — in both cases, an absent data source is a real gap in
what could be verified, and reporting it as `"healthy"` would silently
misrepresent "we don't know" as "we checked and it's fine," exactly the
conflation `PROJECT_RULES.md` Section 7 and `CONTEXT.md` Section 4 both
warn against. Conversely, `network`'s status deliberately does **not**
treat an undetected firewall as a concern at all (not even `"warning"`)
— per `docs/network_collector.md`, firewall non-detection is the normal,
expected outcome for an unprivileged scan, and flagging it as a concern
would have been a false inference this layer must not make.

**Important implementation notes**

- **Verified genuinely, not just written to spec:** the full project was
  copied to the Multipass Ubuntu 24.04 VM (`main-cattle`) using the same
  clean `rsync`-filtered transfer procedure established since Phase 3.6,
  and the full test suite run for real — 270 passed (260 locally on
  macOS, with 10 tests needing a real Linux system). A genuine
  `run_scan()` result (all 9 collectors succeeding) was summarized for
  real on the VM and inspected directly — every section came back
  `"healthy"` with correctly formatted headlines (e.g. `"Ubuntu 24.04.4
  LTS, kernel 6.8.0-134-generic, up 4h 53m"`, `"Top memory consumer:
  fwupd (41.6 MB)"`), confirming the whole `run_scan() →
  summarize_snapshot()` pipeline works with real data, not just
  hand-built fixtures. The temporary VM copy was removed afterward.
- Test fixtures were hand-built dicts modeled directly on real collector
  output (cross-checked against the real fields present in
  `snapshots/sample_snapshot.json`, a gitignored file from earlier
  verification) rather than reading that file directly — keeping the
  test suite fully self-contained and independent of any non-committed
  file, while still genuinely reflecting real shapes rather than
  invented ones.
- Confirmed via `grep` that neither `nodeiq.core.coordinator` nor
  `nodeiq.core.snapshot` import `nodeiq.summary`, and `nodeiq.summary`
  imports neither of them (only `nodeiq.core.errors`, for the shared
  `error_entry` helper used when a summarizer crashes) — the
  independence the design called for is structural, not just described.
- Swept the touched files' headings (`grep -n '^#'`) to confirm
  sequential, non-duplicated numbering before finishing.

**Refactoring Opportunities (recorded only, not acted on this phase)**

Per this task's explicit "do NOT refactor yet" instruction, every
summarizer's threshold logic was written fully inline, even where a
clear, repeatable pattern emerged across multiple sections:

1. **The "combine two independent checks into one overall status" shape**
   (track `has_critical`/`has_warning`/`evaluated_anything`, then
   `if has_critical: critical elif has_warning: warning elif
   evaluated_anything: healthy else: unknown`) appears identically in
   `_summarize_cpu_memory`, `_summarize_processes`, and
   `_summarize_disk` — three occurrences, meeting even the conservative
   evidentiary bar `DECISIONS.md` ADR-012 already established for
   extracting a shared helper.
2. **The "single value vs. two fixed thresholds → healthy/warning/critical,
   with a similarly-templated concern string" shape** appears, in
   slightly different forms, within each of the six individual checks
   inside those same three summarizers, plus `_summarize_services`
   (`failed_services_count`) and `_summarize_logs` (`error_count`) — eight
   occurrences total of essentially the same "value ≥ critical_threshold
   → ...; elif value ≥ warning_threshold → ...; else healthy" shape. A
   generic `_status_for_value(value, warning_threshold,
   critical_threshold) -> str` (and/or a matching concern-string
   builder) is the strongest candidate for the next sprint.
3. **`_join_names`'s cap-with-"and N more" pattern is already shared**
   (extracted directly in this phase, not left duplicated) — used by
   `_summarize_services` and `_summarize_permissions` — recorded here
   only for completeness, not as an outstanding opportunity.

**Future TODOs**

- A dedicated refactoring sprint (mirroring Phase 3.7's own) should
  evaluate extracting the two duplicated threshold patterns above, once
  a tenth section (or a change to an existing one) provides even
  stronger evidence either way — or sooner, if Phase 4's report
  generator surfaces the same "value vs. threshold" need a third
  context.
- `docs/summary_engine_design.md`'s five open questions remain open;
  none were resolved by this implementation phase, per its own explicit
  scope (implement as designed, don't re-litigate the design).
- Phase 4 continues: a human-readable report layout and generator that
  consumes `summarize_snapshot()`'s output — the first real downstream
  consumer of the Summary Engine.
- Still open from prior entries: field-naming/unit divergences across
  `cpu_memory.py`/`processes.py`/`disk.py`/`network.py` vs.
  `docs/snapshot_schema.md`; `docs/process_collector_design.md`'s
  remaining Open Design Questions; per-process CPU utilization and
  `top_by_cpu`; `docs/disk_collector.md`'s deferred `filesystem_type`;
  deferred timestamp fields in `docs/logs_collector.md`/
  `docs/scheduled_jobs_collector.md`; `PROJECT_RULES.md` Section 8
  (Logging Philosophy) vs. ADR-013 reconciliation; `dataclasses` vs.
  `TypedDict` decision for snapshot section shapes; `CONTEXT.md`
  Section 6 clarifying note (optional); Multipass setup docs in
  `README.md`.

---

## 2026-07-15 — Added Temporary Developer Utility: dev_summary.py

Added `dev_summary.py` at the project root — a small, temporary
developer-only script (not part of the production CLI, no argparse) that
orchestrates the existing pipeline for manual testing during development:
`run_scan()` -> `save_snapshot()` -> `summarize_snapshot()` -> pretty-print
the Summary and the saved snapshot's path. It contains no business logic
of its own; it only calls the three already-existing, already-tested
functions in the order `docs/snapshot_persistence.md` and
`docs/summary_engine_design.md` already describe.

Verified: ran locally on macOS (collectors degrade gracefully with
partial data, as designed, since most rely on Linux-only sources) and
again on the Multipass Ubuntu 24.04 VM (`main-cattle`), where a real
9-collector scan came back fully healthy end to end — a snapshot file
was written under `snapshots/`, and the printed Summary showed all 9
sections `available: true, status: "healthy"` with correct headlines
(e.g. `"Ubuntu 24.04.4 LTS, kernel 6.8.0-134-generic, up 5h 57m"`).
