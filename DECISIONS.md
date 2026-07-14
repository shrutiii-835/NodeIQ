# DECISIONS.md — NodeIQ Architecture Decision Record (ADR)

This file is NodeIQ's Architecture Decision Record. Each entry captures one
decision, the option we chose, why we chose it, what else we considered, the
trade-offs we accepted, and how it will affect future work.

Treat entries as historical once written — if a decision changes later, add
a **new** ADR that supersedes the old one (and note the supersession in
both entries) rather than editing the original away. This keeps the record
of *why we changed our mind* just as visible as the original reasoning.

---

## ADR-001: Target Operating System

**Decision:** What Linux distribution/version does NodeIQ primarily target?

**Chosen Option:** Ubuntu 24.04 LTS

**Reason:**
Ubuntu LTS releases are a common baseline for real production Linux
servers, get 5 years of support, and are extensively documented — which
matters both for development and for the project owner's learning goals.
Targeting one well-known distribution first keeps early phases simple.

**Alternatives Considered:**
- Debian stable
- Rocky Linux / AlmaLinux (RHEL-family)
- Arch Linux

**Trade-offs:**
Some tools NodeIQ inspects are Ubuntu/Debian-specific in practice (e.g.
`ufw` as a firewall front-end, `netplan` for networking). Systems from other
distro families may use different tools for the same job (e.g. `firewalld`
instead of `ufw`). We accept this now and handle it explicitly later rather
than generalizing before we have a single working target.

**Future Impact:**
Phase 7 (Robustness) must explicitly account for systems where Ubuntu's
specific tools aren't present, per CONTEXT.md's safety philosophy (a
collector must never crash just because "its" tool is missing).

---

## ADR-002: Development Environment

**Decision:** Where is NodeIQ developed and manually tested?

**Chosen Option:** A Multipass-managed Ubuntu VM

**Reason:**
Multipass provides a fast, disposable, *real* Ubuntu Linux VM, so NodeIQ's
collectors run against an actual systemd, `/proc`, and network stack —
matching the real target environment — even if the developer's own machine
isn't Linux.

**Alternatives Considered:**
- Docker container
- WSL2
- A bare-metal Linux install
- A cloud VM (e.g. EC2)

**Trade-offs:**
A VM uses more local resources than a container, but containers frequently
lack full systemd/journald support and can behave differently from a real
server for exactly the things NodeIQ inspects (services, cron, logs,
network). A VM is closer to "a real Linux server," which is what NodeIQ is
built for.

**Future Impact:**
All manual testing and demos happen inside this VM. Setup instructions in
`README.md` will eventually include Multipass launch steps (Phase 5+).

---

## ADR-003: Python Version

**Decision:** Which Python version is used for development?

**Chosen Option:** Python 3.12

**Reason:**
3.12 is recent enough to have modern type-hint syntax and performance
improvements, is stable, and is readily available on Ubuntu 24.04 LTS
without needing a separate Python installation method.

**Alternatives Considered:**
- Python 3.10 (the project's previously stated minimum, see `PROJECT_RULES.md`)
- Python 3.13 (very new; higher risk of thin third-party library support)

**Trade-offs:**
This pins the concrete *development* version slightly higher than the
codebase's stated minimum compatibility bar (3.10+, from `PROJECT_RULES.md`
Section 3). That minimum bar is unchanged — this ADR only fixes what we
actually develop and test against day-to-day.

**Future Impact:**
Setup instructions and any future CI configuration target Python 3.12
specifically.

---

## ADR-004: CLI Framework

**Decision:** What library parses NodeIQ's command-line arguments?

**Chosen Option:** `argparse` (Python standard library)

**Reason:**
Standard library, so it adds no dependency. The project is partly a
learning exercise in CLI development — `argparse` requires understanding
how argument parsing, subcommands, and help text actually work, rather than
hiding that behind a higher-level framework.

**Alternatives Considered:**
- `click`
- `typer`

**Trade-offs:**
`argparse` involves more boilerplate and a less polished out-of-the-box
help/UX experience than `click` or `typer`. We accept this in exchange for
zero added dependencies and more transparency into how CLI parsing works.

**Future Impact:**
This resolves the open "CLI framework" question noted in `LOGS.md`'s Phase 1
entry. Phase 5 will use `argparse` subparsers for the `scan`, `report`, and
`ask` commands.

---

## ADR-005: LLM Provider

**Decision:** Which LLM does the `ask` command use to interpret snapshots?

**Chosen Option:** OpenAI API

**Reason:**
Widely documented, has a stable official Python SDK, and is a reasonable
default for Phase 6's evidence-only interpretation layer.

**Alternatives Considered:**
- Anthropic API
- A locally-hosted LLM (e.g. via Ollama)
- Other hosted providers

**Trade-offs:**
Introduces an external network dependency and per-call cost, and ties `ask`
to a single vendor for now. Multi-provider support is already listed as a
"Future Improvement" in `README.md` and `CONTEXT.md`, so this is understood
to be a starting point, not a permanent constraint.

**Future Impact:**
This resolves the open "LLM provider" question noted in `LOGS.md`'s Phase 1
entry. Phase 6 will add the OpenAI Python SDK to `requirements.txt` and
design prompts around evidence-only answering (see CONTEXT.md Section 4,
Safety Philosophy). The API key is managed via `.env` — see ADR-008.

---

## ADR-006: Testing Framework

**Decision:** What test runner/framework does NodeIQ use?

**Chosen Option:** `pytest`

**Reason:**
The de facto standard Python testing framework. Its fixture system and
simpler assertion syntax fit well with mocking subprocess/filesystem calls
in collector tests, as required by `PROJECT_RULES.md`'s Testing Philosophy.

**Alternatives Considered:**
- `unittest` (Python standard library)

**Trade-offs:**
Adds a dependency that the standard library alternative wouldn't, but the
readability and fixture ergonomics are worth it once real collector testing
begins.

**Future Impact:**
`pytest` will be added to `requirements.txt` (or a dev-only requirements
file) when the first tests are written — this may happen as early as Phase
3, rather than waiting for Phase 8, per `PROJECT_RULES.md` Section 11.

---

## ADR-007: Package Management

**Decision:** How are Python dependencies installed and managed?

**Chosen Option:** `venv` + `pip`

**Reason:**
Standard, well-understood, and requires no extra tooling beyond Python
itself — appropriate for a project that explicitly prioritizes learning
fundamentals and minimal dependencies.

**Alternatives Considered:**
- Poetry
- Pipenv
- `uv`

**Trade-offs:**
Less convenient dependency locking and version resolution than Poetry or
`uv`, but avoids introducing another tool's concepts before the basics are
solid.

**Future Impact:**
`requirements.txt` remains the single dependency manifest. Setup
instructions in `README.md` use `python3 -m venv` and
`pip install -r requirements.txt`.

---

## ADR-008: Configuration Management

**Decision:** How does NodeIQ manage secrets and configuration (e.g., the
LLM API key)?

**Chosen Option:** `python-dotenv`, reading a local `.env` file

**Reason:**
A simple, standard way to keep secrets out of source code and out of git,
while keeping the configuration-loading code trivial to read and reason
about.

**Alternatives Considered:**
- Plain OS environment variables set manually by the user
- A config file (`config.yaml` / `config.ini`)
- A dedicated secrets manager

**Trade-offs:**
`.env` files are easy to accidentally commit if `.gitignore` isn't
respected — already mitigated, since `.env` is listed in `.gitignore`. This
is simpler than a full secrets-manager setup, which is appropriate for a
single-server tool, but would not scale to a multi-server or team secrets
model.

**Future Impact:**
Phase 6 (LLM integration) reads the OpenAI API key from `.env` via
`python-dotenv`. `python-dotenv` is added to `requirements.txt` at that
point.

---

## ADR-009: Code Formatting and Linting

**Decision:** What tools enforce code style?

**Chosen Option:** Black (formatter) + Ruff (linter)

**Reason:**
Black removes formatting debates entirely — it's opinionated and
deterministic. Ruff is a fast linter that also catches common bugs and
import-order issues, automatically reinforcing the style and import
conventions already defined in `PROJECT_RULES.md` rather than relying on
manual review alone.

**Alternatives Considered:**
- `flake8` + `isort` + `autopep8`
- `pylint`

**Trade-offs:**
Adds two dev dependencies. Black's formatting choices are not configurable
by design — this is a feature (consistency, no bikeshedding) but means no
per-preference tweaking is possible.

**Future Impact:**
Both are added as dev dependencies once real source code exists (Phase 2
onward). `PROJECT_RULES.md`'s style section (Sections 3 and 6) is enforced
by these tools rather than by manual review alone.

---

## ADR-010: System Support Strategy

**Decision:** How does NodeIQ behave on systems without systemd?

**Chosen Option:** Detect the absence of systemd and degrade gracefully
rather than fail.

**Reason:**
CONTEXT.md's Safety Philosophy and the Phase 7 robustness requirements
already establish that a missing tool must never crash a scan. A missing
systemd (e.g., in some containers or minimal installs) is one concrete case
of that general rule, and deserves explicit handling rather than being left
implicit.

**Alternatives Considered:**
- Require systemd and fail the whole scan if it's absent
- Only officially support systemd-based systems, treat everything else as
  unsupported

**Trade-offs:**
Supporting non-systemd systems means the services collector must include an
explicit "systemd not found" branch, adding some complexity. In exchange,
NodeIQ stays usable across a wider range of environments and avoids a hard
external dependency on one init system.

**Future Impact:**
The services collector (Phase 3) and the Phase 7 robustness pass must
include an explicit "systemd not found" path, recorded via
`collection_errors` rather than raising an exception.

---

## ADR-011: Git Strategy

**Decision:** How and when are commits made, and who makes them?

**Chosen Option:** Frequent commits after every significant, verified,
completed task — performed by Claude as part of finishing that task.

**Reason:**
Frequent, small commits keep history granular and reviewable, and give
every development session (which may be the only continuity between one
sitting and the next) a clear checkpoint that lines up with a `LOGS.md`
entry.

**Alternatives Considered:**
- Large, infrequent commits
- Squash-only history
- Commits performed only manually by the project owner (the project's
  original Phase 1 rule)

**Trade-offs:**
More commits to read through individually, but each one is small, is tied
to a specific completed task, and is easy to understand or revert in
isolation.

**Future Impact:**
This **supersedes** the original Phase 1 git rule ("Claude never runs `git
commit` or `git push`"). From this point forward, per the project owner's
explicit updated instructions, Claude commits after each verified,
significant task, using the commit message conventions already defined in
`PROJECT_RULES.md` Section 13. Claude still never pushes to a remote unless
explicitly asked to.

---

## ADR-012: Parsing Location — Collectors, Not the Command Runner

**Decision:** Where does raw command output get turned into structured
data — inside `nodeiq.core.runner`, or inside each collector?

**Chosen Option:** Every collector parses its own command output, in its
own private `_parse_*` helper functions (see `docs/collector_guidelines.md`).
`nodeiq.core.runner.run_command` only ever returns raw, unparsed text.

**Reason:**
`run_command`'s entire job (see `docs/architecture.md`) is generic: run
any command safely and hand back exactly what happened, with no idea what
the output *means*. Parsing is inherently specific to one command's output
format — parsing `df` looks nothing like parsing `systemctl list-units
--failed`. Putting parsing in the runner would require it to know about
every collector's data shape, which breaks the "the runner has no
knowledge of any specific Linux command" boundary already established when
`nodeiq.core` was built (Phase 3.1).

**Alternatives Considered:**
- A generic parser registry in `nodeiq.core` mapping command names to
  parser functions.
- Shared parsing utilities in a common `core/parsers.py` module, used by
  multiple collectors.

**Trade-offs:**
Keeping parsing entirely inside each collector means some genuinely
generic patterns (e.g., "parse a simple whitespace-aligned text table")
could end up duplicated across a few collectors. This is accepted for now:
plain, obvious, independent code in each collector beats a shared
abstraction built before it's known whether the duplication is even real —
this is exactly the "avoid abstraction for its own sake" principle this
task's own Quality Check asked for. If real, repeated duplication shows up
across three or more collectors during Phase 3.2B, a small shared helper
can be extracted *then*, from evidence, rather than designed speculatively
now.

**Future Impact:**
Every Phase 3.2B collector will contain its own `_parse_*` helpers (see
`docs/collector_guidelines.md`). `nodeiq.core.runner` will never gain
command-specific logic — if a future change requires that, it's a sign the
architecture needs revisiting, not a small tweak.

---

## ADR-013: No Application Logging in v1 — Errors Live in `collection_errors`

**Decision:** Does NodeIQ configure and use Python's `logging` module
during v1 development?

**Chosen Option:** No. NodeIQ does not implement application logging in
v1. Every operational fact about what a collector couldn't determine is
captured as structured data in the snapshot's `collection_errors` section
instead (see `docs/snapshot_schema.md` Section 12), returned directly from
each collector's `collect()` call (see `docs/collector_guidelines.md`).

**Reason:**
`PROJECT_RULES.md` Section 8 (Logging Philosophy) already anticipated a
future logging setup, but actually building one (handlers, formatters, log
levels, log file rotation and location) is complexity NodeIQ's v1 doesn't
need: every failure a collector can have is already required to be visible
in the one artifact that actually matters — the snapshot itself. A
developer debugging a broken collector can read `collection_errors` in the
resulting snapshot (or a failing test) rather than needing to also
configure and tail a separate log stream. This mirrors this task's own
instruction to avoid frameworks and abstractions not yet justified by a
real need.

**Alternatives Considered:**
- Implement full `logging` module configuration now, per the existing plan
  in `PROJECT_RULES.md` Section 8.
- Use bare `print()` statements for ad hoc debugging during development.

**Trade-offs:**
Without logging, there's no record of *successful* collector runs, no
timing/diagnostic detail beyond what `collection_errors` and `metadata`
already capture, and no adjustable verbosity (DEBUG vs. WARNING) during
development. This is accepted because v1's actual need — "know what failed
and why" — is already served by the snapshot itself; a parallel logging
system would be additional machinery with no immediate user of its output.

**Future Impact:**
`PROJECT_RULES.md` Section 8 describes NodeIQ's eventual logging plan, not
its current (v1) state — that section predates this decision and is not
being edited as part of this ADR, since reconciling it is out of this
task's declared scope (see `LOGS.md` for this task's file list). This
tension is flagged here explicitly, and a follow-up task should either
update Section 8 to describe v1's actual (no-logging) behavior or
implement logging properly, rather than leaving the two documents
silently disagreeing. If real operational logging is ever added (e.g. for
diagnosing NodeIQ itself in Phase 7 or later), that would be a new ADR
superseding this one, not a silent reversal.

---

## ADR-014: Structured `CollectorResult`/`CollectorContext` Instead of a Tuple

**Decision:** How does a collector receive shared scan information, and
how does it return its outcome to the coordinator — plain tuples and
positional arguments, or named, structured types?

**Chosen Option:** Two small `@dataclass(frozen=True)` types in
`nodeiq.core.collector`:

- `CollectorContext` — passed *into* every `collect()` call, carrying
  `scan_start_time` and `default_timeout`.
- `CollectorResult` — returned *from* every `collect()` call, carrying
  `collector_name`, `data`, `errors`, `duration_ms`, and a computed
  `success` property.

This replaces the Phase 3.2A contract, `collect() -> tuple[dict,
list[dict]]`, with `collect(context: CollectorContext) -> CollectorResult`.

**Reason:**

*Why a structured result instead of a tuple:* a tuple's positions carry no
names — `(data, errors)` only means "data first, errors second" by
convention, and nothing about the type itself documents that at a call
site, or prevents the two positions from silently being written in the
wrong order somewhere. As the result grows to include more than the
original two pieces of information (`duration_ms` and `collector_name`
are new in this ADR), a tuple would either have to grow more positions
(worse) or those extra facts would need to live somewhere else entirely,
disconnected from the data/errors they describe. A dataclass gives every
piece of information a name, readable at the point of use
(`result.duration_ms`), without needing to remember a position-based
convention — the same reasoning that already justified `CommandResult`
(`nodeiq.core.result`) over a raw tuple of `(returncode, stdout, stderr)`
back in Phase 3.1.

*Why `CollectorContext` exists even though only two fields are used so
far:* every collector already independently needs *some* timeout value to
pass to `run_command`, and right now every collector would otherwise
hardcode its own default (or import a shared constant with no way to
override it per-scan). `CollectorContext` gives the coordinator one place
to hand every collector the same timeout default, changeable for an
entire scan by constructing a different context — for example, a future
"quick scan" mode with shorter timeouts, without touching any collector's
code. `scan_start_time` similarly gives every collector one agreed-upon
"now" for the scan, rather than each independently calling
`datetime.now()` and getting slightly different values. Both fields solve
a real, current problem; neither is speculative.

**Alternatives Considered:**
- Keep the `(data, errors)` tuple from ADR/Phase 3.2A, and have the
  coordinator separately track `collector_name` and `duration_ms` outside
  of what `collect()` itself returns (by timing the call externally and
  looking up the name from whichever module was being called).
- A single dict with reserved keys (e.g. `{"data": ..., "errors": ...,
  "duration_ms": ...}`) instead of a dataclass.
- Global/module-level configuration for defaults like `default_timeout`,
  instead of an explicit context object passed as an argument.

**Trade-offs:**
This is more code than a bare tuple — two dataclass definitions instead of
zero — and every collector must now measure and report its own
`duration_ms` and hardcode its own `collector_name` string, rather than
the coordinator inferring these facts externally. This is accepted because
the amount of *actual* new complexity is small (the same shape of
dataclass as the `CommandResult` already in the codebase, plus a few lines
of self-timing per collector, mirroring how `run_command` already times
itself) and the payoff (self-documenting fields, one shared context object)
outweighs it. A dict with reserved keys was rejected because it has all of
a dataclass's indirection with none of its type-checking or IDE-completion
benefit. Global configuration for `default_timeout` was rejected because it
would be implicit, hidden shared state (which `PROJECT_RULES.md` Section 3
already prohibits: "No global mutable state. Pass data explicitly between
functions.") — an explicit `CollectorContext` argument keeps the dependency
visible in every `collect()` signature.

**Future Impact:**
Every Phase 3.2B collector implements `collect(context: CollectorContext)
-> CollectorResult`, per the revised `docs/collector_guidelines.md`. The
future scan coordinator (`nodeiq.core.coordinator`) will construct exactly
one `CollectorContext` per scan and pass it to every collector, then
collect each returned `CollectorResult` to assemble the snapshot and
`collection_errors`. Adding a new field to either dataclass later (with a
default value, so existing collectors are unaffected) remains trivial —
this is not expected to need another ADR unless a field is ever removed or
renamed, which would be a breaking change per the same convention already
established for the snapshot schema's `metadata.schema_version`
(`docs/snapshot_schema.md`).
