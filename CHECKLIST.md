# CHECKLIST.md — NodeIQ Progress Tracker

This is the permanent, living progress tracker for NodeIQ, organized by the
implementation phases defined in [CONTEXT.md](CONTEXT.md) Section 8. Update
this file whenever a task is completed — check off the task and, if needed,
add newly-discovered sub-tasks. Do not remove future/unchecked tasks; they
stay listed (unchecked) until their phase is actually worked on.

---

## Progress Summary

- **Current Phase:** Phase 6D — AI Integration (complete — Phase 6, LLM Integration, is now fully complete)
- **Next Phase:** Phase 7 — Robustness, or a refactoring sprint for Phase 4.1B's recorded opportunities
- **Overall Progress:** 167 / 179 tasks complete (~93%)
- **Completed Tasks:** 167 (all of Phase 1, 13 of 14 in Phase 2, all of Phase 3.1, all of Phase 3.2A, all of Phase 3.2B, all 9 of 9 in Phase 3.2C, all of Phase 3.4, all of Phase 3.5A, all of Phase 3.5B, all of Phase 3.6, all of Collector Sprint 1, all of Collector Sprint 2, all of Phase 3.7, all of Phase 3.8, all of Phase 4.1A, all of Phase 4.1B, all of Phase 4.2, all of Phase 5A, all of Phase 5B, all of Phase 6A, all of Phase 6B, all of Phase 6C, all of Phase 6D)
- **Remaining Tasks:** 12 (1 in Phase 2, all of Phases 7–8)

> This summary must be updated by hand whenever tasks below are checked or
> added, so it always matches the checkboxes further down this file.

---

## Phase 1 — Project Architecture

- [x] Define project folder structure (`docs/`, `snapshots/`, `src/nodeiq/`, `tests/`)
- [x] Write `README.md`
- [x] Write `CONTEXT.md`
- [x] Write `PROJECT_RULES.md`
- [x] Write `LOGS.md`
- [x] Create `requirements.txt` and `.gitignore`
- [x] Write `CHECKLIST.md` (this file)
- [x] Write `DECISIONS.md` (Architecture Decision Record)
- [x] Write `ROADMAP.md`
- [x] Write `LEARNING_NOTES.md`
- [x] Initialize git repository and make the first commit

## Phase 2 — Data Model

- [x] Define the top-level snapshot envelope schema (`timestamp`, `hostname`, `collection_errors`, etc.)
- [x] Define `metadata` section schema
- [x] Define `system` section schema
- [x] Define `cpu_memory` section schema
- [x] Define `processes` section schema
- [x] Define `disk` section schema (includes inode usage — see `docs/snapshot_schema.md` Section 14)
- [x] Define `services` section schema
- [x] Define `logs` section schema
- [x] Define `network` section schema
- [x] Define `scheduled_jobs` section schema
- [x] Define `permissions` section schema (scope intentionally conservative — flagged as an open question)
- [x] Define `collection_errors` section schema
- [x] Document all section schemas under `docs/` (`docs/snapshot_schema.md`, `docs/data_model_design.md`)
- [ ] Decide on schema representation in code (dataclasses vs. TypedDict)

## Phase 3 — Collectors

### Phase 3.1 — Core Execution Infrastructure

- [x] Create `src/nodeiq/core/` and `src/nodeiq/collectors/` package structure
- [x] Implement `CommandResult` (`core/result.py`)
- [x] Implement project-specific exceptions (`core/exceptions.py`)
- [x] Implement the command runner (`core/runner.py`) — timeout, stdout/stderr/returncode capture, duration measurement, never raises for a system-level failure
- [x] Add a documented scan coordinator placeholder (`core/coordinator.py`) — no scanning logic yet
- [x] Introduce `pytest`; write focused runner tests (success, non-zero exit, timeout)
- [x] Document the execution architecture (`docs/architecture.md`)

### Phase 3.2A — Collector Design Pattern

- [x] Document collector purpose, responsibilities, and non-responsibilities (`docs/collector_guidelines.md`)
- [x] Document the standard lifecycle: `collect()` → `run_command()` → parse → validate → return
- [x] Document separation of command execution and parsing
- [x] Document error handling expectations (the `(data, errors)` contract)
- [x] Document JSON output expectations
- [x] Document helper function conventions (`_parse_*`, `_validate_*`)
- [x] Document testing expectations for collectors
- [x] Review core infrastructure against the design; reconcile `collect()` return-type documentation (`PROJECT_RULES.md` Section 9, `core/coordinator.py`, `docs/architecture.md`)
- [x] Add ADR-012 (parsing location) and ADR-013 (no v1 application logging) to `DECISIONS.md`

### Phase 3.2B — Collector Infrastructure Refinement

- [x] Create `src/nodeiq/core/collector.py` with `CollectorContext` and `CollectorResult` dataclasses
- [x] Replace the `collect() -> tuple[dict, list[dict]]` contract with `collect(context) -> CollectorResult` in `docs/collector_guidelines.md`
- [x] Update `docs/architecture.md` diagram and layer explanations for the refined contract
- [x] Add ADR-014 (structured `CollectorResult` vs. tuple; why `CollectorContext` exists before many options need it)
- [x] Update `core/coordinator.py` docstring and `PROJECT_RULES.md` Section 9 (documentation only, no logic changed)
- [x] Add focused unit tests for `CollectorContext`/`CollectorResult`

### Phase 3.2C — Collectors (Implementation, complete — all 9 collectors built)

- [x] System metadata collector (`system`: hostname, operating_system, kernel_version, architecture, uptime_seconds — `os_name`/`os_version` split and `boot_time` deferred, see `docs/system_collector.md`)
- [x] CPU + memory collector (`cpu_memory`: memory/swap usage from `/proc/meminfo`, load averages from `/proc/loadavg` — CPU utilization percentages deferred; module renamed from `resource.py` to `cpu_memory.py` in Phase 3.4 to match `docs/snapshot_schema.md` Section 4; field-shape divergence — flat byte fields vs. nested kB, no `core_count` — still not reconciled, see `docs/cpu_memory_collector.md`)
- [x] Processes collector (`processes`: process_count, zombie_count, blocked_process_count (state `D`), top_by_memory — reads only `/proc/<pid>/status`, `cmdline`, `comm`, no `ps`; `stat` deferred; disappearing processes skipped gracefully; see `docs/process_collector.md`)
- [x] Disk + inodes collector (`disk`: total_bytes/used_bytes/available_bytes/usage_percent plus inode_total/inode_used/inode_available/inode_usage_percent per filesystem, merged from `df -P -B1` and `df -P -i`; highest_disk_usage_percent/highest_inode_usage_percent computed; field-shape divergence from `docs/snapshot_schema.md` Section 6 not reconciled, see `docs/disk_collector.md`)
- [x] Services collector (`services`: running/failed/enabled counts, failed_services, restarting_services, `systemd_available` graceful degradation — from `systemctl list-units`/`list-unit-files`; see `docs/services_collector.md`)
- [x] Logs collector (`logs`: `journalctl -o json` for the last 100 warning-or-worse entries, `warning_count`/`error_count`, `truncated` flag, graceful degradation when the journal is unavailable; see `docs/logs_collector.md`)
- [x] Network collector (`network`: interfaces (state/IPv4/IPv6) merged from `ip -o link`/`ip -o addr`, default route from `ip route`, listening ports from `ss -tulpn`, best-effort firewall detection (`ufw`/`nft`/`iptables`); see `docs/network_collector.md`)
- [x] Scheduled jobs collector (`scheduled_jobs`: cron_jobs (system + user-accessible) + systemd_timers, from `/etc/crontab`/`/etc/cron.d/*`/`/var/spool/cron/crontabs/*` + `systemctl list-timers`; timer next_run/last_run deferred; see `docs/scheduled_jobs_collector.md`)
- [x] Permissions collector (`permissions`: checked_paths for `/etc/passwd`, `/etc/shadow`, `/etc/ssh`, `/var/log` — exists/owner/group/mode/world_writable, no subprocess; conservative v1 scope, not a security audit; see `docs/permissions_collector.md`)

### Phase 3.4 — Coordinator MVP

- [x] Rename `resource.py` to `cpu_memory.py` (module, tests, docs, and all references)
- [x] Implement `run_scan()`: build one `CollectorContext`, run registered collectors, aggregate errors, assemble an in-memory snapshot (no disk writes yet)
- [x] Register collectors in a simple list (`_REGISTERED_COLLECTORS`) — no plugin system
- [x] Populate `metadata` (`scan_timestamp`, `scan_duration_ms`, `collector_count`, `nodeiq_version`, `hostname`)
- [x] Add lightweight snapshot validation (`_validate_snapshot`) — no external validation library
- [x] Coordinator unit tests (fake collectors) and an end-to-end integration test verified on the Multipass VM
- [x] Document the coordinator (`docs/coordinator.md`)

### Phase 3.5A — Process Collector Design (design only, no code)

- [x] Document how Linux represents processes, `/proc/<pid>` structure, which files NodeIQ should/shouldn't use, and `/proc` vs. `ps` trade-offs (`docs/process_collector_design.md`)
- [x] Propose the v1 process schema (`pid`, `process_name`, `command`, `state`, `memory_rss_bytes`, `owner`, `start_time`, `threads`) with Source/Why/Required-or-optional for each field
- [x] Recommend a process summarization strategy (`process_count`, `top_by_memory`, zombie/`D`-state counts; not sending every process to the LLM)
- [x] Research and document Linux process states (`R`, `S`, `D`, `T`, `Z`) and their operational significance
- [x] Review `docs/snapshot_schema.md` Section 5's existing `processes` schema against this design and record recommended improvements (not implemented)

### Phase 3.5B — Process Collector Implementation

- [x] Implement `collectors/processes.py`: discover PIDs via `/proc`, read only `status`/`cmdline`/`comm` (no `ps`, `stat` deferred), produce `process_count`, `zombie_count`, `blocked_process_count`, and `top_by_memory` (top 10)
- [x] Resolve `owner` from UID via `pwd.getpwuid`, falling back to the numeric UID string on lookup failure
- [x] Skip processes that disappear mid-scan gracefully — no collector-wide error
- [x] Register `processes` with the coordinator (`_REGISTERED_COLLECTORS`, `_REQUIRED_SECTIONS`)
- [x] Unit tests (mocked `/proc`) and an integration test verified on the Multipass VM (full 88-test suite passing)
- [x] Document the collector (`docs/process_collector.md`)

### Phase 3.6 — Disk + Inodes Collector

- [x] Implement `collectors/disk.py`: run `df -P -B1` and `df -P -i`, parse each independently, merge by mount point into one per-filesystem entry
- [x] Compute scan-wide `highest_disk_usage_percent` and `highest_inode_usage_percent`
- [x] Handle `-` values (filesystems with no inode concept, e.g. `efivarfs`) gracefully as `None`
- [x] If one `df` command fails, return whatever the other still produced, plus a structured error — never lose already-gathered data
- [x] Register `disk` with the coordinator (`_REGISTERED_COLLECTORS`, `_REQUIRED_SECTIONS`)
- [x] Unit tests (parsing, merge logic, `collect()`) and an integration test verified on the Multipass VM (full 111-test suite passing)
- [x] Document the collector (`docs/disk_collector.md`)

### Collector Sprint 1 — Services, Scheduled Jobs, Permissions

- [x] Implement `collectors/services.py`: `systemctl list-units` + `list-unit-files`, `systemd_available` graceful degradation (DECISIONS.md ADR-010)
- [x] Implement `collectors/scheduled_jobs.py`: system + user-accessible cron jobs, systemd timers (next_run/last_run intentionally deferred — fragile date parsing)
- [x] Implement `collectors/permissions.py`: conservative fixed path list, three-state exists/owner/group/mode/world_writable, no subprocess
- [x] Register all three with the coordinator (`_REGISTERED_COLLECTORS`, `_REQUIRED_SECTIONS`)
- [x] Unit tests and integration tests for all three collectors, verified on the Multipass VM (full 151-test suite passing)
- [x] Document all three collectors (`docs/services_collector.md`, `docs/scheduled_jobs_collector.md`, `docs/permissions_collector.md`)
- [x] Quality review of all three collectors; duplication recorded as Refactoring Opportunities only, not refactored (per this sprint's explicit scope)

### Collector Sprint 2 — Network, Logs (completes the NodeIQ v1 collector set)

- [x] Implement `collectors/network.py`: interfaces (`ip -o link` + `ip -o addr` merged), default route (`ip route show default`), listening ports (`ss -tulpn`), best-effort firewall detection
- [x] Implement `collectors/logs.py`: `journalctl -p warning -n 100 -o json`, `warning_count`/`error_count`, `truncated` flag, graceful degradation
- [x] Register both with the coordinator (`_REGISTERED_COLLECTORS`, `_REQUIRED_SECTIONS`) — all 9 collectors now registered
- [x] Unit tests and integration tests for both collectors, verified on the Multipass VM (full 193-test suite passing)
- [x] Document both collectors (`docs/network_collector.md`, `docs/logs_collector.md`)
- [x] Quality review of both collectors; consolidated Refactoring Opportunities recorded (with Collector Sprint 1's), not refactored (per this sprint's explicit scope)

### Phase 3.7 — Refactoring Sprint

- [x] Extract shared `error_entry` helper (`nodeiq/core/errors.py`) from 9 identical per-collector `_error_entry` definitions
- [x] Extract shared `command_failure_message` helper (`nodeiq/core/runner.py`) from 11 identical call sites across 6 collectors
- [x] Extract shared `resolve_username`/`resolve_groupname` helpers (`nodeiq/core/identity.py`) from 3 near-identical UID/GID resolution implementations across 2 collectors
- [x] Update all 9 collectors to use the shared helpers; remove every local copy
- [x] Quality review each extraction against "simplifies code / real duplication / worth it with two collectors" — removed a speculative `severity` parameter from `error_entry` that no caller actually used
- [x] Verify zero behavior change: full test suite passes locally and on the Multipass VM; a real snapshot's shape and values are unchanged
- [x] Document the shared helpers and two observed command-execution patterns (`docs/collector_guidelines.md`)

### Phase 3.8 — Snapshot Persistence

- [x] Implement `core/snapshot.py`: `save_snapshot()`, `load_snapshot(path)`, `load_latest_snapshot()`
- [x] `save_snapshot()` creates `snapshots/` if missing, writes indented JSON, returns the saved path
- [x] Deterministic, timestamped filenames derived from `metadata.scan_timestamp` (microsecond precision; falls back to current time if missing/malformed)
- [x] `load_snapshot()` validates basic shape (JSON object with `metadata`) and raises `SnapshotError` (new, in `core/exceptions.py`) for any broken file
- [x] `load_latest_snapshot()` selects the newest snapshot by filename (sorts chronologically by construction), no `stat()` needed
- [x] Add `SnapshotError` to `core/exceptions.py`
- [x] Coordinator unchanged — persistence wired in only via a documented usage example, never imported by `core/coordinator.py`
- [x] Unit tests (full save/load/load_latest coverage, missing directory, malformed JSON) and a real save/load round trip verified with an actual `run_scan()` result, locally and on the Multipass VM
- [x] Document snapshot persistence (`docs/snapshot_persistence.md`)

## Phase 4 — Report Generation

### Phase 4.1A — Summary Engine Design (design only, no code)

- [x] Document architecture: where the Summary Engine fits between raw snapshots and every downstream consumer (`docs/summary_engine_design.md`)
- [x] Answer all 7 design questions (input, output shape, dict/dataclass/TypedDict, section representation, what belongs in summaries, what stays raw-only, supporting CLI/OpenAI/web UI without duplication)
- [x] Apply the Report Philosophy concretely: draw the line between deterministic templated headlines and interpretation; between fixed-threshold concerns and diagnosis/recommendations
- [x] Propose an illustrative Summary object shape, a section lifecycle mirroring the collector lifecycle, and a module/naming proposal (single `summary.py` for v1, package split deferred)
- [x] Quality review: reject a speculative `SummaryContext` object; record five genuine open questions rather than guessing

### Phase 4.1B — Summary Engine Implementation

- [x] Implement `summary.py`: `summarize_snapshot()` plus one pure `_summarize_<section>` per section, orchestrated via a plain `_REGISTERED_SUMMARIZERS` list mirroring `_REGISTERED_COLLECTORS`
- [x] Rename the design's `facts` field to `evidence` (kept concise, never the full raw section) and add `highlights` as its own list field
- [x] Add a deterministic `status` field (`healthy`/`warning`/`critical`/`unknown`) to every section, computed only from fixed, named-constant thresholds — no AI, no inferred causes, no recommendations
- [x] Orchestrator isolates summarizer failures (mirrors `run_scan()`'s own crash-safety net) and never lets a missing/crashed section stop the rest
- [x] Comprehensive unit tests (53) covering determinism, non-mutation of input, missing/crashed sections, summarizer-failure isolation, status logic per section, headline generation, and full structure conformance; a real, unmocked `run_scan()` integration test (portable — no Linux skip needed, since summarization itself has no OS dependency)
- [x] Quality review: identified (not yet extracted) duplicated threshold-combination and value-vs-threshold logic across summarizers — recorded as Refactoring Opportunities for the next sprint

### Phase 4.2 — Report Formatter

- [x] Implement `report.py`: `format_report(summary) -> str`, presentation-only, no summarization, no data collection
- [x] Cover every Summary section in the report output (status, headline, highlights; concerns only when present)
- [x] Missing/unavailable sections render cleanly (no crash, no raw JSON)
- [x] Update `dev_summary.py`: `run_scan()` → `save_snapshot()` → `summarize_snapshot()` → `format_report()` → `print(report)`
- [x] Unit tests (28) covering every-section formatting, missing sections, empty highlights/concerns, determinism, non-mutation, no raw JSON leaked
- [x] Document the formatter (`docs/report_formatter.md`) — separation of Summary vs. Formatter, formatting philosophy, module/naming
- [x] Quality review: single shared `_format_section` helper, no per-section formatting functions, no speculative abstractions added

- [x] Design a `nodeiq report` CLI command that wires this formatter to a loaded snapshot (Phase 5) — see Phase 5A below

## Phase 5 — CLI

### Phase 5A — CLI Design (design only, no code)

- [x] Document `scan`/`report`/`ask` syntax, arguments, flags, exit codes, expected behavior, and interaction with snapshots/Summary Engine/OpenAI (`docs/cli_design.md`)
- [x] Design `report --section NAME` as CLI-layer dict filtering (no new parameters in `nodeiq.summary`/`nodeiq.report`)
- [x] Design `ask --fresh` as CLI-layer composition of `scan`'s own sequence with `ask`'s normal load-and-interpret flow (no new live-system access inside `ask` itself)
- [x] Define error handling and a proposed exit-code scheme for snapshot-not-found, malformed snapshot, OpenAI unavailable, scan failure, and invalid arguments
- [x] Document the complete user flow (`scan` → `report` → `report --section` → `ask` → `ask --fresh`)
- [x] Quality review: reject a speculative `CliContext` object; record six genuine open questions (exit codes, `report --fresh` symmetry, `scan --quiet`, `ask --fresh` output shape, the Phase 6 LLM function signature, console-script entry point) rather than guessing

### Phase 5B — CLI Implementation

- [x] Wire up `argparse` with subcommands (`src/nodeiq/cli/main.py`; `python -m nodeiq` via `src/nodeiq/__main__.py`; console-script `nodeiq` via `pyproject.toml`)
- [x] Implement `nodeiq scan`: `run_scan()` -> `save_snapshot()` -> print collectors-executed + snapshot location
- [x] Implement `nodeiq report` (default, `--fresh`, `--snapshot PATH`, `--section NAME`, resolving Phase 5A Open Question 2 in favor of symmetry)
- [x] Implement `nodeiq ask` as a placeholder reporting that AI integration arrives in Phase 6 (real implementation deferred)
- [x] Unit tests (32) covering argument parsing, `main()` dispatch, `scan`, `report` (default/fresh/snapshot/section, missing/malformed snapshot, invalid section), the `ask` placeholder, and both pure helpers (`_scan_confirmation`, `_select_section`)
- [x] Quality review: no duplicated CLI logic (`_scan_confirmation`/`_select_section` each written once, shared where needed); argument validation delegated to `argparse` wherever possible (mutually-exclusive `--snapshot`/`--fresh`); CLI computes no status/formatting of its own


## Phase 6 — LLM Integration

### Phase 6A — Prompt Builder & Guardrail Design (design only, no code)

- [x] Document Prompt Builder responsibilities, module proposal (`src/nodeiq/llm/prompt.py`), and its independence from the CLI/OpenAI client/collectors/coordinator (`docs/prompt_builder_design.md`)
- [x] Design the prompt flow, the `Prompt` shape, system/user prompt content, evidence formatting, output ordering (system → evidence → question), and a prompt-versioning strategy
- [x] Design guardrails for hallucination prevention, missing/conflicting evidence, unknown answers, recommendations, cause vs. observation, historical vs. current state, confidence wording, evidence boundaries, and unsupported questions
- [x] Discuss (without implementing) question-category evidence needs (information/explanation/analysis/comparison/troubleshooting/security) and Summary-vs-Snapshot token trade-offs
- [x] Quality review: checked for hidden coupling, unnecessary complexity, token waste, maintainability, hallucination risk, and future migration problems; record eight genuine open questions rather than guessing

### Phase 6B — Prompt Builder Implementation

- [x] Implement `src/nodeiq/llm/prompt.py`: `build_prompt(question, evidence, evidence_kind="summary") -> dict`, a pure function returning a plain `{system, user, prompt_version}` dict
- [x] Implement every guardrail designed in Phase 6A as real system-prompt text (evidence boundary, allowed/forbidden conclusions, when to refuse, uncertainty-phrasing registers, conflicting evidence, historical-vs-current framing, unsupported questions)
- [x] Construct the user prompt as evidence (JSON, order-preserving, with a freshness marker) then the verbatim question, per the Phase 6A ordering
- [x] Reject any `evidence_kind` other than `"summary"` explicitly, rather than silently treating an unimplemented kind as a Summary
- [x] Unit tests (35) covering normal/empty questions, empty evidence, unsupported `evidence_kind`, determinism, prompt versioning, evidence/question preservation, guardrail presence, non-mutation, and Unicode/multiline handling
- [x] Quality review: confirmed zero coupling to the OpenAI SDK or `nodeiq.cli` (only `import json`), no duplicated prompt text, no hidden mutation

### Phase 6C — OpenAI Client

- [x] Add OpenAI SDK (`openai`) and `python-dotenv` dependencies to `requirements.txt`
- [x] Implement `src/nodeiq/llm/client.py`: `ask_openai(prompt, *, temperature=0.0) -> str`, consuming exactly the Prompt Builder's `{system, user, prompt_version}` shape, never rebuilding or modifying it
- [x] `OPENAI_API_KEY` read only in `client.py` (via `os.environ`, with `.env` support through `python-dotenv`); `.env.example` added with placeholder-only content; missing key raises a project-specific `LLMConfigurationError` with a clear message
- [x] Implement `src/nodeiq/llm/exceptions.py`: `LLMError` and 7 subclasses translating every SDK failure category (config, auth, timeout, connection, rate limit, server error, malformed/empty response) — no raw SDK exception ever escapes `ask_openai`
- [x] Implement timeout, a fixed-attempt retry with backoff for transient failures only (timeout/connection/rate-limit/server error — not auth failures or malformed responses), a configurable `temperature` with a deterministic (`0.0`) default, and response validation/extraction
- [x] Choose and document one default model (`gpt-4o-mini`) as a module-level constant — no runtime model selection
- [x] Unit tests (31) covering success, missing/invalid key, auth failure (and its non-retry), timeout/rate-limit/server-error retry exhaustion, successful recovery after a transient failure, malformed/empty responses, deterministic defaults, prompt verbatim pass-through, and API-key-never-leaked checks across every exception path
- [x] Security review: confirmed `OPENAI_API_KEY` is read only in `client.py`, never logged/printed/serialized, `.env` is gitignored, `.env.example` contains only a placeholder, no real secret exists anywhere in the repository
- [x] Quality review: no hidden coupling, no duplicated prompt logic, no OpenAI imports outside `nodeiq.llm`, no unnecessary complexity

### Phase 6D — AI Integration

- [x] Implement `src/nodeiq/llm/ask.py`: `answer_question(question, snapshot_path=None) -> str`, the one backend orchestration function composing snapshot loading, `summarize_snapshot()`, `build_prompt()`, and `ask_openai()`
- [x] Wire `nodeiq ask` to `answer_question()`, replacing the Phase 6A/6B/6C placeholder — `--snapshot PATH` supported, question now a required positional argument
- [x] CLI-level error handling: `SnapshotError` → clean "no snapshot found, run `nodeiq scan`" message (exit 1); any `LLMError` → clean message (exit 3, the code reserved for this since Phase 5A); any other exception → generic clean message (exit 4) — never a raw traceback
- [x] Unit tests (12 in `tests/llm/test_ask.py` + updated/added CLI tests in `tests/cli/test_main.py`) covering successful answers, latest/explicit snapshot loading, missing/malformed snapshot, missing API key, authentication failure, timeout, verbatim prompt/question/answer pass-through, and CLI integration
- [x] Manual end-to-end verification: `nodeiq ask` against a real Ubuntu snapshot, with a real configured `OPENAI_API_KEY`, produced a correct, evidence-grounded, guardrail-compliant answer; graceful failure verified for missing snapshot, invalid `--snapshot` path, and missing API key
- [x] Security review: `OPENAI_API_KEY` still read only in `client.py`; confirmed never appears in CLI output, exceptions, snapshots, or prompts; Prompt Builder and OpenAI Client both unchanged
- [x] Quality review: CLI remains thin (one call to `answer_question()` plus exception translation, no orchestration duplicated), no duplicated prompt construction, no hidden coupling

## Phase 7 — Robustness

- [ ] Apply timeouts to every subprocess call
- [ ] Handle partial collector failures end-to-end (verify `collection_errors` works in practice)
- [ ] Implement secret redaction for logs/config data
- [ ] Handle very large log volumes gracefully
- [ ] Handle missing systemd gracefully
- [ ] Handle different firewall implementations (iptables / nftables / ufw)
- [ ] Handle permission errors gracefully (e.g., non-root user)

## Phase 8 — Testing

- [ ] Unit tests for every collector (happy path + failure paths)
- [ ] Integration tests for CLI commands against fixture snapshots
- [ ] End-to-end validation pass
- [ ] Demo preparation

---

## Notes on Using This File

- Check a box only when the task is actually complete and verified, per the
  Definition of Done in `PROJECT_RULES.md`.
- If a task turns out to need splitting into smaller tasks mid-phase, add
  the new sub-tasks (unchecked) rather than silently expanding scope.
- Update the **Progress Summary** section at the top every time a checkbox
  changes, so the two never drift out of sync.
