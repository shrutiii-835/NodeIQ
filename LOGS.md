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
