# Report Formatter — NodeIQ

**Status:** Implemented (`src/nodeiq/report.py`), Phase 4.2. Formats an
already-computed Summary (`docs/summary_engine_design.md`,
`src/nodeiq/summary.py`) as a plain-text terminal report. No CLI
command (`nodeiq report`, Phase 5) exists yet — the current, only
consumer is the developer utility `dev_summary.py`.

Read this alongside [summary_engine_design.md](summary_engine_design.md)
(the shape of what this module consumes).

---

## Where This Fits

```
run_scan()  →  save_snapshot()  →  summarize_snapshot()  →  format_report()  →  print(...)
   raw snapshot        .json file          Summary (dict)       report (str)
```

`format_report()` is the first real consumer of a Summary. It sits
**after** the Summary Engine, never beside or inside it: `nodeiq.summary`
gains no dependency on `nodeiq.report`, and `format_report()` depends on
nothing but the plain Summary dict shape `summarize_snapshot()` already
produces. Either module can change independently — a future CLI
formatter, an OpenAI prompt builder, or a web UI serializer could each
consume the same Summary without `format_report()`'s existence changing
anything about how a Summary is computed.

---

## Separation of Summary vs. Formatter

These are two distinct, single-purpose layers, not one job split
arbitrarily in two:

- **The Summary Engine's job** (`nodeiq.summary`) is deciding *what
  matters*: which facts to surface, what counts as a concern, and what
  each section's `status` is — all under strict, transparent rules
  (fixed thresholds only, never AI, never inferred causes). Its output
  is a plain dict, not text — deliberately consumer-agnostic (see
  `docs/summary_engine_design.md` Section 5).
- **The Formatter's job** (`nodeiq.report`) is deciding *how it looks on
  a terminal*: headings, indentation, bullet points, which fields to
  show and which to omit. It makes zero judgment calls about what's
  healthy, concerning, or worth mentioning — every one of those
  decisions was already made, once, by the Summary Engine.

Concretely, `format_report()` never computes a `status`, never decides
whether a number crosses a threshold, and never adds a highlight or
concern that wasn't already in the Summary it was given. It only
arranges already-decided facts on a page. This mirrors two precedents
already established elsewhere in this project: collectors don't do
presentation work (`docs/collector_guidelines.md`), and the Summary
Engine doesn't gather its own raw facts (`docs/summary_engine_design.md`
Section 1) — this is the same "one layer, one job" discipline applied a
third time.

**Why keep them separate instead of one function that summarizes and
prints?** Because a Summary is reused by more than one consumer. A
terminal report, a future OpenAI prompt, and a future web UI all want
the *same* underlying facts, but each wants them shaped completely
differently — one as indented plain text, one as JSON embedded in a
prompt, one as HTML. If summarization and formatting were fused into
one function, every one of those consumers would have to re-derive the
facts themselves, duplicating (and risking drift in) the threshold
logic `nodeiq.summary` already owns exclusively.

---

## Formatting Philosophy

- **Presentation only, no new facts.** `format_report()` reads
  `status`, `headline`, `highlights`, and `concerns` exactly as the
  Summary provides them — it does not invent, reorder, filter, or
  reinterpret any of them beyond deciding whether to print a given
  block at all (e.g., omitting an empty `concerns` list).
- **Concerns are shown only when present.** An empty `concerns` list
  means nothing worth flagging was found — the report shows no
  "Concerns:" heading at all in that case, rather than printing an
  empty one. The same applies to `highlights`: an empty list produces
  no bullet lines, never a blank or placeholder line.
- **No raw JSON, ever.** The report never calls `json.dumps`, `repr`,
  or prints a dict/list directly — every line is either a literal
  heading or a string field the Summary already provides. A section's
  `evidence` dict (the concise, structured backing numbers behind its
  `status`/`concerns`) is deliberately **not** printed at all: it exists
  for machine consumers (a future OpenAI prompt, a future export), and
  printing it here would duplicate information the section's `headline`
  and `highlights` already say in readable form — see
  `docs/summary_engine_design.md` Section 7's "counts and highlights
  belong in the Summary" principle, applied one more layer down.
- **Deterministic.** Given the same Summary dict, `format_report()`
  always returns the exact same string — no current timestamp, no
  randomness, no environment-dependent formatting. (The Summary's own
  `generated_at` field is itself dynamic bookkeeping, per
  `docs/summary_engine_design.md` Section 10 — but the *formatter*
  doesn't introduce any further non-determinism of its own.)
- **Missing or unavailable sections render cleanly, never crash.** A
  section that's `None`, absent from `summary["sections"]` entirely, or
  in the standard "unavailable" shape (`available: False, status:
  "unknown"`) still produces a normal-looking heading and headline line
  — there's no special-cased "crash" path, because none of those states
  are actually exceptional from the formatter's point of view; they're
  just Summary data like any other section, per
  `docs/summary_engine_design.md` Section 9's "availability must
  survive" guarantee.

---

## Report Shape

```
======================================================================
NodeIQ Report
Host: main-cattle
Snapshot: 2026-07-15T11:37:30.805455+00:00
======================================================================

System [HEALTHY]
Ubuntu 24.04.4 LTS, kernel 6.8.0-134-generic, up 6h 21m
  - Hostname: main-cattle
  - Architecture: aarch64

CPU & Memory [HEALTHY]
Memory 24.5% used
  - Load average: 0.17 (1m), 0.07 (5m), 0.02 (15m)

Disk [WARNING]
Fullest filesystem at 92.0%
  - 8 filesystem(s) checked
  Concerns:
    - Highest filesystem usage at 92.0% (warning threshold: 85%)
```

Sections render in the same order `summary["sections"]` already has
them (the order `summarize_snapshot()` built them in, mirroring
`_REGISTERED_SUMMARIZERS`) — the formatter doesn't hardcode or re-sort a
section list of its own, so it stays correct even if a future 10th
section is added to the Summary Engine without any change here.

---

## Module and Naming

**One new module, `src/nodeiq/report.py`**, exposing exactly one public
function, `format_report(summary: dict) -> str`, plus one small private
helper (`_format_section`) and one small display-title lookup
(`_SECTION_TITLES`, currently a single entry for `cpu_memory` — the only
one of the 9 v1 section names whose default `.title()`-cased form would
read poorly). This mirrors `nodeiq.summary`'s own "one file for v1, not
a package" decision (`docs/summary_engine_design.md` Section 13): 9
sections, each formatted by a few lines of shared logic, don't yet
justify a `report/` package.

---

## Quality Review

Applying the same "simplify, don't add ceremony" check used in every
prior quality review this project has done:

- **No duplicated formatting logic.** A single `_format_section` helper
  handles every section identically — there is no per-section
  formatting function the way `nodeiq.summary` has a per-section
  *summarizing* function, because unlike summarization (where each
  section's thresholds are genuinely different), every section's
  *rendering* rule is the same: title, status, headline, highlights,
  concerns-if-any. Writing 9 near-identical `_format_system`,
  `_format_disk`, ... functions here would have been duplication
  invented for symmetry with `nodeiq.summary`, not because the sections
  actually render differently.
- **No new abstraction invented.** A `Section`/`ReportLine` class, a
  template-string mini-language, or a pluggable renderer registry were
  all considered and rejected — none solve a problem that actually
  exists yet with only one report format (plain terminal text) and one
  consumer (`dev_summary.py`). The plain list-of-lines-then-`"\n".join`
  approach already used elsewhere in this codebase's simplest functions
  is sufficient.
- **`_SECTION_TITLES` stays a single-entry dict, not a rule engine.**
  Only one of the 9 real section names (`cpu_memory`) needs a special
  display title; a general-purpose acronym-detection scheme would be
  solving a problem with no second real instance yet.

No abstraction proposed for this phase failed this review — the
simplest structure that satisfies the stated requirements is what got
built.
