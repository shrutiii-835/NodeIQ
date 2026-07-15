# Summary Engine Design — NodeIQ

**Status:** Design only (Phase 4.1A). No code exists yet —
`src/nodeiq/summary.py` (or wherever implementation ultimately lands, see
"Module and Naming Proposal" below) is not implemented, and nothing in
`nodeiq.core.coordinator` or `nodeiq.core.snapshot` changes as a result
of this document. This exists so implementation (Phase 4.1B, presumably)
starts from a reviewed plan, per this project's established "design
before implementation" convention (see `LEARNING_NOTES.md`, "Why does
design come before implementation?", and the precedent set by Phase
3.5A's process collector design before Phase 3.5B's implementation).

Read this alongside [architecture.md](architecture.md) (the execution
layers this new layer sits between), [snapshot_schema.md](snapshot_schema.md)
(the shape of what the Summary Engine consumes), and
[snapshot_persistence.md](snapshot_persistence.md) (how a snapshot gets
from a scan to something this engine can load and summarize later).

---

## 1. Purpose and Scope

The data collection layer (all 9 collectors, `run_scan()`, snapshot
persistence) is complete. Every future consumer of a snapshot — a CLI
`report` command, an OpenAI prompt for `ask`, a future web UI, a future
export format — currently faces the same raw, ~10-section snapshot and
would have to independently decide what matters, what's noise, and how
to phrase it. Left unaddressed, that logic would get duplicated (and
would drift out of sync) across every consumer.

The **Summary Engine** is the single, shared layer that turns a raw
snapshot into one concise, structured **Summary** — computed once,
consumed by every downstream presentation format. This document designs
that layer. It does **not** implement it, and it does not implement
`report`, `ask`, or any CLI command — those remain Phase 4 (report),
Phase 5 (CLI), and Phase 6 (LLM integration) as already ordered in
`CONTEXT.md` Section 8.

---

## 2. Where This Fits

```
Layer 1 (existing)              New layer (this design)        Layer 2 / presentation (future)
─────────────────────           ──────────────────────          ────────────────────────────────

run_scan()
   │
   ▼
snapshot (dict)  ──────────►  summarize_snapshot(snapshot)
   │                                    │
   │ save_snapshot()                    ▼
   ▼                              Summary (dict)
snapshots/*.json                        │
   │                     ┌──────────────┼──────────────┬─────────────────┐
   │ load_snapshot()      ▼              ▼               ▼                 ▼
   └───────────────►  CLI report    OpenAI prompt    Future web UI    Future exports
                      formatter     builder          serializer       (CSV, etc.)
                      (Phase 4/5)   (Phase 6)         (unscheduled)    (unscheduled)
```

The Summary Engine reads a snapshot (freshly produced by `run_scan()`,
or reloaded later via `load_snapshot()`/`load_latest_snapshot()` — see
`docs/snapshot_persistence.md`) and produces one Summary. Every
downstream consumer reads that same Summary instead of independently
re-deriving what matters from the raw snapshot. This mirrors a pattern
already proven twice in this project: collectors don't duplicate
`nodeiq.core.runner`'s subprocess-safety logic, and the coordinator
doesn't duplicate any one collector's parsing logic. The Summary Engine
applies the identical "shared logic lives in exactly one place" principle
one layer higher up the pipeline.

Critically, the Summary Engine sits **beside**, not **inside**, the
existing pipeline: `nodeiq.core.coordinator` and `nodeiq.core.snapshot`
gain no new dependency on it, and it depends on neither of them beyond
reading the plain dict shape they already produce. A snapshot remains a
complete, valid, independently useful artifact with or without a Summary
ever being computed from it.

---

## 3. Design Question 1 — What Should the Input Be?

**A single, plain snapshot dict** — exactly the shape `run_scan()`
returns, and exactly the shape `load_snapshot()`/`load_latest_snapshot()`
return (see `docs/snapshot_persistence.md`). No new input type.

This matters for one concrete reason: it makes summarization
**reproducible from storage**. Because `summarize_snapshot()` takes the
same dict shape whether it just came from a live scan or was loaded from
a `.json` file written days earlier, generating a Summary is always:

```python
from nodeiq.core.snapshot import load_latest_snapshot
from nodeiq.summary import summarize_snapshot  # proposed location

summary = summarize_snapshot(load_latest_snapshot())
```

— regardless of whether the snapshot is one second old or one month old.
This directly extends the "Snapshot Lifecycle" diagram already
established in `docs/snapshot_persistence.md`.

A secondary consequence: the top-level entry point takes the **whole**
snapshot, but internally it's organized per-section, and each per-section
summarizer function takes only that one section's own data — never the
whole snapshot, never another section's data. This is the same
independence rule `docs/collector_guidelines.md` already enforces for
collectors ("must not call, import, or depend on another collector"),
applied to summarizers instead: a `disk` summarizer has no way to see
`cpu_memory`'s data, by construction, not by convention alone.

---

## 4. Design Question 2 — What Should the Output Look Like?

A **Summary**: one small object per snapshot, containing scan-level
bookkeeping plus one **SectionSummary** per snapshot section. Each
SectionSummary reports whether that section's data was available, a
short deterministic headline, the specific facts worth surfacing, any
concerns (still just facts — see Section 10), and that section's own
collection errors, if any.

See Section 11 for a concrete, illustrative shape.

---

## 5. Design Question 3 — Plain Dict, Dataclass, or Something Else?

**Recommendation: plain dicts**, matching the convention every collector
and the snapshot itself already use — **not** the `CollectorResult`
dataclass pattern (`DECISIONS.md` ADR-014), despite the superficial
similarity ("the output of one unit of work").

The reason this is a *different* decision, not an inconsistent one:
`CollectorResult` exists to be passed between exactly two parties inside
one process (a collector and the coordinator) and is never itself
serialized — only its `.data` field ends up in the snapshot dict. A
Summary's entire purpose is the opposite: it exists specifically **to be
serialized** — embedded in an OpenAI prompt as JSON, converted to text
for a CLI report, returned as a JSON API response for a future web UI.
A dataclass would force every one of those consumers to call
`dataclasses.asdict()` (or equivalent) before doing the one thing they
actually want to do with it, for no compensating benefit — the "named
fields over positional tuple" argument that justified `CollectorResult`
over a tuple doesn't apply here, since a dict already has named,
self-documenting keys.

This recommendation deliberately does **not** resolve the still-open
Phase 2 checklist item, "decide on schema representation in code
(dataclasses vs. TypedDict)" (`CHECKLIST.md`, unchecked since Phase 2) —
that question is about how *snapshot sections themselves* are
represented in code, a different (and still genuinely unresolved)
question from how a *derived* Summary object is represented. Both could
independently land on "plain dict" or "TypedDict" without one answer
constraining the other; this document only commits to an answer for the
Summary shape, and explicitly leaves the older question open, rather
than silently deciding it as a side effect.

---

## 6. Design Question 4 — How Should Sections Be Represented?

**One summarizer function per snapshot section, orchestrated by one
engine function** — directly mirroring the collector architecture
already validated across 9 real collectors:

| Collector architecture | Summary Engine architecture (proposed) |
|---|---|
| One module per section (`system.py`, `disk.py`, ...) | One function per section (`_summarize_system`, `_summarize_disk`, ...) |
| `collect(context: CollectorContext) -> CollectorResult` | `_summarize_<section>(data, errors) -> dict` (a SectionSummary) |
| `_REGISTERED_COLLECTORS` (a plain list in `coordinator.py`) | `_REGISTERED_SUMMARIZERS` (a plain list in the engine module) |
| `run_scan()` orchestrates: call each, aggregate, never let one crash the scan | `summarize_snapshot()` orchestrates: call each, aggregate, never let one crash the summary |
| Collectors never call each other | Summarizers never call each other |
| Coordinator builds `metadata` itself (a scan-level fact, not any one collector's job) | Engine builds Summary-level bookkeeping itself (`generated_at`, `snapshot_timestamp`) — not any one summarizer's job |

This isn't a new architectural idea being introduced — it's the same one
applied a second time, which is exactly why it's a strong candidate: it
has already been validated (structurally and via three full rounds of
real implementation across 9 collectors) rather than being a fresh,
unproven design.

---

## 7. Design Question 5 — What Belongs in Summaries?

A concrete observation from reviewing all 9 collectors' actual output,
not a general assumption: **collectors have mostly already done the
"reduce noise" work.** `processes.py` already returns only
`top_by_memory` (10 entries), not all ~90+ running processes. `disk.py`
already returns `highest_disk_usage_percent`, not a walk of every
filesystem for the caller to reduce themselves. `logs.py` already caps
at 100 entries via `_MAX_ENTRIES`. The Summary Engine's job for most
sections is therefore **less** "compress a firehose" and **more**:

1. Select the specific fields from each section that matter for a quick
   read (not necessarily every field the collector returned).
2. Add a small amount of deterministic, templated framing (a headline
   string — see Section 10) so every consumer isn't independently
   reinventing the same "N services failed" phrasing.
3. Surface whether the section's data is trustworthy at all — see
   Section 9.

What belongs: the counts, percentages, and top-N lists collectors
already computed; a deterministic headline built from those facts;
whether the section succeeded, partially succeeded, or failed entirely.

---

## 8. Design Question 6 — What Stays in the Raw Snapshot Only?

Different sections have genuinely different "noise profiles" — this is
an observation from the real data, not a rule invented in the abstract:

- **Naturally small/already-scalar sections** (`system`, `cpu_memory`,
  the disk section's two `highest_*` fields) need almost no further
  reduction — the summary for these is close to a pass-through plus a
  headline.
- **Naturally unbounded sections** (`processes.top_by_memory`,
  `scheduled_jobs.cron_jobs`, `logs.recent_entries`,
  `disk.filesystems` on a system with many mounts) are where a Summary
  earns its keep — e.g. a Summary might keep `cron_job_count` and a
  small number of notable/flagged entries, while the *full* list stays
  something only the raw snapshot carries.

The general rule: **counts and highlights belong in the Summary; full,
unbounded detail lists stay in the raw snapshot**, retrievable via
`load_snapshot()`/`load_latest_snapshot()` whenever a consumer's
question genuinely needs it (e.g. "list every cron job" is a question
the *raw* snapshot answers better than any summary could, by design —
see the open question in Section 17 about how `ask` should choose
between the two).

---

## 9. Availability and Errors Must Survive Summarization

`CONTEXT.md` Section 4 (Safety Philosophy) is unambiguous: "If evidence
is missing or a collector failed, that fact must be visible... so the
LLM (and the user) knows the answer may be incomplete." A Summary that
silently dropped a failed section — rather than reporting "this section
couldn't be determined" — would violate that guarantee at exactly the
layer meant to make evidence *more* accessible, not less honest.

Every SectionSummary therefore carries:

- `available: bool` — `False` if the collector crashed (`snapshot[section]
  is None`) or the section is simply absent from an older snapshot.
- `errors: list[dict]` — that section's own `collection_errors` entries,
  copied through unchanged (empty list if none).

And the Summary as a whole carries `collection_errors` echoed from the
snapshot's own top-level field, so a consumer that only cares "was
*anything* wrong" doesn't need to walk every section.

---

## 10. Report Philosophy, Applied Concretely

The task's philosophy — reduce noise, preserve evidence, remain
deterministic, never invent conclusions — needs concrete rules to
actually hold up in code, not just be a heading. Three specific
tensions, resolved explicitly:

### Is a "headline" string interpretation?

`docs/collector_guidelines.md` forbids collectors from doing
"presentation work" — phrasing belongs to `report`/`ask`. Does a
Summary Engine headline (e.g. `"3 services failed"`) cross that same
line?

**Resolution:** there's a real difference between *mechanical*
templating of facts and *interpretive* phrasing. `f"{failed_count}
services failed"` is a deterministic function of a number already in
evidence — no judgment is involved, and every consumer would otherwise
have to write the identical formatting code themselves (a real
duplication risk, per Design Question 7). `"3 services failed — you
should investigate recent deployments"` requires causal judgment this
layer must never make. The rule: **headlines may state a fact using a
fixed, neutral template; they may never explain a cause or suggest an
action.** No adjectives implying severity ("critical", "concerning") —
only feature-flag facts (Section 10's next point).

### Are threshold-based "concerns" a diagnosis?

Flagging `disk.usage_percent > 90` as worth surfacing requires *some*
judgment about what counts as noteworthy — is that already "diagnosis"?

**Resolution (a defensible line, not a certainty — see Section 17):** a
concern is acceptable when it (a) is triggered by a **fixed, documented,
named constant** (the same convention `logs.py`'s `_MAX_ENTRIES` already
established), not an inferred or dynamic judgment, and (b) states only
the fact plus the threshold — never a cause or a fix. `"filesystem / at
92% usage (threshold: 90%)"` is a transparent, reproducible statement
anyone can verify against the same fixed number. `"disk almost full,
probably logs — clear /var/log"` is a diagnosis and a recommendation,
both forbidden. Whether fixed-threshold flagging belongs in this engine
at all, versus being deferred entirely to Phase 6, is recorded as an
open question (Section 17) rather than asserted as settled.

### Is `generated_at` a determinism violation?

The Summary Engine's own bookkeeping (when was this Summary computed)
is, definitionally, not a pure function of the snapshot — two calls to
`summarize_snapshot()` on the identical snapshot, seconds apart, would
produce two different `generated_at` values.

**Resolution:** "deterministic" describes the summarization *logic* —
same snapshot facts in, same section headlines/facts/concerns out —
not incidental bookkeeping about the summarization *process* itself.
This is exactly the same distinction already accepted for
`metadata.scan_duration_ms` in the coordinator's own snapshot (Phase
3.4): nobody considers that field a violation of collector determinism,
because collector determinism is about the *facts collected*, not the
scan's own timing. The same reasoning is applied here, one layer up.

---

## 11. Proposed Summary Object (Illustrative)

Field names and full section detail are left to the implementation
phase — this shows the *shape*, grounded in the real fields the 9
collectors actually produce today:

```json
{
  "generated_at": "2026-07-15T09:00:00.000000+00:00",
  "snapshot_timestamp": "2026-07-15T08:35:17.525799+00:00",
  "hostname": "main-cattle",
  "sections": {
    "system": {
      "available": true,
      "headline": "Ubuntu 24.04.4 LTS, kernel 6.8.0-134-generic, up 5d 3h",
      "facts": {
        "operating_system": "Ubuntu 24.04.4 LTS",
        "kernel_version": "6.8.0-134-generic",
        "architecture": "aarch64",
        "uptime_seconds": 446417.0
      },
      "concerns": [],
      "errors": []
    },
    "cpu_memory": {
      "available": true,
      "headline": "Memory 26.6% used, load average 0.01",
      "facts": {
        "memory_usage_percent": 26.62,
        "swap_usage_percent": 0.0,
        "load_average_1m": 0.01
      },
      "concerns": [],
      "errors": []
    },
    "processes": {
      "available": true,
      "headline": "91 processes, 0 zombies, 0 blocked",
      "facts": {
        "process_count": 91,
        "zombie_count": 0,
        "blocked_process_count": 0,
        "top_by_memory": [
          {"process_name": "multipathd", "memory_rss_bytes": 27107328}
        ]
      },
      "concerns": [],
      "errors": []
    },
    "disk": {
      "available": true,
      "headline": "Fullest filesystem at 60.0% (/dev/sda1 on /)",
      "facts": {"highest_disk_usage_percent": 60.0, "highest_inode_usage_percent": 24.0},
      "concerns": [],
      "errors": []
    },
    "services": {
      "available": true,
      "headline": "54 running, 0 failed, 45 enabled",
      "facts": {"running_services_count": 54, "failed_services_count": 0},
      "concerns": [],
      "errors": []
    }
  },
  "collection_errors": {}
}
```

(`scheduled_jobs`, `permissions`, `network`, and `logs` omitted here only
for length — each follows the identical `{available, headline, facts,
concerns, errors}` shape.)

---

## 12. Section Lifecycle

Directly parallel to `docs/collector_guidelines.md`'s "Standard
Lifecycle":

```
summarize_snapshot(snapshot)
  →  for each registered section name in _REGISTERED_SUMMARIZERS:
        section_data   = snapshot.get(section_name)          # None if collector crashed
        section_errors = snapshot["collection_errors"].get(section_name, [])
        →  if section_data is None:
              record {available: False, headline: "not available", facts: {}, concerns: [], errors: section_errors}
        →  else:
              try:
                  section_summary = _summarize_<section>(section_data, section_errors)
              except Exception:
                  # last-resort safety net, mirroring run_scan()'s own crash handling —
                  # one summarizer failing must never crash the whole Summary
                  record {available: False, headline: "summarization failed", ...}
  →  assemble generated_at, snapshot_timestamp, hostname
  →  return the Summary dict
```

Every `_summarize_<section>` function is a **pure function**: given the
same section data and errors, it always returns the same SectionSummary
— no I/O, no subprocess calls, no dependency on any other section. This
is what makes each one trivially testable with a literal sample dict, no
mocking required, exactly like every collector's `_parse_*` helpers
already are.

---

## 13. Module and Naming Proposal

**Proposed for v1: one new module, `src/nodeiq/summary.py`**, containing
every `_summarize_<section>` function as a private helper plus one
public `summarize_snapshot()` — not a new `nodeiq/summary/` package with
one file per section.

This placement is deliberate: `nodeiq.core` holds shared execution
infrastructure collectors and the coordinator depend on
(`runner`, `result`, `exceptions`, `collector`, `snapshot`, `errors`,
`identity`) — the Summary Engine isn't that; it's not infrastructure
other modules build on, it's a consumer of the snapshot shape.
`nodeiq.collectors` holds one module per *raw-fact-gathering* concern —
the Summary Engine isn't that either; it transforms already-collected
data, it doesn't gather any of its own. It's a new, third kind of
concern, so it gets a new top-level module rather than being wedged into
either existing package.

A single file (not a package) for v1 mirrors `cpu_memory.py`'s own
precedent of handling more than one data source in one module when doing
so doesn't yet cause a real problem — 9 section summarizers, several of
which may be only a few lines long (e.g. `system`'s summarizer is close
to a pass-through), don't yet justify 9 separate files. If any individual
summarizer grows complex enough to warrant its own file, splitting
`summary.py` into a `summary/` package (one file per section, exactly
mirroring `collectors/`) is a mechanical, low-risk refactor to do
*then*, from evidence — not a speculative structure to build now.

---

## 14. Trade-offs

- **Plain dict output (chosen) vs. dataclass:** gains simplicity and
  direct JSON-serializability for every known consumer; loses
  compile-time/IDE-checked field access (a typo'd section-name key
  fails silently at lookup, not at type-check time). This is an accepted,
  already-standing trade-off in this codebase — every collector's own
  `.data` dict has the identical property, and it hasn't caused real
  problems across 9 collectors and hundreds of tests.
- **One module for v1 (chosen) vs. a `summary/` package:** gains
  simplicity now; loses some of the "one file, one concern" clarity
  collectors enjoy individually. Mitigated by keeping each
  `_summarize_<section>` function short and independently testable
  regardless of which file it lives in — the *functional* separation
  (independent, pure, one per section) is preserved even without
  separate files.
- **Templated headlines (chosen) vs. no headlines at all:** gains
  cross-consumer reuse (CLI, prompt, and web UI don't each reinvent "N
  services failed" phrasing) and a quick-glance summary that's still
  useful without any downstream renderer at all; loses a small amount of
  the "purely structured data, zero prose" purity a stricter design
  might prefer, and introduces the ongoing discipline requirement
  (Section 10) that headlines never drift from "mechanical fact" into
  "interpretation." This is the single trade-off in this design most
  worth revisiting if it proves hard to hold the line in practice — see
  Section 17.
- **Fixed-threshold "concerns" (tentatively proposed) vs. no
  threshold-flagging in this layer at all:** gains earlier, more useful
  visibility into what's actually worth a human's attention across all
  consumers at once; loses some of the clean "this layer only ever
  passes facts through, unchanged" simplicity, and requires ongoing
  discipline to keep thresholds fixed/transparent rather than
  creeping toward inferred judgment. Recorded as the least-settled
  decision in this design (see Section 17).

---

## 15. Future Extensibility

- **Adding a new snapshot section** (a 10th collector, someday): add one
  `_summarize_<new_section>` function and one entry to
  `_REGISTERED_SUMMARIZERS` — the same "one line to add a collector"
  ergonomics `docs/coordinator.md` already established, applied one
  layer up.
- **Insulating consumers from raw schema churn.** Every known and future
  divergence between what a collector *actually* returns and what
  `docs/snapshot_schema.md` originally specified (documented extensively
  across `docs/system_collector.md`, `docs/cpu_memory_collector.md`,
  `docs/disk_collector.md`, and others) is a real, ongoing source of
  churn at the raw-snapshot level. A stable Summary shape means a future
  raw-field rename or restructuring only requires updating the one
  affected `_summarize_<section>` function — every CLI formatter, prompt
  builder, and future web UI serializer keeps working unchanged, because
  none of them ever look at raw collector fields directly. This is
  arguably the single biggest structural benefit of introducing this
  layer at all, beyond the immediate noise-reduction goal.
- **Summary caching** (not proposed now): summarization is a pure,
  cheap, in-memory transformation of already-small data — there's no
  current evidence this is expensive enough to warrant caching a
  computed Summary alongside its snapshot. If that ever changes,
  `nodeiq.core.snapshot`'s existing persistence pattern (deterministic
  filenames, `snapshots/`) could be extended by analogy — but only from
  a real, observed need, not speculatively now.
- **Severity levels / scoring** (not proposed now): assigning an
  "info/warning/critical" score to a concern would require a judgment
  call this design deliberately avoids (Section 10). If a future phase
  decides this is worth the risk, it should be its own explicit
  decision (and likely its own ADR), not something that creeps in
  silently through this design.

---

## 16. Relationship to the Still-Open Schema-Representation Decision

`CHECKLIST.md`'s Phase 2 section has carried one unchecked item since
this project's second phase: "Decide on schema representation in code
(dataclasses vs. TypedDict)." This design does not resolve that
question — it answers a narrower, adjacent one (what shape should a
*derived Summary* take — see Section 5) without taking a position on
whether *snapshot sections themselves* should eventually move from plain
dicts to `TypedDict` or `dataclasses`. Whatever that older decision
ends up being, `summarize_snapshot()`'s input contract (Section 3) is
unaffected: it consumes whatever shape a snapshot dict already has,
however that shape ends up being declared in code.

---

## 17. Open Questions

Recorded explicitly, per this project's practice of writing down a
genuine unresolved tension rather than guessing at a confident-sounding
answer:

1. **Should `ask` (Phase 6) consume only the Summary, only the raw
   snapshot, or both depending on the question?** A narrow question
   ("list every cron job") is plausibly better answered from the raw
   snapshot than a necessarily-trimmed Summary; a broad question
   ("how's this server doing?") is plausibly better served by the
   Summary alone. This is fundamentally a Phase 6 (LLM integration)
   design question, not something this phase should resolve by
   assumption.
2. **Are fixed-threshold "concerns" (Section 10) appropriately in scope
   for this layer at all**, or should *all* flagging/highlighting be
   deferred to Phase 6, with this layer only ever passing facts through
   unchanged? This document tentatively proposes yes, with strict
   rules, but flags it as the least-settled call in this design.
3. **Should threshold constants be user-configurable** (e.g. "flag disk
   usage above N%") or fixed constants in code, the way `logs.py`'s
   `_MAX_ENTRIES` is? Configurability implies a config system that
   doesn't exist yet in NodeIQ v1 — likely a "no, not yet" by default,
   but not decided here.
4. **Exact per-section field selection** (precisely which facts, beyond
   the illustrative examples in Section 11, belong in each section's
   `facts`) is deliberately left to the implementation phase, the same
   way Phase 3.5A's process collector design left exact schema fields
   to Phase 3.5B — this document fixes the *shape and rules*, not every
   field.
5. **Should a Summary be persisted alongside its snapshot**, or always
   regenerated on demand? Section 15 leans "regenerate, don't persist,"
   but this hasn't been tested against a real CLI/prompt workflow yet.

---

## 18. Quality Review

Applying the same three-question test used in Phase 3.7's refactoring
sprint (`docs/collector_guidelines.md`, "Quality Check"):

- **Does each proposed structure simplify the code, or add ceremony?**
  The summarizer-per-section pattern reuses an already-proven structure
  rather than inventing a new one — simplifies by precedent. The plain
  dict output avoids a mandatory serialization step every consumer would
  otherwise repeat — simplifies. A `SummaryContext` object (mirroring
  `CollectorContext`) was considered and **rejected**: unlike
  `CollectorContext`, which solved two concrete, current problems
  (shared timeout, shared scan-start time — ADR-014), no shared
  parameter every summarizer needs has been identified yet. Inventing
  one now, for symmetry alone, would be exactly the "speculative
  abstraction" this phase's Quality Review warns against — so it's left
  out until a real need appears.
- **Is each choice based on real evidence, or a guess?** The "collectors
  already reduce noise" observation (Section 7) comes from reviewing
  all 9 collectors' actual current output, not an assumption. The
  module-placement decision (Section 13) comes from the real, existing
  boundary between `nodeiq.core` and `nodeiq.collectors`, not an
  invented third category. Where evidence doesn't yet exist (fixed
  thresholds' exact values, whether `ask` needs raw-snapshot fallback),
  Section 17 records that honestly instead of asserting a confident
  guess.
- **Would this decision still make sense with far less at stake** (a
  smaller version of this problem)? The one-module-not-a-package choice
  (Section 13) is explicitly framed this way: with only 9 (mostly small)
  sections, one file is the right amount of structure; a whole package
  would be over-built for the actual current size of the problem, and
  splitting later remains cheap and low-risk if that changes.

No abstraction proposed in this document failed this review; the one
genuinely speculative idea considered (a `SummaryContext` object) was
identified and explicitly rejected rather than included "just in case."
