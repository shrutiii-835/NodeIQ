# LEARNING_NOTES.md — NodeIQ, Explained for a Beginner

This file is written for you, the developer, as you learn Linux systems
programming, observability, and CLI development through building NodeIQ.
Every time a new concept shows up in the project, it gets explained here in
plain language — what it is, why it exists, and why NodeIQ uses it.

This file grows over time. New sessions add new sections; nothing here is
meant to be deleted, only added to.

---

## Core Concepts (Project Foundations)

### What is observability?

"Observability" is the general idea of being able to answer questions about
a running system — *is it healthy, what is it doing, why did something go
wrong* — by looking at the data it produces (logs, metrics, process state,
configuration), rather than by guessing or by adding print statements after
the fact.

In big companies, observability usually means dashboards, metrics
databases, and log aggregation tools. NodeIQ is a small, single-server take
on the same idea: instead of a dashboard, you ask a question in plain
English, and instead of a metrics database, NodeIQ reads the same raw
system data an experienced sysadmin would check by hand (`systemctl`,
`journalctl`, `/proc`, etc.).

### Why build NodeIQ?

Diagnosing "what's wrong with this server" today means running many
different commands and mentally combining their output — you have to
already know *which* commands to run and *how* to interpret them. NodeIQ's
goal is to automate the "gather the evidence" step and add a natural
language layer on top, so you can ask a plain question and get an answer
grounded in real data from that specific machine.

Building it yourself (rather than just using an existing tool) is also the
point — it's a structured way to learn Linux internals (`/proc`, systemd,
networking tools), Python system programming (running subprocesses safely,
handling failures), and CLI design, one deliberate phase at a time.

### Why are we documenting first?

Before any code exists, NodeIQ has a full set of documentation
(`README.md`, `CONTEXT.md`, `PROJECT_RULES.md`, and now `CHECKLIST.md`,
`DECISIONS.md`, `ROADMAP.md`, and this file). That might feel backwards if
you're used to "just start coding" — but this project spans many separate
development sessions, possibly weeks or months apart. Documentation-first
means:

- Nobody (including future-you, or a future AI assistant) has to
  re-figure-out *why* a decision was made — it's already written down.
- Rules about style, error handling, and architecture are agreed on before
  code exists, so the code doesn't drift into inconsistency over time.
- You can review and correct the architecture cheaply now — before it's
  encoded in hundreds of lines of code that would be expensive to change.

### What is an ADR?

ADR stands for **Architecture Decision Record**. It's a short, structured
note capturing *one* decision: what was decided, what else was considered,
why the chosen option won, what you gave up by not choosing the
alternatives (trade-offs), and what it means for the future.

NodeIQ keeps its ADRs in [DECISIONS.md](DECISIONS.md). The value of an ADR
isn't really for the moment you write it — it's for six months from now,
when you've forgotten *why* you picked `argparse` over `click`, and instead
of having to re-derive the reasoning, you just read the ADR.

A good rule of thumb: if you catch yourself thinking "wait, why did we do
it this way?" — that question should already be answered in `DECISIONS.md`.
If it isn't, that's a sign we should have written an ADR for it.

### Why frequent Git commits?

Git is a version control system — it keeps a history of every change made
to the project, as a series of "commits," each with a message describing
what changed and why. Committing frequently (after each small, verified,
complete task) instead of rarely (one giant commit at the end of a long
session) has a few concrete benefits:

- If something breaks, you can look at recent commits to see exactly what
  changed and undo just that change, instead of untangling a huge diff.
- Each commit becomes a readable "checkpoint" of the project's history —
  useful given this project is built across many sessions.
- It pairs naturally with `LOGS.md`: each significant commit should have a
  matching diary entry explaining the reasoning, so the git history and the
  development diary tell the same story from two angles (one terse, one
  detailed).

### What is snapshot-first architecture?

This is NodeIQ's central architectural idea, and it's worth understanding
deeply (see `CONTEXT.md` Section 3 for the full philosophical treatment —
this is the beginner-friendly version).

Instead of letting the AI (the LLM) directly run commands on your server
whenever you ask it a question, NodeIQ splits the work into two separate
steps:

1. **`scan`** — a plain Python program (no AI involved) runs a fixed set of
   safe, read-only Linux commands, collects their output, and saves it all
   into one JSON file called a **snapshot**. Think of a snapshot like a
   photograph of the system's state at that exact moment.
2. **`ask`** — later, when you ask a question, the LLM is given *only* that
   JSON snapshot (never live access to your server) and answers using
   *only* what's in it.

Why not just let the AI run commands directly? A few reasons:

- **Safety** — an AI with live shell access to a real server is risky. It
  could run something slow, something destructive, or something it
  misunderstood the consequences of. A snapshot is just a file — it can't
  do anything.
- **Predictability** — because the evidence-gathering step is plain,
  deterministic Python code (not an AI), you always know exactly what
  commands ran and what data was collected. Bugs in "did we collect the
  right data" are separate from bugs in "did the AI reason about it
  correctly."
- **Honesty** — the LLM is instructed to answer only from the snapshot, and
  to say so if evidence is missing, rather than guessing based on "what
  servers usually do." Since you can read the exact same snapshot yourself,
  you can always double-check its answer against the real evidence.

This is why the project's very first architectural rule (see `CONTEXT.md`)
is: **collection and interpretation are two separate layers, and the
interpretation layer never gets to skip the collection layer.**

---

## Concepts Introduced in This Session

### What is Multipass, and why a VM instead of just your laptop?

[Multipass](https://multipass.run) is a tool that quickly creates and
manages lightweight Ubuntu virtual machines (VMs) on your computer. A VM is
a full, isolated "fake computer" running inside your real one — it has its
own filesystem, its own processes, its own network stack.

NodeIQ needs to run real Linux commands (`systemctl`, `journalctl`,
reading `/proc`, etc.) against a real Linux system. If your everyday laptop
isn't running Linux natively, a Multipass VM gives you a genuine Ubuntu
environment to develop and test against, without needing a separate
physical machine. See `DECISIONS.md` ADR-002 for the full reasoning,
including why a VM was chosen over a Docker container (containers often
don't have a full, real `systemd`, which NodeIQ specifically needs to
inspect).

### What is an "ADR supersession," and why did the Git rule change?

Sometimes a project's own past decision needs to change — that's normal.
When it does, instead of quietly editing the old decision away, we write a
**new** ADR that explicitly says it replaces the old one, and note that
relationship in both entries. That way the history stays honest: you can
see not just "here's the current rule" but "here's what we used to do, and
here's exactly why we changed it."

This session is a concrete example: Phase 1 originally said "Claude never
commits." `DECISIONS.md` ADR-011 records the project owner's explicit
decision to change that, and why (frequent, small, verified commits create
better checkpoints across long-running, multi-session work). The *old*
rule wasn't wrong when it was made — circumstances (and the owner's
preference) changed, and now that change itself is on the record.

### What is a `.gitkeep` file?

Git only tracks files, not empty folders — so an empty directory like
`docs/` or `tests/` would simply vanish from version control if you tried
to commit it as-is. A `.gitkeep` is just an empty, conventionally-named
file placed inside an otherwise-empty folder so Git has *something* to
track, which keeps the folder itself present in the repository. It has no
special meaning to Git — it's a community convention, not a built-in
feature.

---

## Concepts Introduced in Phase 2 (Data Model Design)

### What is a data model?

A **data model** is a plan for how information is organized and related,
before you write any code that uses it. Think of it like a blueprint for a
house: the blueprint isn't the house, but every wall, door, and pipe in the
real house follows what the blueprint decided. NodeIQ's data model is the
plan for what a "snapshot" of a Linux server looks like — what categories
of information it contains (`system`, `disk`, `services`, ...), and what
each category's fields mean — before any collector actually goes and reads
real data from a real machine.

Designing this first means every future collector, report generator, and
LLM prompt is building against the same blueprint, instead of everyone
inventing their own shape for "disk information" and having them all
disagree.

### What is a schema?

A **schema** is a precise, written-down description of a data model's
shape: which fields exist, what type each one is (string, number, list of
objects, ...), and which fields are required versus optional. If the data
model is the blueprint's overall floor plan, the schema is the detailed
spec sheet — "this room is 4m × 3m, this door is 90cm wide, this outlet is
required, that shelf is optional."

`docs/snapshot_schema.md` is NodeIQ's schema: for every section of a
snapshot, it says exactly what fields exist, what they mean, and whether
they must always be present. This means a future collector doesn't have to
guess what shape to produce, and a future report or LLM prompt doesn't have
to guess what shape to expect.

### Why does design come before implementation?

It's tempting to just start writing a collector and figure out the JSON
shape as you go. NodeIQ deliberately does the opposite — schema first,
code later — for a concrete reason: **a design mistake found on paper costs
almost nothing to fix; the same mistake found after eleven collectors and
a report generator are already built costs a lot more.**

For example, this phase discovered that CONTEXT.md's informal list of
"CPU" and "Memory" as two separate collectors didn't cleanly map onto the
JSON schema's single `cpu_memory` key. Catching that mismatch while writing
a markdown document took a few extra paragraphs of explanation. Catching it
*after* writing two separate Python collector files that both tried to
write to the same JSON key would have meant going back and refactoring
working code. Designing first turns expensive code changes into cheap
document edits.

### Why is JSON commonly used for system tools?

Linux system tools that need to exchange structured information with other
programs (rather than just printing something for a human to read)
overwhelmingly reach for JSON — many modern Linux commands even support a
`--json` output flag for exactly this reason. JSON won out over
alternatives like XML or custom text formats because it's simple (only a
handful of value types), has a JSON parser/writer built into practically
every programming language including Python's standard library, and stays
readable in a plain text editor even without special tooling. NodeIQ uses
it for the same reasons: it needs to hand structured data from Python code
(collectors) to another consumer (a report generator, or an LLM), and JSON
is the simplest format both ends already know how to speak.

### What is a "contract" between software components?

A **contract**, in software design, is an agreement about what one piece of
code will provide and what another piece of code can rely on — without
either one needing to know *how* the other actually works internally.

NodeIQ's snapshot schema is exactly this kind of contract: a collector's
side of the contract is "I will produce a `disk` object shaped exactly like
`docs/snapshot_schema.md` Section 6 describes." The report generator and
the LLM's side of the contract is "I can safely assume any snapshot has a
`disk` object shaped that way, and I don't need to know that it internally
ran `df -i` under the hood to get it." As long as both sides honor the
contract, the collector's internals can change freely (a faster parsing
method, a different command) without breaking anything that reads the
snapshot — which is exactly the kind of maintainability this project is
optimizing for.
