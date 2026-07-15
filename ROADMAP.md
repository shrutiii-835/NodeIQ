# ROADMAP.md — NodeIQ High-Level Roadmap

This file tracks NodeIQ's milestones at a high level. For the detailed,
checkbox-level task breakdown, see [CHECKLIST.md](CHECKLIST.md). For *why*
each milestone is ordered this way, see [CONTEXT.md](CONTEXT.md) Section 8.

---

## Status: v1 Complete and Release-Ready

Every milestone below is done, tested, and verified on a real Ubuntu 24.04
machine (a Multipass VM, plus two independent fresh-install/`git clone`
simulations — Phase 8 and Phase 9 — and five hands-on scenario validations;
see `LOGS.md`'s Phase 8 and Phase 9 entries for the full record). NodeIQ's
three commands (`scan`, `report`, `ask`) and its interactive shell are all
real, working software, not a plan. Phase 9 added a final security audit
(secret redaction for collected log messages, a full repository secret
sweep, and confirmed-in-practice firewall/permission-error handling) with
nothing left that blocks a release.

A small number of items remain deliberately unchecked in `CHECKLIST.md`
rather than silently marked done — see "Known Gaps, Recorded Honestly"
below. None of them block v1; they're recorded so future work starts from
an accurate picture, not a guess.

---

## Long-Term Milestones — All Complete

1. **Phase 1 — Project Architecture.** Repository structure and the full
   documentation set (`README.md`, `CONTEXT.md`, `PROJECT_RULES.md`,
   `LOGS.md`, `CHECKLIST.md`, `DECISIONS.md`, `ROADMAP.md`,
   `LEARNING_NOTES.md`); git initialized.

2. **Phase 2 — Data Model.** The snapshot JSON schema, documented field by
   field in `docs/snapshot_schema.md`. (One item intentionally left open:
   `dataclasses` vs. `TypedDict` for in-code schema representation — a
   real, still-undecided question, not an oversight.)

3. **Phase 3 — Collectors.** All 9 v1 collectors built, tested (mocked
   unit tests plus real Multipass VM integration tests for each), and
   registered with the coordinator: system metadata, CPU/memory,
   processes, disk & inodes, services, logs, network, scheduled jobs,
   permissions. `nodeiq.core.coordinator.run_scan()` runs all of them,
   aggregates `collection_errors`, and assembles one in-memory snapshot —
   one broken collector never stops the rest.

4. **Phase 4 — Report Generation.** The Summary Engine
   (`nodeiq.summary`) turns a raw snapshot into a concise, deterministic
   Summary (per-section `status`/`headline`/`highlights`/`concerns`,
   computed only from fixed thresholds — never AI, never inferred
   causes). The Report Formatter (`nodeiq.report`) renders a Summary as
   clean terminal text, presentation only.

5. **Phase 5 — CLI.** `nodeiq scan`, `nodeiq report` (`--section`,
   `--snapshot`, `--fresh`), and `nodeiq ask` wired up with `argparse`
   (`src/nodeiq/cli/`), reachable via `python -m nodeiq` or the installed
   `nodeiq` console script.

6. **Phase 6 — LLM Integration.** The Prompt Builder (`nodeiq.llm.prompt`)
   builds a fixed, versioned, guardrail-enforcing prompt from a question
   and a Summary; the OpenAI Client (`nodeiq.llm.client`) is the one
   module that talks to OpenAI, with retries, timeouts, and every SDK
   failure translated into a clean, project-specific exception;
   `nodeiq.llm.ask.answer_question()` composes the whole pipeline, and
   `nodeiq ask` calls it — evidence-only answering, so the LLM never
   invents a fact it wasn't given.

7. **Phase 7 — UX, Hardening & Robustness.**
   - **7A — User Experience & Platform Awareness:** an interactive shell
     (running `nodeiq` with no subcommand — a `NodeIQ>` prompt reusing
     the exact same `ask` pipeline), platform/distribution detection with
     a clean refusal on non-Linux systems, and consistent Question/Answer
     presentation.
   - **7B — Hardening:** a secret-safe deployment helper
     (`scripts/sync_to_vm.sh`), a stale-snapshot freshness warning,
     prompt/response size limits so no single request can become
     unbounded, `nodeiq --version` backed by one single version source,
     and a full security/quality review.
   - **7C — Robustness:** timeouts, partial-collector-failure handling,
     large-log-volume handling, and missing-systemd handling were all
     already true from earlier phases and re-verified here; secret
     redaction for log/config *content* remains a known, recorded gap
     (see below).

8. **Phase 8 — Testing & Validation.** The full automated test suite
   (unit tests for every collector and every module, integration tests
   for the CLI) plus a genuine end-to-end validation pass: a fresh-install
   simulation (`git clone` → venv → `pip install -e .` → configure
   `.env` → verify every command) and five real, hands-on scenarios
   (disk usage, a stopped service, a new listening process, generated log
   warnings/errors, a permissions change) on a real Ubuntu 24.04 VM.

---

## Known Gaps, Recorded Honestly

Per this project's own practice of writing down a real limitation rather
than silently overstating completeness:

- ~~Secret redaction for log/config content~~ — **fixed in Phase 9**:
  `nodeiq.core.redaction.redact_secrets()` sanitizes API keys, tokens,
  passwords, credentials, and PEM private-key blocks in every collected
  log message before it can reach a snapshot, Summary, report, or prompt.
- **Firewall-implementation variance** (`iptables`/`nftables`/`ufw`) and
  **non-root permission/root-required handling** were both explicitly
  verified during Phase 9's release validation on a real Multipass
  Ubuntu VM with all three firewall tools installed: run as an
  unprivileged user, all three commands fail with a permission error,
  and `network.py`'s `_detect_firewall()` degrades to
  `{"tool": None, "enabled": None}` rather than crashing — confirmed,
  not just assumed.
- **No demo script or slide deck exists.** Arguably out of scope for this
  project's own goals, but left unchecked rather than assumed done.

---

## Post-v1 Future Directions *(not scheduled into any phase)*

- Remote host support (currently single, local server only)
- Historical snapshot comparison / trend detection
- Scheduled scans (via cron or systemd timers) with alerting
- Support for multiple LLM providers
- A simple web UI for browsing reports
- Question-aware routing between the Summary and the raw snapshot
  (`docs/prompt_builder_design.md` Section 15)
