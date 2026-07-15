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

---

## Concepts Introduced in Phase 3.1 (Core Execution Infrastructure)

### What is `subprocess`?

Python code can't directly run a Linux command like `df` or `systemctl` —
those are separate programs, not Python functions. `subprocess` is
Python's standard-library module for launching another program, waiting
for it to finish (or not, if you choose), and capturing what it printed
and how it exited. `nodeiq.core.runner.run_command` is a thin, careful
wrapper around `subprocess.run` — every future collector will call
`run_command` instead of using `subprocess` directly, so all the safety
decisions below only have to be made once.

### Why is `shell=True` avoided?

`subprocess.run` can be told to run your command through a shell
(`shell=True`) or run the program directly (`shell=False`, the default,
and what NodeIQ always uses). Running through a shell means a *second*
program (`/bin/sh`) reads your command as text and interprets things like
spaces, quotes, `$VARIABLES`, `;`, and `|` before your actual program ever
runs. If any part of that text came from somewhere untrusted (a filename,
a config value, eventually maybe user input), the shell can be tricked
into running something you never intended — this class of bug is called
**shell injection**.

Passing the command as a list (`["df", "-h"]`) instead of a single string
(`"df -h"`) and using `shell=False` skips the shell entirely — Python hands
the program its arguments directly, with no text interpretation step in
between. There's simply no shell present to trick, which is why NodeIQ's
`run_command` requires a list and refuses anything else (see
`InvalidCommandError`).

### stdout vs. stderr

Every well-behaved command line program actually has *two* separate output
channels, not one:

- **stdout** ("standard output") — the program's normal, expected output.
  For `df`, this is the disk usage table.
- **stderr** ("standard error") — error messages and diagnostics, kept
  deliberately separate so a program's real output doesn't get
  contaminated by warnings mixed into the middle of it.

`CommandResult` keeps `stdout` and `stderr` as two separate fields for
exactly this reason: a collector needs to parse `stdout` as data, and
separately check `stderr` for anything that hints something went wrong,
without the two ever being tangled together.

### What is an exit code?

When any program finishes, it reports a single number back to whatever
launched it, called an **exit code** (or "return code"). By long-standing
Unix convention, `0` means "everything succeeded," and any non-zero number
means "something went wrong" (different programs use different non-zero
numbers to mean different specific problems). `CommandResult.returncode`
captures this number, and `CommandResult.succeeded` is really just a
convenience for "was the exit code 0, and did the command run at all,
without timing out."

### What is a timeout, and why does every command need one?

A **timeout** is a maximum amount of time you're willing to let something
run before giving up on it. Some Linux commands can hang indefinitely in
rare situations (a network filesystem that's stopped responding, a
misbehaving service). Without a timeout, NodeIQ's entire `scan` could
freeze forever waiting on one stuck command. `run_command` always applies
a timeout (`DEFAULT_TIMEOUT_SECONDS = 10.0` unless a collector asks for a
different one); if the command is still running when time's up, Python
kills it and `run_command` reports back `timed_out=True` instead of
hanging or crashing.

### What is a "command execution abstraction"?

An **abstraction** just means hiding the messy details of *how* something
works behind a simple interface for *what* it does. `run_command` is an
abstraction over `subprocess`: instead of every collector needing to
remember to set `shell=False`, pass a timeout, catch `TimeoutExpired`,
catch `FileNotFoundError`, and decide what to do with each — a collector
just calls `run_command(["some", "command"])` and gets back one simple,
predictable `CommandResult`, regardless of what actually went right or
wrong underneath. The complexity still exists, but it exists in exactly
one place instead of being repeated (and possibly gotten slightly wrong)
in every collector.

### What is orchestration?

**Orchestration** means coordinating several independent pieces of work so
they combine into one larger result, without those pieces needing to know
about each other. NodeIQ's future scan coordinator
(`nodeiq.core.coordinator`) is an orchestrator: it will call every
collector, one at a time, and combine their independent results into one
snapshot — but no individual collector will know the coordinator exists,
or that any other collector exists. This is the same relationship an
orchestra conductor has to individual musicians: the conductor combines
everyone's playing into one performance, but a violinist doesn't need to
know how to play the trumpet, or even that a trumpet section exists, to
play their own part correctly.

---

## Concepts Introduced in Phase 3.2A (Collector Design Pattern)

### What is separation of concerns?

**Separation of concerns** means giving each piece of code exactly one job,
and drawing a clear line between "this part's job" and "that part's job,"
so a change to one never has to ripple into the other. `docs/
collector_guidelines.md` applies this in a very concrete way: running a
command is one concern (handled entirely by `nodeiq.core.runner`), turning
that command's raw text into structured data is a second, separate concern
(handled entirely inside each collector's own `_parse_*` helpers), and
deciding what to do with that structured data — show it in a report, feed
it to an LLM — is a third concern that doesn't exist yet (Phases 4 and 6).
None of these three concerns needs to understand how either of the other
two actually works internally, which is exactly what makes each one safe
to change, test, or rewrite on its own.

### Why do contracts between modules matter?

A **contract** (introduced in Phase 2's notes) is an agreement about what
one piece of code provides and what another can rely on. Phase 3.2A's
whole deliverable is really one contract: every collector promises to
expose a function called `collect()` that returns exactly a `(data,
errors)` tuple shaped a specific way. Because that promise is written down
and identical for all nine planned collectors, the future scan coordinator
can be written **once**, against that one contract, instead of needing
special-case code for each collector's own quirks. This is the practical
payoff of a contract: it turns "the coordinator needs to understand nine
different collectors" into "the coordinator needs to understand one
shape, nine times."

### Why is parsing different from execution?

*Executing* a command means asking the operating system to run a program
and waiting to see what it prints — the result is just text, and neither
Python nor the command itself knows what that text is supposed to *mean*
to NodeIQ. *Parsing* means taking that text and turning it into data your
program can actually reason about (a list of filesystems, a percentage, a
process ID) — and it requires knowing the specific format one particular
command happens to use.

Keeping these two jobs in separate functions (per `docs/
collector_guidelines.md`'s "Separation of Command Execution and Parsing")
means a parsing function never needs a real command to test — you can hand
`_parse_df_output` a plain string written directly into a test and check
what comes out, with no subprocess, no mocking, and no real Linux system
involved at all. That's a large part of why `docs/collector_guidelines.md`
requires `_parse_*` helpers to be **pure functions**: same text in, same
structured data out, every time, with nothing else going on behind the
scenes.

### Why are we delaying application logging?

"Application logging" means a program keeping its own internal diary —
using Python's `logging` module to write out lines like "ran `df -h` at
14:02:03, took 40ms" to a console or log file, mainly so a developer can
later understand what the program itself was doing. `PROJECT_RULES.md`
Section 8 sketched out a plan for this early on, but NodeIQ's v1 doesn't
actually implement it — see `DECISIONS.md` ADR-013.

The reasoning is about avoiding unbuilt machinery nobody needs yet: every
fact a developer would want from a log line ("did this collector succeed?
what went wrong?") is *already* required to show up in the snapshot's
`collection_errors` section, because collectors return that information
directly through their return value. Building and configuring a whole
separate logging system now would duplicate information that already has
a home, before anyone has actually needed the extra detail logging would
add (timing beyond what `metadata` records, adjustable verbosity, etc.).
If that need becomes real later, `DECISIONS.md` says explicitly that
adding logging would deserve its own new decision — not a quiet reversal
of this one.

---

## Concepts Introduced in Phase 3.2B (Collector Infrastructure Refinement)

### What is a dataclass?

A **dataclass** is a Python feature (the `@dataclass` decorator, from the
standard library's `dataclasses` module) that writes the boring, repetitive
parts of a "just holds some named values" class for you — the
constructor, a readable `__repr__`, and equality comparison — so you only
have to write down the field names and their types. `CollectorResult`, for
example, is defined by listing four fields (`collector_name`, `data`,
`errors`, `duration_ms`); Python generates the rest.

Adding `frozen=True` (as every dataclass in NodeIQ so far does) makes
instances **immutable** — once created, none of their fields can be
reassigned. This matters here because a `CollectorResult` represents a
fact about what already happened ("this collector ran and got this
result") — nothing later in the program has a legitimate reason to change
that fact, so the type itself prevents it.

### Why use a result object instead of tuples?

A **tuple** is Python's plain, position-based grouping of values — `(x,
y)`. The Phase 3.2A contract returned `(data, errors)`, a two-item tuple.
That works, but only as long as everyone remembers "position 0 is data,
position 1 is errors" — the tuple itself carries no names, so reading
`result[0]` tells you nothing about what it contains without already
knowing the convention.

A **result object** (here, `CollectorResult`, a dataclass) replaces
positions with names: `result.data`, `result.errors`,
`result.duration_ms`. This has two concrete advantages that mattered
enough to justify the change: it's self-documenting at the point of use
(no need to remember "which position was which"), and it can grow to hold
more information (this refinement added `duration_ms` and
`collector_name`) without becoming an ever-longer, harder-to-read tuple.

### Why design for reasonable extensibility without over-engineering?

`CollectorContext` currently has only two fields (`scan_start_time`,
`default_timeout`), and it would be easy to assume it exists "to be
extensible for the future" in some vague sense. The actual reasoning is
narrower and worth noticing: both fields already solve a real, present
problem — every collector already needs a timeout value, and centralizing
it means a future scan mode could change every collector's timeout at
once, from one place, rather than editing nine files. Nothing speculative
was added "just in case" (no placeholder `extra: dict` field, no unused
hooks) — see `DECISIONS.md` ADR-014 and the Quality Check in
`docs/collector_guidelines.md`.

The useful distinction: **reasonable extensibility** means choosing a
shape (a plain dataclass) where adding a genuinely new field later, when a
real need shows up, is trivial and doesn't break existing code (because
Python dataclasses support default values for new fields). **Over-engineering**
would mean building machinery for extensibility you don't have a concrete
use for yet — a plugin system, a generic "settings bag," an abstract base
class — none of which NodeIQ needed to add anything meaningful here.

### What is a context object?

A **context object** is a single value bundling together information that
many different parts of a program need access to, so it can be passed
around as one thing instead of as several separate parameters (or worse,
as global variables). `CollectorContext` is exactly this: rather than
every collector function needing separate `scan_start_time` and
`default_timeout` parameters (or, worse, reading them from some shared
global state), they receive one `CollectorContext` object that already
bundles both.

The key property of a context object done well: it's passed explicitly, as
an ordinary argument — `collect(context)` — so a reader can see exactly
what a function depends on just by reading its signature. This is why
`PROJECT_RULES.md` Section 3's "no global mutable state" rule and
`CollectorContext`'s design go together: the alternative to a context
object usually isn't "no shared information at all," it's "the same
information, but hidden in a global instead of visible in a function
signature."

---

## Concepts Introduced in Phase 3.2C (System Collector v1)

### What is `/proc`?

`/proc` is a special directory that doesn't contain real files on disk —
it's a **virtual filesystem** the Linux kernel generates on the fly,
letting programs read live information about the running system by
opening what *look* like ordinary files. `/proc/uptime`, which
`system.py` reads, isn't stored anywhere; every time you read it, the
kernel computes a fresh answer right then and hands it back as two
numbers separated by a space. This is also why numbers in `/proc` files
change between reads: `cat /proc/uptime` twice in a row gives two
slightly different values, because the kernel is reporting live state,
not a saved file.

This matters for NodeIQ specifically because it means reading `/proc`
files is both **fast** (no disk I/O, no external process — just the
kernel handing over numbers it already tracks) and **exact** (no risk of
a stale cached value), which is exactly what a system-diagnostic tool
wants.

### What is `/etc/os-release`?

`/etc/os-release` is a plain text file, in the real (on-disk) filesystem
this time, that every modern Linux distribution ships specifically so
that scripts can reliably ask "which distribution and version is this?"
without needing to know one distribution's particular quirks. Its format
is simple and deliberate: one `KEY=value` pair per line, e.g.

```
NAME="Ubuntu"
VERSION_ID="24.04"
PRETTY_NAME="Ubuntu 24.04.4 LTS"
```

`system.py` reads this file directly and pulls out the `PRETTY_NAME`
line — the one field explicitly meant to be a ready-to-display, "this is
what the distribution is" string.

### Why does Linux expose system information through files?

Unix systems (Linux included) follow a long-standing philosophy often
summarized as "everything is a file" — as many kinds of information and
interaction as reasonably possible are exposed through the filesystem's
familiar `open`/`read`/`close` operations, rather than through bespoke,
one-off APIs that a program would need special code to talk to. `/proc`
is the clearest example of this: instead of Linux needing a special
system call just for "how long has this machine been up," it exposes that
answer as a file any program can read with the exact same code it would
use to read any other file.

The practical payoff for NodeIQ: `system.py` doesn't need any special
library or system-specific API to read kernel state — `Path("/proc/
uptime").read_text()` is the *same* operation Python would use to read any
ordinary text file on disk, even though what's "in" that file is being
generated live by the kernel.

### What's the difference between machine-readable and human-readable interfaces?

A **human-readable** interface is designed to be read by a person looking
at a terminal — it prioritizes being easy to scan at a glance, often
combining several pieces of information into one nicely formatted line,
and its exact wording can change between versions without much
consequence (a human just reads whatever's there). The `uptime` command's
output (`14:32:07 up 10 days, 3:42, 2 users, load average: ...`) is a good
example: convenient for a person, but if a program wants just the number
of seconds of uptime, it has to unpick that sentence apart, hoping the
exact wording doesn't change on some other system or future version.

A **machine-readable** interface is designed to be read by a program —
`/proc/uptime`'s `"36564.34 36066.00"` and `/etc/os-release`'s
`KEY=value` lines are both examples. They prioritize a stable, predictable
structure over readability; a human can still read them (they're plain
text), but their whole point is that a program can parse them with
simple, reliable rules that won't quietly break because someone tweaked a
sentence's wording.

`docs/system_collector.md` and `docs/collector_guidelines.md`'s "Two Ways
to Gather Evidence" both come back to this same distinction: whenever a
machine-readable source exists for a fact NodeIQ needs, prefer it over
parsing a human-readable command's output for the same fact — it's less
fragile and doesn't require guessing at another program's formatting
choices.

---

## Concepts Introduced in Phase 3.3 (Resource Collector)

### What does `/proc/meminfo` contain?

`/proc/meminfo` is a `/proc` file (see "What is `/proc`?" above) listing
dozens of memory-related statistics, one per line, each shaped
`Key:  value kB`:

```
MemTotal:         974844 kB
MemFree:          572636 kB
MemAvailable:     706648 kB
SwapTotal:             0 kB
SwapFree:              0 kB
...
```

`resource.py` only reads four of these lines — `MemTotal`,
`MemAvailable`, `SwapTotal`, `SwapFree` — and computes everything else
(bytes used, percentages) from just those four numbers. The file has many
more lines (`Buffers`, `Cached`, `Dirty`, and so on) describing exactly
*how* the kernel is using memory internally, but NodeIQ's v1 doesn't need
that level of detail to answer "what is consuming memory?"

### What does "load average" actually mean?

**Load average** is a single number summarizing how much demand there has
been for the CPU over a recent stretch of time — roughly, the average
number of processes that were either running or waiting for CPU time
during that period. `/proc/loadavg` reports three of these numbers at
once, averaged over the last 1, 5, and 15 minutes respectively, so you can
see whether load is currently spiking, steadily elevated, or already
trending back down.

A load average of `1.0` on a single-core machine means the CPU was
*exactly* as busy as it could sustainably be — one thing running or
waiting, all the time. A load average of `4.0` on a 4-core machine means
roughly the same thing: demand matched capacity. This is the one place
where `resource.py`'s current scope has a real gap worth knowing about:
without `core_count` (deferred — see `docs/resource_collector.md`), a raw
load average number alone doesn't tell you whether `0.56` is "barely
loaded" (a 1-core machine) or "essentially idle" (an 8-core machine) — you
need to know the core count to interpret it, and NodeIQ doesn't collect
that yet.

### Why is available memory often more useful than free memory?

`/proc/meminfo` reports both `MemFree` (memory nothing is using at all)
and `MemAvailable` (memory that could be handed to a new process without
that process having to wait on swap). These sound similar but answer
different questions, and `MemFree` alone is famously misleading:

Linux aggressively uses "free" memory for disk caching (`Buffers` and
`Cached` in `/proc/meminfo`) — data recently read from disk is kept around
in RAM in case it's needed again soon, since RAM is much faster than disk.
This cache isn't wasted; the kernel will instantly drop cached pages the
moment a real process actually needs that memory. But it means `MemFree`
on a healthy, well-utilized Linux server is often surprisingly *low* — not
because the machine is struggling, but because it's using spare memory
productively for caching.

`MemAvailable` already accounts for this: it's the kernel's own estimate
of "how much memory could actually be given to a new process right now,"
including memory it would reclaim from the cache if asked. This is why
`resource.py` uses `MemAvailable` (not `MemFree`) to compute
`memory_used_bytes`/`memory_usage_percent` — it answers "is this machine
actually running low on memory?" far more reliably than `MemFree` does.

### What's the difference between memory usage and CPU load?

These measure two entirely different kinds of resource pressure, and
it's easy to conflate them:

- **Memory usage** is a *snapshot* — at this exact instant, how many bytes
  of RAM are in use vs. available. It doesn't inherently involve time; you
  can ask "what's memory usage right now?" and get a single, complete
  answer from one read of `/proc/meminfo`.
- **CPU load** is fundamentally about *demand over time* — it only means
  something as an average across a window (1, 5, or 15 minutes), because
  "how busy was the CPU at this exact instant" isn't really a meaningful
  question the way "how much memory is in use right now" is. This is also
  why CPU *utilization percentage* (a different, related metric NodeIQ
  doesn't collect yet — see `docs/resource_collector.md`) requires taking
  two separate readings of `/proc/stat` a short time apart and computing
  the difference, whereas every memory field here comes from a single
  point-in-time read of `/proc/meminfo`.

A machine can be high on one and low on the other — plenty of free memory
but a CPU struggling to keep up with requests, or memory nearly exhausted
while the CPU sits mostly idle waiting on disk I/O. This is exactly why
`resource.py` treats them as two independent data sources internally, even
though they're gathered by the same collector: a `/proc/meminfo` failure
should never prevent `/proc/loadavg` from still being read, and vice
versa.
