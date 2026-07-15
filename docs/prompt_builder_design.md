# Prompt Builder & Guardrail Design — NodeIQ

**Status:** Design only (Phase 6A). No code exists yet —
`src/nodeiq/llm/` (already reserved, empty, in `PROJECT_RULES.md`
Section 1's folder structure) is not created, no OpenAI SDK is added to
`requirements.txt`, and nothing in `nodeiq.core`, `nodeiq.summary`,
`nodeiq.report`, or `nodeiq.cli` changes as a result of this document.
This exists so implementation (Phase 6B, presumably) starts from a
reviewed plan, per this project's established "design before
implementation" convention (`docs/process_collector_design.md`,
`docs/summary_engine_design.md`, `docs/cli_design.md`).

Read this alongside [summary_engine_design.md](summary_engine_design.md)
(the shape of the evidence this design consumes), and
[cli_design.md](cli_design.md) (`ask`'s current placeholder, and Section
4.3's already-recorded open question about what evidence `ask` hands to
Phase 6).

---

## 1. Purpose and Scope

Every other layer of NodeIQ is built: 9 collectors, `run_scan()`,
snapshot persistence, the Summary Engine, the Report Formatter, and the
production CLI. `nodeiq.cli.main._cmd_ask` is currently a placeholder
that always prints "AI-powered question answering isn't implemented
yet." The only remaining major capability is turning a user's question
plus the evidence NodeIQ already collects into an actual, LLM-generated
answer.

This document designs the one component responsible for that first
step: converting `(question, evidence)` into a complete, ready-to-send
prompt. It does **not** design or implement the LLM client itself
(which SDK call, retry/timeout handling, how `ask`'s placeholder becomes
real), and it does not implement question routing, section-filtering,
or an OpenAI dependency. Per this task's explicit scope, **no Python
code is written or changed by this document.**

---

## 2. Where This Fits

```
User Question (str)                    Summary (nodeiq.summary) — today
        │                               Raw Snapshot (nodeiq.core.snapshot) — future, see Section 12
        │                                        │
        └───────────────────┬────────────────────┘
                             ▼
                  ┌───────────────────────┐
                  │    Prompt Builder        │   nodeiq.llm.prompt (proposed)
                  │    (this design)         │   pure function, no I/O
                  └────────────┬──────────────┘
                               │ a Prompt: {system, user}
                               ▼
                  ┌───────────────────────┐
                  │   LLM Client (Phase 6B)  │   not designed here
                  └────────────┬──────────────┘
                               │ raw answer text
                               ▼
                  ┌───────────────────────┐
                  │  `nodeiq ask` (CLI)       │   prints the answer
                  └───────────────────────┘
```

The Prompt Builder sits **beside**, not **inside**, every existing
layer — exactly the same relationship `nodeiq.report` already has to
`nodeiq.summary` (`docs/report_formatter.md`), and `nodeiq.summary` has
to `nodeiq.core.coordinator`/`nodeiq.core.snapshot`
(`docs/summary_engine_design.md` Section 2). Concretely:

- **Independent of the CLI:** `nodeiq.cli` will eventually call the
  Prompt Builder and the LLM client, in that order — the Prompt Builder
  never imports or knows about `argparse`, exit codes, or how `ask`
  prints its result.
- **Independent of the OpenAI client:** the Prompt Builder produces
  plain data (Section 5's `Prompt` shape) and hands it to whatever calls
  the LLM. It never imports an SDK, never makes a network call, and
  never knows which provider will ultimately receive its output (see
  Section 13, Open Question 3).
- **Independent of the collectors and the coordinator:** the Prompt
  Builder only ever receives an already-computed evidence dict (a
  Summary today, per Section 12) — it never calls `run_scan()`,
  `load_snapshot()`, or anything in `nodeiq.collectors`. This mirrors
  `docs/architecture.md`'s "dependencies only ever point downward" rule,
  applied one layer further out: the Prompt Builder depends on the
  *shape* of evidence a lower layer already produced, never on how that
  evidence was produced.
- **The only component responsible for constructing prompts:** no
  prompt text or evidence-serialization logic should ever be duplicated
  elsewhere (e.g., inside `nodeiq.cli` or a future test harness) — every
  future consumer that needs a prompt calls this one component, the same
  "shared logic lives in exactly one place" principle already applied at
  every other layer of this project.

---

## 3. Prompt Builder Responsibilities

**Owns:**

- The system prompt's fixed text (Section 6) — NodeIQ's persona, rules,
  and guardrails (Section 10), versioned (Section 8).
- Evidence serialization (Section 7) — turning a Summary (or, later, a
  raw snapshot) into the text the model actually reads.
- User prompt assembly (Section 6) — evidence plus the literal question,
  in a fixed, deterministic structure (Section 9).
- The final `Prompt` shape handed to whatever calls the LLM.

**Explicitly does not own:**

- Calling any LLM API, or knowing which one will be called (Section 2).
- Deciding *whether* a question needs the Summary or the raw snapshot
  (question routing — explicitly out of scope this phase, Section 11).
- Deciding what counts as "healthy," "a concern," or a threshold — those
  decisions are already made, once, by `nodeiq.summary`, before evidence
  ever reaches this layer (`docs/summary_engine_design.md`).
- Printing, formatting for a terminal, or deciding CLI exit codes —
  those belong to `nodeiq.report`/`nodeiq.cli` respectively.

**Proposed module:** `src/nodeiq/llm/prompt.py` (the `llm/` folder is
already reserved, empty, in `PROJECT_RULES.md` Section 1). One public
function is enough for v1:

```python
def build_prompt(question: str, evidence: dict, evidence_kind: str = "summary") -> dict:
    """Returns {"system": <str>, "user": <str>, "prompt_version": <str>}."""
```

**Why a plain dict, not a dataclass:** the same reasoning
`docs/summary_engine_design.md` Section 5 already gave for the Summary
shape applies again here — a `Prompt`'s entire purpose is to be handed,
almost immediately, to an SDK call that itself expects plain
strings/dicts (e.g. OpenAI's `messages=[{"role": "system", ...},
{"role": "user", ...}]`). A dataclass would force an `asdict()`-style
conversion step for no compensating benefit.

**Why this must be a pure function:** given the same `question` and
`evidence`, `build_prompt()` must always return the same `Prompt` — no
I/O, no network call, no randomness, no current-time stamping inside
the builder itself (any timestamp shown to the model comes from the
evidence's own `generated_at`/`snapshot_timestamp` fields, not from the
builder calling `datetime.now()`). This is what makes it trivially unit
-testable with a literal fixture dict, exactly like every summarizer and
`format_report()` before it — no mocking a network call required to test
prompt construction.

---

## 4. Prompt Flow

1. `nodeiq ask "<question>"` (Phase 6B, replacing today's placeholder)
   resolves a snapshot exactly as `docs/cli_design.md` Section 4.3
   already designed (default: latest; `--fresh`: scan first;
   `--snapshot PATH`: a specific file).
2. The CLI computes evidence — a Summary via `summarize_snapshot()`
   today; possibly the raw snapshot too, per Section 12's still-open
   question.
3. The CLI calls `build_prompt(question, evidence)`.
4. The CLI (or a small LLM-client wrapper, Phase 6B, not designed here)
   sends the returned `Prompt`'s `system`/`user` strings to the LLM.
5. The CLI prints the raw answer text — no reformatting, since the
   system prompt itself (Section 6) already instructs the model to
   answer in plain, direct prose suitable for a terminal.

---

## 5. The `Prompt` Shape

```python
{
    "system": "<the fixed, versioned system prompt text>",
    "user": "<evidence block>\n\nQuestion: <the verbatim user question>",
    "prompt_version": "v1",
}
```

`prompt_version` is not sent to the model — it travels alongside the
`Prompt` purely so a caller (the CLI, a future eval harness, a bug
report) can record *which* system prompt text was live for a given
answer (Section 8).

---

## 6. System Prompt Design

The system prompt is fixed text, identical for every question, built
once (versioned, Section 8) rather than assembled per-question. It
establishes, in this order:

1. **Identity and role.** NodeIQ is an evidence interpreter for a single
   Linux server's collected diagnostic data — explicitly **not** a
   general-purpose assistant, not a Linux shell, and not connected to
   the live machine (Section 10's Prompt Philosophy, restated here as
   the model's own framing, not just a design-doc statement).
2. **The evidence boundary** (Section 10.9) — stated first among the
   actual rules, since it is the single most load-bearing guardrail:
   the model's entire universe of facts is the evidence block it is
   about to receive in the user message; nothing from general knowledge
   about "what Linux servers usually do" may be used to fill a gap.
3. **What it may conclude, must never conclude, and must refuse**
   (Section 10.1–10.2) — the explicit rules, not left implicit.
4. **Uncertainty and phrasing conventions** (Section 10.4) — the exact
   phrasing patterns the model should reach for.
5. **Style** — plain, direct, terminal-appropriate prose; no markdown
   headers or decorative formatting (the CLI prints the answer
   verbatim, per Section 4, step 5).

The **user prompt**, per question, contains exactly two things, in this
order (Section 9 explains why):

1. The evidence block (Section 7).
2. The literal question, clearly labeled (`Question: <...>`), so it is
   never ambiguous which part of the message is instruction-like
   evidence and which part is the actual request — a deliberate,
   simple mitigation for the model ever treating part of the evidence
   text as if it were a new instruction.

---

## 7. Evidence Formatting

**Recommendation: JSON, not hand-written prose.** The Summary is
already a plain, serializable dict (`docs/summary_engine_design.md`
Section 5) — `json.dumps(evidence, indent=2)` costs nothing to produce,
is exactly what the model can parse most reliably, and avoids a second,
independent "re-summarize the Summary into prose" step that could
silently drift from what the Summary actually says. This mirrors the
project's own recurring principle: don't re-derive facts a lower layer
already computed (`docs/report_formatter.md`'s whole argument for why
`format_report()` never recomputes a `status`).

**Which fields to include per section:** all of them — `available`,
`status`, `headline`, `highlights`, `concerns`, `evidence`, and
`errors`. In particular:

- `errors` must never be dropped — CONTEXT.md Section 4 is explicit
  that missing/failed evidence "must be visible... so the LLM (and the
  user) knows the answer may be incomplete." Omitting `errors` from the
  prompt to save tokens would directly violate this non-negotiable
  rule.
- `status`/`concerns` may be shown to the model **as already-computed
  facts to cite**, not as something the model re-derives — the model is
  told these are deterministic, threshold-based labels already
  computed by NodeIQ, not the model's own judgment to second-guess or
  restate more strongly (Section 10.1).

**A visible freshness marker:** the evidence block is prefixed with the
Summary's own `snapshot_timestamp` (when the data was collected) and
`generated_at` (when the Summary was computed) — both already exist
in every Summary, no new field needed — so the model can (and per
Section 10.6, must) frame any answer relative to that point in time,
not as a claim about "right now."

---

## 8. Prompt Versioning Strategy

A single named string constant in `nodeiq.llm.prompt` — e.g.
`_PROMPT_VERSION = "v1"` — echoed into every `Prompt`'s
`prompt_version` field (Section 5). Bump it whenever the system
prompt's *wording that changes model behavior* changes (a new guardrail
rule, a changed uncertainty-phrasing instruction, a restructured
evidence format) — not for a typo fix or a comment change. This mirrors
the project's existing precedent for `metadata.nodeiq_version` and
`docs/snapshot_schema.md`'s `schema_version`: a plain, visible version
marker, not a full changelog/migration framework, kept only as
complex as the current, real need (one active version, no history of
past versions tracked anywhere yet — see Open Question 2, Section 13).

---

## 9. Output Structure and Ordering Rationale

```
System Prompt
    ↓
Evidence
    ↓
User Question
```

**Why the system prompt comes first, as its own separate message
(not prose prepended to the user message):** this maps directly onto
how real chat-completion APIs already work — a system/developer role
message, sent once, distinct from user messages — so this isn't merely
"put the rules at the top of one blob of text," it's the natural
mapping onto the actual message-role structure every mainstream chat
API already has (which also makes Section 13's "future multi-provider
support" question easier: the `{system, user}` shape ports directly).
Establishing the rules in a structurally separate channel, before the
model has seen any data, is also a stronger guardrail placement than
mixing instructions and evidence in one undifferentiated block.

**Why evidence comes before the question, within the user message:**
the model encounters the ground truth before the specific request,
mirroring how a human analyst would naturally be handed "here is the
data" before "here is what I want to know," rather than the reverse.
This also gives the evidence a clear, delimited position ahead of a
clearly labeled `Question:` — reducing the chance the model reads part
of the evidence text as if it were an instruction, since the actual
instruction (the question) is unambiguously the last, distinctly
labeled thing in the message. This also aligns with common guidance
that models attend most reliably to content placed at the end of a
long context — the evidence is bulk reference material; the question is
the specific, load-bearing final ask.

---

## 10. Guardrail Design

This is where NodeIQ's AI behavior is actually defined — every rule
below is intended to become literal system-prompt text (Section 6),
not just a design-time intention.

### 10.1 What the model is allowed to conclude

- A direct restatement of a fact literally present in the evidence
  (e.g., "memory usage is 24.5%, per the evidence").
- A comparison between two facts both literally present in the same
  evidence block (e.g., "the disk section reports 92% usage, above the
  85% warning threshold NodeIQ already flagged").
- Citing a Summary's own already-computed `status`/`concerns` verbatim
  — these are already transparent, deterministic, threshold-based
  facts computed one layer down (`docs/summary_engine_design.md`
  Section 10); the model may repeat them, but must not *upgrade* their
  severity, invent a new concern alongside them, or treat their
  presence as license to speculate further.
- Noting an **observed correlation** between two facts that are both
  explicitly present (e.g., "the `services` section shows `nginx`
  failed, and the `logs` section separately shows an error mentioning
  `nginx` in the same window") — but only as a stated correlation
  between two named, cited facts, never elevated to a cause (Section
  10.6).

### 10.2 What the model must never conclude

- A **root cause** not literally stated in the evidence. NodeIQ's
  collectors never record causal claims — no collector produces a "why"
  field — so in practice this guardrail reduces to: **the model should
  almost never state a cause for anything**, and this should be said
  plainly in the system prompt rather than left to be inferred from a
  softer rule, since "the evidence sort of implies a cause" is exactly
  the kind of gradual erosion this guardrail exists to prevent.
- **Recommendations or remediation steps** ("restart the service,"
  "clear /var/log," "increase memory") — a direct, unconditional
  restatement of CONTEXT.md Section 4 and `docs/summary_engine_design.md`
  Section 10's existing "never diagnose, never recommend" rule, carried
  through to the one layer that can actually violate it in free text.
- **Invented facts** of any kind not directly supported by evidence:
  services, processes, configuration values, resource numbers, or
  security conclusions the model wasn't given. If a number isn't in the
  evidence, the model must not estimate, round beyond the evidence's own
  precision, or interpolate one.
- **Security judgments beyond what a section's `concerns` already
  states.** `permissions_collector.md` is explicit that NodeIQ v1's
  permissions collector is "not a security audit" — the model must not
  declare something "suspicious" or "a vulnerability" beyond literally
  repeating what a section already flagged.
- **Any claim of having done something beyond reading the supplied
  evidence** — the model never ran a command, never checked anything
  live, and must never phrase an answer as if it had (Section 10.9).

### 10.3 When the model must refuse, or say evidence is insufficient

- The relevant section is `available: false`, or its `status` is
  `"unknown"`, for the specific thing being asked (e.g. asked about
  failed services while `services.available` is `false` because
  systemd isn't present).
- The question requires evidence NodeIQ v1 categorically does not
  collect (e.g. application-level logs, per-request tracing, anything
  outside the 9 collectors' documented scope).
- The question requires comparing two points in time (Section 11,
  Comparison) and NodeIQ has no history/diff capability yet (Section
  13, Open Question 7) — the model must say plainly that only one
  snapshot's evidence was provided, not attempt to imagine a prior
  state.
- The question is fundamentally outside what a point-in-time snapshot
  can answer at all (Section 10.9) — e.g. "is this happening right
  now," "why does this specific error message occur," or anything
  requiring live interaction or general troubleshooting knowledge not
  grounded in the supplied evidence.

### 10.4 How uncertainty must be communicated

Three distinct phrasing registers, and the model must use the one that
actually matches its epistemic status — never blur them:

| Register | Example phrasing | When |
|---|---|---|
| **Fact** | "According to the evidence, X." | A value/field literally present. |
| **Observed correlation, not a cause** | "The evidence shows both X and Y; this may be related, though the evidence does not establish a cause." | Two facts co-occur, no causal statement exists in evidence. |
| **Explicit insufficiency** | "The evidence does not contain enough information to determine Z." | The question can't be answered from what was supplied. |

The model must never use a hedge phrase that implies access to
information it doesn't have (e.g. "it's probably still running" implies
real-time knowledge) — the correct register is always "as of the
snapshot taken at `<snapshot_timestamp>`, the evidence shows..."
(Section 10.6).

### 10.5 Conflicting evidence

If two sections appear to disagree (e.g., a service shown as
`running` while a log entry elsewhere describes it crashing), the model
must **surface both facts plainly and name the discrepancy explicitly**
— never silently pick one side, never guess which one is "more
correct." This is itself an instance of "state the observation, not a
resolved conclusion" (Section 10.1).

### 10.6 Historical logs vs. current state

Logs (`logs` section) describe events that already happened — the
past. Every other section's fields describe the state at the moment of
the scan — a point-in-time present, not "right now." The system prompt
must keep these grammatically distinct: the model must never present a
log entry as describing the current moment, and must never treat "no
errors among the last N entries" as "there have never been more errors
than that" — the `logs.truncated` flag exists specifically to
communicate this bound, and the guardrail requires the model to check
and mention it when relevant, rather than silently assume completeness.

### 10.7 Unsupported questions

Questions genuinely outside what NodeIQ's evidence can address (asking
what a specific error message *means* in general, asking about
application code, asking for live interaction) must be met with a plain
statement that NodeIQ cannot determine that from the collected
evidence — never a fallback to the model's general Linux knowledge,
which would directly violate CONTEXT.md Section 4's "never answer from
general knowledge about what Linux servers usually do."

### 10.8 Cause vs. observation — restated as one explicit rule

Because this distinction appears throughout the above and is the
single easiest guardrail to erode gradually in practice, it is stated
once more, plainly, as its own rule: **the model may state what the
evidence shows (an observation); the model may never state why it is
that way (a cause) unless the evidence itself contains an explicit
causal statement.** Since no NodeIQ v1 collector ever produces a causal
statement, this rule is, in practice, close to absolute for v1.

### 10.9 Evidence boundaries (the foundational guardrail)

The model's entire universe of facts, for any given question, is the
evidence block in that one prompt — nothing from training data about
"typical" servers, "common" causes, or "usual" fixes may be used to
fill a gap. This is stated first and most prominently in the system
prompt (Section 6) precisely because every other guardrail above is a
specific consequence of this one general rule.

---

## 11. Question Types — Discussion (no routing implemented)

For each category: whether the current Summary is sufficient, or
whether the raw Snapshot may eventually be needed, based on what the
Summary Engine actually keeps vs. discards
(`docs/summary_engine_design.md` Section 8's "counts and highlights
belong in the Summary; full, unbounded detail lists stay in the raw
snapshot" rule).

| Category | Example | Summary sufficient? | Notes |
|---|---|---|---|
| **Information** | "What kernel version is running?" | Yes | A direct field lookup (`system.evidence.kernel_version`) already present in every Summary. |
| **Explanation** | "Explain why memory usage is high." | Mostly | The Summary can state the observation (usage %, threshold crossed, single top memory consumer) but — per Section 10.2/10.8 — cannot state a cause. The raw snapshot's fuller process list (`processes.py` collects more than the Summary's single top-consumer highlight) could support a *more evidence-rich observation* later, not a cause. |
| **Analysis** | "Analyze disk usage." | Partially | The Summary intentionally keeps only `highest_disk_usage_percent` and a filesystem count — the full per-filesystem breakdown is deliberately raw-snapshot-only (Section 8's rule, cited above). A genuinely thorough "analyze every filesystem" answer needs `disk.filesystems` from the raw snapshot. |
| **Comparison** | "What changed since the previous snapshot?" | **No — neither is sufficient today.** | NodeIQ only ever loads the *latest* snapshot (`load_latest_snapshot()`); there is no history/diff capability at all yet (CONTEXT.md Section 9 lists this as an unscheduled future roadmap item). Per Section 10.3, the model must say so rather than guess. |
| **Troubleshooting** | "Why might this machine feel slow?" | Mostly | The Summary's `concerns` lists, read across all 9 sections at once, are exactly designed for this — safe, evidence-grounded leads (high load, blocked processes, high disk usage). The answer must present these as candidate observations, never confirmed causes (Section 10.1/10.8). |
| **Security** | "Is anything suspicious?" | Partially, with a strong caveat | The `permissions` and `network` sections give some signal (world-writable paths, listening ports), but `docs/permissions_collector.md` is explicit that this is "not a security audit." The honest answer is usually "the following facts were observed; NodeIQ v1 does not perform a full security audit" (Section 10.2). |

**General pattern:** the Summary is the right default evidence source
for most question categories, since it's already the noise-reduced
layer purpose-built for "what matters" (`docs/summary_engine_design.md`
Section 7). Categories that need the full, unbounded detail lists
(every filesystem, every process, every cron job, every log entry) will
eventually need the raw snapshot. Comparison needs a capability that
doesn't exist yet, regardless of evidence source. This analysis
motivates Section 12's `evidence_kind` parameter existing at all, but
**deciding which category gets which evidence source (question
routing) is explicitly out of scope for this phase.**

---

## 12. Evidence Source: Summary vs. Snapshot

`build_prompt()` is designed to accept **either** shape via its
`evidence_kind` parameter (Section 3), because Section 11's analysis
shows both are genuinely needed eventually — but which one gets used
for a given question is not decided or implemented here (Open Question
1, Section 13; this also directly touches `docs/summary_engine_design.md`
Section 17's own still-open Question 1 and `docs/cli_design.md` Section
4.3's note that `ask`'s exact evidence shape is a Phase 6 decision).

For Phase 6A's purposes, the important design commitment is only this:
**the Prompt Builder's evidence-formatting step (Section 7) must not
assume the Summary's specific shape is the only possible input** — it
should serialize whatever dict it's given as evidence, the same way
`json.dumps` doesn't care whether that dict is a Summary or a raw
snapshot. This keeps the door open for Section 11's harder question
categories without requiring a redesign of this module later.

---

## 13. Token-Conscious Design (trade-offs only, nothing implemented)

**Option A — send the entire Summary, every question.**

- *For:* the Summary is already small and bounded (9 sections, most
  collapsing to a few lines — `docs/summary_engine_design.md` Section
  7's "collectors already reduce noise" observation), so the token cost
  of sending all of it is modest and predictable. No routing logic is
  needed, which avoids a real risk: a naive keyword-based
  section-relevance filter could silently omit evidence that was
  actually relevant to the question, and a wrong-because-incomplete
  answer is a substantially worse failure mode than a slightly larger
  prompt. Several of Section 11's categories (Troubleshooting,
  cross-section correlation observations) genuinely benefit from the
  model seeing every section's `concerns` at once.

**Option B — send only sections judged relevant to the question.**

- *For:* token cost (and latency, and per-call price) scales with
  usage volume; a narrowly-scoped question (e.g. "what's the kernel
  version?") never needs the `network`/`logs`/`services` sections, and
  filtering could meaningfully cut cost with no loss of accuracy for
  such questions specifically.
- *Against:* requires solving question routing (explicitly out of
  scope this phase) correctly enough that a relevant section is never
  silently dropped — the exact failure mode Option A's "for" case
  warns about.

**Recommendation (not a decision — see Open Question, below):** default
to Option A for the first real implementation, since the Summary's
current size makes the savings from Option B speculative and the risk
of silently dropping relevant evidence real. Revisit only once genuine
usage data (real questions, real token costs) exists to justify the
added complexity — the same "evidence over speculation" discipline
already applied throughout this project (e.g. `docs/summary_engine_design.md`
Section 18 rejecting a speculative `SummaryContext`). The Prompt
Builder's evidence-formatting step should not need to change shape if
Option B is adopted later — only the dict it's handed would shrink.

---

## 14. Future Extensibility

- **A new question category or evidence source** doesn't require a
  redesign — `build_prompt()`'s `evidence_kind` parameter (Section 12)
  already anticipates more than one shape; a new category is a routing
  decision made *above* this module, not inside it.
- **A new LLM provider** (Section 13, Open Question 3) — the `{system,
  user}` plain-string shape (Section 5) doesn't assume OpenAI's exact
  message format; adapting it to another provider's API is a thin
  translation at the LLM-client layer, not a Prompt Builder change.
- **Citation strategy** (Section 13, Open Question 4) — if ever added,
  would live entirely in the system prompt's instructions (asking the
  model to reference which section/field it drew from) plus, possibly,
  a stricter evidence-formatting scheme (e.g. tagging each fact with an
  id) — a bounded, additive change to Sections 6/7, not a new module.
- **Prompt evaluation/regression testing** — since `build_prompt()` is
  a pure function, a future test suite could snapshot-test its exact
  output against fixture evidence (mirroring how `test_report.py`
  already snapshot-tests `format_report()`'s exact output) — no new
  testing infrastructure required, just more tests.

---

## 15. Open Questions

Recorded explicitly, per this project's practice of writing down a
genuine unresolved tension rather than guessing at a confident answer:

1. **Summary vs. Snapshot, resolved how and when?** Section 11's
   analysis shows the Summary is sufficient for most question
   categories but not all — but *how* a future implementation decides
   which one to use for a given question (question routing) is
   deliberately not designed here, per this task's explicit scope.
2. **Prompt versioning: is a single string constant enough long-term?**
   No history of past prompt versions is tracked anywhere yet — if a
   future need arises to compare model behavior across prompt versions
   (e.g. a regression in answer quality after a wording change), a
   more structured versioning/changelog scheme might be needed. Not
   built now, since no such need exists yet.
3. **Future multi-provider support** — the `{system, user}` shape is
   designed to be provider-agnostic (Section 14), but whether NodeIQ
   ever actually adds a second provider (per ADR-005's own "not a
   permanent constraint" framing) remains genuinely undecided.
4. **Citation strategy** — should an answer ever be required to cite
   which section/field it drew from? Would improve auditability
   (directly serving CONTEXT.md's "you can always see exactly what
   evidence the LLM was given" goal) but adds real prompt complexity
   and depends on the model reliably complying with a citation format
   — genuinely open, not decided here.
5. **Future conversation memory** — should `ask` ever support a
   multi-turn, remembered conversation within one session? This would
   be a real philosophical fork: every other NodeIQ command (`scan`,
   `report`) is fully stateless between invocations; conversation
   memory would be the first stateful CLI behavior in the project.
   Not proposed for v1.
6. **Should the Prompt Builder ever become question-aware** — adapting
   evidence selection or system-prompt wording based on a detected
   question category? Deliberately deferred (this task's explicit "do
   not implement question routing" instruction) until real usage data
   exists to justify it.
7. **Comparison-type questions** — should a future history/diff
   capability (CONTEXT.md Section 9's already-listed, unscheduled
   "historical snapshot comparison" item) be built specifically to
   support this question category, or should the model simply keep
   declining it indefinitely? Not decided here.
8. **Should a section's `status` (e.g. `"critical"` vs. `"unknown"`)
   change how prominently it's surfaced in the prompt** (beyond simply
   being present in the evidence, unmodified)? Leaning toward "no — any
   such prominence decision would itself be an interpretive act this
   layer shouldn't make," but flagged as a genuine, non-obvious edge
   worth a second opinion rather than assumed.

---

## 16. Quality Review

Applying the same three-question test used in every prior design in
this project (`docs/collector_guidelines.md`, `docs/summary_engine_design.md`
Section 18, `docs/cli_design.md` Section 10), plus the specific risks
this task asked to check for:

- **Hidden coupling:** the Prompt Builder's only real coupling is to
  whatever dict shape it's handed as evidence (Section 12) — the same,
  already-accepted kind of coupling `nodeiq.report` already has to
  `nodeiq.summary`'s output shape. Nothing new or undocumented was
  introduced; Section 2 states this coupling explicitly rather than
  leaving it implicit.
- **Unnecessary complexity:** a question-classification/routing system,
  a citation-enforcement mechanism, and a full prompt-version changelog
  framework were all considered (Sections 11, 13, 14, 15) and
  explicitly deferred rather than built now, none justified by a real,
  current need — the same "no abstraction until justified by evidence"
  discipline `DECISIONS.md` ADR-012 already established for this
  project.
- **Token waste:** directly addressed in Section 13 as an explicit
  trade-off discussion, not a blind default — the "send the whole
  Summary" recommendation is reasoned from the Summary's actual current
  size, not assumed, and is flagged for revisit once real usage data
  exists.
- **Maintainability:** the system prompt is proposed as a single,
  versioned, plain-text constant (Sections 6, 8) — easy to review and
  diff in git, not scattered across templates or assembled
  conditionally per question.
- **Hallucination risks:** this is the primary risk surface for this
  entire design and received the most dedicated section (Section 10) —
  every one of the ten guardrail dimensions this task asked for
  (hallucination prevention, missing/conflicting evidence, unknown
  answers, recommendations, cause vs. observation, historical vs.
  current, confidence wording, evidence boundaries, unsupported
  questions) has an explicit, concrete rule, not a general aspiration.
- **Future migration problems:** keeping the Prompt Builder's output a
  plain, provider-agnostic `{system, user}` dict (Section 5) avoids
  near-term lock-in to one SDK's message object type; multi-provider
  support is explicitly recorded as an open question (Section 15)
  rather than silently assumed resolved in either direction.

No revision to this design was needed as a result of this review — the
concerns this task asked to check for were already addressed by
decisions made while writing Sections 10–14, rather than discovered
afterward and patched in.
