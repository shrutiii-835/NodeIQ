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
