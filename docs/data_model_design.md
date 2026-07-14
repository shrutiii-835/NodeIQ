# Data Model Design Philosophy — NodeIQ

This document explains the *why* behind the schema defined in
[snapshot_schema.md](snapshot_schema.md). Read that file for the exact
field-level shape of every section; read this file for the reasoning that
produced it.

This is a design document, not an implementation record — no Python code,
collectors, or CLI logic exist as a result of this document. See
`CHECKLIST.md` Phase 2 and `LOGS.md` for what was actually built.

---

## Why JSON Was Chosen

JSON is the internal contract between NodeIQ's two layers (collection and
interpretation — see `CONTEXT.md` Section 2). It was chosen, rather than
plain text, CSV, or a custom format, because it is:

- **Structured but simple.** JSON has exactly the amount of structure this
  project needs — objects, arrays, strings, numbers, booleans, null — and
  nothing more exotic (no schemas-within-schemas, no binary encoding).
- **Native to both ends of the pipeline.** Python's standard library reads
  and writes JSON with no extra dependency (`json.dumps`/`json.loads`), and
  every LLM API in common use (including the one chosen in `DECISIONS.md`
  ADR-005) is designed to read and reason about JSON-shaped text directly.
- **Human-readable.** A snapshot can be opened in any text editor and
  understood without tooling — important for a project whose own developer
  is still learning the underlying Linux concepts, and important generally
  for auditability (CONTEXT.md Section 3).
- **Diffable.** Two snapshots can be compared with an ordinary text diff,
  which matters for the future "what changed?" feature already listed in
  `ROADMAP.md`'s long-term milestones.

## Why Snapshot-First Architecture Matters (Recap)

`CONTEXT.md` Section 3 already covers this in full as a hard requirement;
the short version relevant to the data model specifically: because the LLM
never has live access to the system, the JSON snapshot has to be
*complete enough on its own* to answer real operational questions. That
requirement directly shaped this schema — every section exists because it
answers one of the project's example questions ("what service failed?",
"what is consuming memory?", "what ports are open?", "what cron jobs
exist?", "why might disk space be running out?"), not because a Linux
command happened to be available.

## Why Collectors Should Not Depend on Each Other

Each collector is only responsible for producing its own section of the
snapshot, using its own data source, with no reference to any other
collector's output. This has two motivations:

1. **Fault isolation.** `PROJECT_RULES.md` Section 7 requires that one
   broken collector never stops the whole scan. If collectors depended on
   each other, a failure in one would cascade into failures in every
   collector that depended on it, defeating the whole point of independent
   failure handling.
2. **Simplicity of reasoning.** A collector with no dependencies can be
   understood, tested, and debugged in complete isolation — you never have
   to ask "what did some other collector already do to the data by the
   time this one runs?"

The schema supports this by giving every collector its own, separately
owned key to write into (see the next section) rather than, for example, a
single shared structure that multiple collectors would need to
cooperatively build.

## Why Every Section Has a Single Owner

Every top-level key in the snapshot (`system`, `cpu_memory`, `processes`,
`disk`, `services`, `logs`, `network`, `scheduled_jobs`, `permissions`) is
written by exactly one collector module, and no two collectors ever write
into the same key.

This single-ownership rule is what makes "a collector must never crash the
scan" (PROJECT_RULES.md Section 7) actually enforceable: the scan
coordinator can run each collector, catch any exception it raises, and know
*precisely* which section of the snapshot is affected — because exactly
one collector is responsible for it.

Two sections needed a closer look because CONTEXT.md's Section 6 collector
list names more line items than CONTEXT.md's Section 7 has top-level keys:

- **`cpu_memory`** covers what Section 6 lists as two items ("CPU" and
  "Memory"). They're combined under one collector because they're always
  read together in practice and neither needs the other's data — combining
  them costs nothing and avoids introducing a second, functionally
  pointless top-level key.
- **`disk`** covers what Section 6 lists as two items ("Disk" and
  "Inodes"). They're combined because both come from the exact same
  underlying Linux tool (`df`, with and without `-i`) describing the exact
  same set of mounted filesystems — splitting them into two collectors
  would mean running near-identical logic twice for no benefit.

In both cases, the *section* still has exactly one owner; what changed is
just that one owner's internal scope covers two closely related,
non-dependent pieces of data. See `snapshot_schema.md` Section 14 for the
full resolution write-up.

## How This Helps the LLM

The LLM in `ask` (Phase 6) receives the snapshot and nothing else. A
schema that is flat, consistently named, and self-describing helps it in
concrete ways:

- **Predictable field names** (`snake_case`, matching Python conventions —
  see `PROJECT_RULES.md` Section 10) mean the LLM doesn't have to guess at
  meaning or handle multiple naming styles.
- **`collection_errors` as a required read.** Because failures are always
  reported in one predictable place, the LLM can be instructed (in Phase 6
  prompt design) to check `collection_errors` before answering and say "I
  don't have that information" instead of guessing — directly supporting
  the Safety Philosophy in `CONTEXT.md` Section 4.
- **No ambiguous absence.** Because "no data" and "collection failed" are
  never conflated (see `snapshot_schema.md` Section 12), the LLM is never
  put in a position where it has to guess which one an empty field means.

## How This Improves Maintainability

- **Adding a new fact to an existing section** (e.g., a new field in
  `disk`) never requires touching any other collector, since sections are
  independently owned.
- **Adding a whole new category of information** (a new top-level key) is
  additive, not disruptive — old consumers (reports, prompts) that don't
  know about the new key simply don't read it.
- **`metadata.schema_version`** exists specifically so that if a truly
  breaking change is ever needed (a field renamed or removed, not just
  added), every consumer can detect it explicitly rather than silently
  misreading old snapshots.
- **Documentation lives next to the contract.** `snapshot_schema.md` is
  the single place every section's shape, owner, and purpose is recorded,
  so a collector's implementation (Phase 3) has an exact target to match,
  and a report or prompt (Phases 4 and 6) has an exact contract to rely on.

## Future Extensibility Considerations

- New top-level sections can be added in later phases (for example, a
  future `firewall` section, currently folded conceptually into `network`
  and not yet separated out) without breaking this schema — they would
  simply be new mandatory-or-optional keys alongside the existing ones.
- Any field addition to an existing section should be treated as backward
  compatible; anything that would require *removing or renaming* an
  existing field should bump `metadata.schema_version` and be recorded as a
  new ADR in `DECISIONS.md`, per the project's supersession convention.
- The `permissions` section is deliberately the loosest-scoped part of this
  design (see `snapshot_schema.md` Section 11) and is the most likely
  section to grow meaningfully once Phase 3 clarifies exactly what
  "permissions and ownership" should mean operationally.
- Whether these shapes are represented in Python as `dataclasses` or
  `TypedDict` (`PROJECT_RULES.md` Section 4 allows either) is intentionally
  left undecided by this document — that's an implementation decision for
  the next step, not a data-model design decision.
