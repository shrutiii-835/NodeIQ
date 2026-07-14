# System Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/system.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the first
real Linux collector in NodeIQ — its purpose is as much to prove the
`CollectorContext` → `collect()` → `CollectorResult` pattern works
end-to-end as it is to gather this specific data.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the full `system` section
schema, which this v1 collector intentionally implements only part of —
see "Fields Intentionally Deferred" below).

---

## Responsibilities of the System Collector

The System Collector answers the most basic operational question NodeIQ
can ask about a machine: **what is this, and what is it running?**
Specifically, v1 gathers exactly five facts:

- `hostname` — which machine this is
- `operating_system` — a human-readable description of the Linux
  distribution installed
- `kernel_version` — which kernel is actually running
- `architecture` — the machine's hardware architecture (e.g. `x86_64`,
  `aarch64`)
- `uptime_seconds` — how long the machine has been running, in seconds

Nothing else. Per `docs/collector_guidelines.md`, it does not decide how
this data is displayed (that's `report`, Phase 4), does not answer
questions about it (that's `ask`, Phase 6), and does not know it's part of
a larger scan (that's the coordinator's job, still a placeholder).

Every field is gathered **independently** — if one fails, the other four
are still returned, and the failure is recorded as a
`docs/snapshot_schema.md`-shaped entry in `CollectorResult.errors` rather
than stopping the whole collector (see `PROJECT_RULES.md` Section 7).

---

## Why Each Data Source Was Chosen

| Field | Source | Why |
|---|---|---|
| `hostname` | `hostname` command | A single, universal command available on essentially every Unix-like system, whose entire output is exactly the hostname — no meaningful parsing beyond trimming whitespace. |
| `kernel_version` | `uname -r` | The standard, portable way to ask the kernel what version it is; output is one line, nothing to parse beyond trimming whitespace. |
| `architecture` | `uname -m` | Same tool as kernel version, different flag — asking the same "ask the kernel directly" source for a related fact keeps this collector's command surface small. |
| `operating_system` | `/etc/os-release` (`PRETTY_NAME` field) | A machine-readable, `KEY=value` file every modern Linux distribution ships specifically so scripts don't have to guess at distribution identity by parsing `/etc/issue` or a version-specific command. See below for why this is a file read, not a command. |
| `uptime_seconds` | `/proc/uptime` | The kernel's own live uptime counter, exposed as a file — see below for why this is preferred over running `uptime`. |

Three of the five fields (`hostname`, `kernel_version`, `architecture`)
come from trivial single-line commands where there's essentially nothing
to parse — `uname`'s whole job *is* to hand back exactly the fact
requested, with no formatting or extra context to strip away. The other
two (`operating_system`, `uptime_seconds`) come from files precisely
because a *command* asking the same question (`lsb_release -d`, `uptime`)
would return a formatted, human-oriented line that has to be parsed apart
from surrounding text — see the next section.

---

## Why Machine-Readable Files Are Preferred Over Parsing Formatted Command Output

Compare two ways of finding out how long a machine has been up:

```
$ uptime
14:32:07 up 10 days, 3:42, 2 users, load average: 0.15, 0.22, 0.18

$ cat /proc/uptime
878536.42 3512004.11
```

`uptime`'s output is designed for a human glancing at a terminal — it
bundles the current time, uptime in a mixed "days, hours:minutes" format,
user count, and load averages into one line, in a format that has
changed across different Unix variants and can change again. Extracting
just the uptime number means parsing free-form text that was never meant
to be machine-parsed, and quietly encodes assumptions about its exact
wording that could break on some other system.

`/proc/uptime`, by contrast, was written by the kernel specifically to be
read by programs: two space-separated numbers, always in the same units
(seconds), with a stable meaning that doesn't change based on locale,
terminal width, or how many users are logged in. The same reasoning
applies to `/etc/os-release` vs. something like `lsb_release -d`: the file
is `KEY=value` pairs, explicitly designed for scripts to parse; the
command exists for a human to read.

This is also why `PROJECT_RULES.md` Section 9 (item 7) and
`docs/collector_guidelines.md`'s "Two Ways to Gather Evidence" both state
this preference as a standing rule, not something decided fresh for this
collector — every future collector should reach for a file first and a
command's output only when no machine-readable file exists for that fact.

---

## Fields Intentionally Deferred to Future Versions

`docs/snapshot_schema.md` Section 3 already defines a richer `system`
section schema than this v1 collector implements:

```json
{
  "hostname": "<string>",
  "os_name": "<string — e.g. Ubuntu>",
  "os_version": "<string — e.g. 24.04>",
  "kernel_version": "<string>",
  "architecture": "<string — e.g. x86_64>",
  "boot_time": "<ISO 8601 UTC timestamp>",
  "uptime_seconds": 0
}
```

This task's scope was deliberately narrower — exactly `hostname`,
`operating_system`, `kernel_version`, `architecture`, `uptime_seconds` —
to validate the collector pattern with the smallest useful real
implementation, not to fully implement the Phase 2 schema in one step.
Two differences are worth calling out explicitly rather than leaving
implicit:

- **`operating_system` (one field) vs. `os_name` + `os_version` (two
  fields).** `/etc/os-release`'s `PRETTY_NAME` line already combines both
  into one human-readable string (`"Ubuntu 24.04.4 LTS"`); splitting it
  back into separate name/version fields would mean parsing a second
  field (`NAME` and `VERSION_ID` both exist in the same file) and is a
  reasonable next step, deferred rather than done now.
- **`boot_time` is not collected at all in v1.** It could be derived from
  `uptime_seconds` plus the scan's `CollectorContext.scan_start_time` (this
  collector already receives everything it needs to compute it), but
  doing so wasn't part of this task's five-field scope and is deferred.

This is a **known, deliberate gap** between the collector's current
output and the full schema in `docs/snapshot_schema.md`, not an oversight
— tracked in `LOGS.md` and `CHECKLIST.md` as a follow-up for when the
System Collector is extended.

---

## Testing

- **Unit tests** (`tests/collectors/test_system.py`, 17 tests): every
  `_parse_*` function tested with literal sample text (no I/O at all);
  every `_get_*` function tested with `run_command` monkeypatched or a
  `tmp_path` file standing in for the real path; `collect()` tested
  end-to-end with everything faked, covering both "everything succeeds"
  and "one field fails, the rest don't."
- **Integration test** (`tests/collectors/test_system_integration.py`, 1
  test): calls the real `collect()` with no mocking at all, and is
  automatically skipped unless running on Linux (checked via
  `platform.system()`), so `pytest` on a non-Linux dev machine skips it
  rather than failing for an unrelated reason. Verified by actually
  copying the code to the Multipass Ubuntu 24.04 VM (`main-cattle`,
  `DECISIONS.md` ADR-002), installing `pytest` there, and running the full
  suite — all 30 tests passed, including this one running for real.
