# Scheduled Jobs Collector — NodeIQ

**Status:** Implemented and tested
(`src/nodeiq/collectors/scheduled_jobs.py`), both with mocked unit tests
and a real integration test verified against the Multipass Ubuntu 24.04
VM (`DECISIONS.md` ADR-002). This is the sixth real Linux collector
(Collector Sprint 1, alongside `services.py` and `permissions.py`),
following the same `CollectorContext` → `collect()` → `CollectorResult`
pattern as every previous collector.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `scheduled_jobs`
section, Section 10, whose `cron_jobs` field shape this implementation
matches exactly — see "Schema Alignment" below).

---

## Responsibilities

The Scheduled Jobs Collector answers "what cron jobs exist?" — one of
NodeIQ's headline example questions — covering both ways Linux
schedules recurring work:

- **Cron**: system-wide jobs (`/etc/crontab`, `/etc/cron.d/*`) and
  personal jobs (`/var/spool/cron/crontabs/*`, read only where
  accessible), merged into one `cron_jobs` list plus a `cron_job_count`.
- **Systemd timers**: `systemctl list-timers --all`, summarized as
  `systemd_timers` (each with its `name` and the `unit` it activates)
  plus a `timer_count`.

---

## Reading Cron Directly, Not Via `crontab -l`

Every cron source here is read as a plain file, not via the `crontab`
command — matching `PROJECT_RULES.md` Section 9 (item 7)'s standing
preference for a stable, direct interface over a command wrapper, the
same reasoning `system.py` and `cpu_memory.py` already established for
`/proc` files.

**System cron** (`/etc/crontab`, `/etc/cron.d/*`) uses one format —
five schedule fields, an explicit **user** field, then the command:

```
17 *	* * *	root	cd / && run-parts --report /etc/cron.hourly
```

**Personal cron** (`/var/spool/cron/crontabs/<username>`) uses a
slightly different format — the same five schedule fields, but **no
user field**, since the file itself belongs to exactly one user (its
filename *is* the username):

```
0 9 * * * /home/alice/standup.sh
```

Both formats also allow special schedules (`@reboot`, `@daily`, ...)
in place of the five numeric fields. `_parse_system_crontab_line` and
`_parse_user_crontab_line` are two separate, straightforward functions
(not one function branching on whether a user field is present) —
favoring explicit, obviously-correct code over a cleverer, harder-to-read
single function, per `PROJECT_RULES.md` Section 3. Their ~10-line
overlap is recorded in this sprint's Refactoring Opportunities rather
than consolidated now, per this task's explicit "do not refactor" scope.

Both parsers skip blank lines, comments (`#...`), and environment
variable assignments (e.g. `PATH=/usr/bin:/bin`, `SHELL=/bin/sh`) —
real lines that appear throughout `/etc/crontab` and `/etc/cron.d/*` but
aren't schedulable jobs. An assignment line has no internal whitespace
(one token), which is naturally too few tokens to look like a schedule
line — no special-case detection needed beyond a plain length check.

---

## Why Personal Crontabs Are "Read Where Accessible," Not Guaranteed

`/var/spool/cron/crontabs/` is deliberately restrictive — real
permissions pulled from the Multipass VM:

```
$ ls -la /var/spool/cron/crontabs/
drwx-wx--T 2 root crontab 4096 ...
```

Group has **write+execute but not read** — even a `crontab`-group
member can't *list* this directory's contents directly; only the
`crontab` command itself (which runs with elevated privileges) is meant
to read or write these files. As a non-root user, `_get_user_cron_jobs`
genuinely cannot list this directory at all:

```
$ ls -la /var/spool/cron/crontabs/
ls: cannot open directory '/var/spool/cron/crontabs/': Permission denied
```

This is treated as a normal, expected outcome — an empty list, no error
— per this task's own "user cron jobs where accessible" instruction and
`PROJECT_RULES.md` Section 7's "the system genuinely has none of this"
vs. "we couldn't check" distinction: being unable to read *someone
else's* crontab as an unprivileged user isn't a failure of this
collector, it's the system's access control working as designed. When
this scan *does* run with sufficient privilege (e.g. as root), every
readable file in the directory is parsed, one user at a time, and a
single unreadable file among several doesn't stop the rest from being
read.

---

## Why Timer Timestamps Are Not Parsed

`systemctl list-timers`'s output packs a lot into two columns that
aren't simple values — real output from the VM:

```
Wed 2026-07-15 07:10:00 UTC      30s Wed 2026-07-15 07:00:00 UTC     9min ago sysstat-collect.timer sysstat-collect.service
Thu 2026-07-16 00:07:00 UTC      16h -                                      - sysstat-summary.timer sysstat-summary.service
```

NEXT and LAST are each a human-formatted, locale-dependent absolute
timestamp *plus* a relative-time phrase ("9min ago", or `-` if never
run) — genuinely fragile to parse positionally, and exactly the kind of
human-oriented text this project avoids parsing wherever a simpler path
exists (`docs/system_collector.md`'s "Why Machine-Readable Files Are
Preferred," applied here to a command's *columns* rather than a whole
command).

The simpler path here: a timer's own name and the service it activates
are always the **last two** whitespace-separated tokens on every line,
regardless of how many words the date/relative-time columns before them
contain — unit names never contain spaces. `_parse_list_timers` reads
`tokens[-2]` and `tokens[-1]` and ignores everything else, sidestepping
the whole date-parsing problem entirely. `next_run`/`last_run` (present
in `docs/snapshot_schema.md` Section 10 as nullable fields) are
consequently not populated in this v1 — deferred, not silently dropped,
and recorded under "Schema Alignment" below.

---

## Schema Alignment

`docs/snapshot_schema.md` Section 10's `cron_jobs` shape (`user`,
`schedule`, `command`, `source_file`) is matched **exactly** by this
implementation — a rare case where no field-naming divergence needed to
be recorded at all, since the original Phase 2 design already fit this
collector's real data well.

`systemd_timers` diverges in one place: this implementation returns
`name`/`unit` per timer (matching the schema's own field names for
those two) but does **not** populate `next_run`/`last_run`, for the
reason above. Recorded here rather than silently omitted, consistent
with every prior collector's practice of flagging schema divergences
explicitly.

---

## Testing

- **Unit tests** (`tests/collectors/test_scheduled_jobs.py`, 16 tests):
  both crontab-line parsers tested with literal sample lines (normal
  entries, `@special` schedules, comments, blank lines, environment
  assignments); `_get_system_cron_jobs`/`_get_user_cron_jobs` tested via
  monkeypatched path constants pointing at `tmp_path` (including missing
  files/directories and an inaccessible spool directory); `_parse_list_timers`
  tested with real VM-shaped sample text including a never-run timer
  (`-` placeholders); `collect()` tested end-to-end for the merged happy
  path and a `list-timers` command failure.
- **Integration test**
  (`tests/collectors/test_scheduled_jobs_integration.py`, 1 test): calls
  the real `collect()` with nothing mocked, automatically skipped unless
  running on Linux. Verified on the Multipass VM (real result: 8 system
  cron jobs across `/etc/crontab` and `/etc/cron.d/*`, 17 systemd
  timers, no errors) as part of the full 151-test suite for this sprint.

---

## Collector Review Checklist

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — the one real command (`systemctl list-timers`) is wrapped in `try`/`except`; every file-based cron source degrades gracefully on its own.
- [x] Cron is read directly as files, never via `crontab -l` — avoids the ambiguity of `crontab -l`'s "no crontab for this user" non-zero exit vs. a genuine failure.
- [x] Parsing is separated from file/command access: both crontab-line parsers and `_parse_list_timers` are pure functions, tested with literal sample text.
- [x] Missing or inaccessible cron sources degrade gracefully to an empty contribution, never an error — matches this task's explicit instruction.
- [x] A real command failure (`list-timers`) *is* recorded as a structured error, distinct from the "file/directory doesn't exist" cases.
- [x] Field names match `docs/snapshot_schema.md` Section 10's `cron_jobs` shape exactly; `systemd_timers`' omitted fields are recorded, not silently dropped.
- [x] Unit tests cover parsing, file discovery (including inaccessible directories), and `collect()` end-to-end; an integration test verifies real behavior on the Multipass VM.
- [ ] *(Known duplication, not refactored per this sprint's scope)* `_parse_system_crontab_line`/`_parse_user_crontab_line` share ~10 lines of structure — see this sprint's Refactoring Opportunities.
