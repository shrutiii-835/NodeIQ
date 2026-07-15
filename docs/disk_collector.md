# Disk + Inodes Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/disk.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the
fourth real Linux collector, following `system.py`, `cpu_memory.py`, and
`processes.py`'s `CollectorContext` → `collect()` → `CollectorResult`
pattern. Unlike `cpu_memory.py` and `processes.py`, it needs **commands**,
not `/proc` files — see "Why `df` Was Chosen" below.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `disk` section,
Section 6, which this implementation's field shape diverges from — see
"A Note on Naming and Schema Alignment" below).

---

## Responsibilities

The Disk Collector answers "why might disk space be running out?" — one
of NodeIQ's headline example questions — for every mounted filesystem.
It gathers two related but independent facts per filesystem, merged into
one entry:

- **Disk capacity**: `total_bytes`, `used_bytes`, `available_bytes`,
  `usage_percent`.
- **Inode usage**: `inode_total`, `inode_used`, `inode_available`,
  `inode_usage_percent`.

Plus two scan-wide summary fields computed from the merged list:
`highest_disk_usage_percent` and `highest_inode_usage_percent` — the
single most-full filesystem by each metric, so a report or an `ask`
answer can immediately say "your fullest filesystem is at N%" without
scanning the whole list itself.

---

## What a Filesystem Is

A **filesystem** is the structure the operating system uses to organize
data on a storage device (or a virtual, in-memory device) — it's what
turns a raw block of storage into files and directories you can actually
read and write. A single machine typically has several filesystems at
once: one for the root partition on a physical disk (e.g. `ext4` on
`/dev/sda1`), and several virtual, memory-backed ones the kernel creates
for its own bookkeeping (`tmpfs` for `/run`, `efivarfs` for UEFI boot
variables). Every filesystem is **mounted** at a specific path — see
"What a Mount Point Is" in `LEARNING_NOTES.md` — which is why `df`
reports one row per filesystem, each with its own mount point, rather
than one number for "the disk."

## What an Inode Is, and Why Inode Exhaustion Matters

An **inode** is a fixed-size record the filesystem keeps for every single
file and directory, holding that file's metadata — its owner, its
permissions, its size, and where its actual data blocks live on disk.
Crucially, **every filesystem is created with a fixed, finite number of
inodes**, decided when the filesystem was formatted — this number
usually has nothing to do with how much storage *space* the filesystem
has, only with how many *files* it was designed to hold.

This is why **a filesystem can run out of inodes while still having
plenty of free space** — see `LEARNING_NOTES.md`, "Why can a disk be
only 40% full and still fail?" A filesystem with millions of tiny files
(a classic case: a directory silently accumulating one small log or
cache file per request, never cleaned up) can exhaust its inode budget
long before it exhausts its byte budget. Once a filesystem's inodes are
exhausted, **no new file can be created on it, even if there are
gigabytes of free space** — an operationally serious failure mode that
`df -h`-style space checks alone will never reveal. This is exactly why
this collector tracks `inode_usage_percent` as its own first-class
metric, not a footnote to disk space.

---

## Why `df` Was Chosen

Every previous collector (`system.py`, `cpu_memory.py`, `processes.py`)
preferred a stable kernel-provided file (`/proc/uptime`, `/proc/meminfo`,
`/proc/<pid>/status`) over parsing a command's output, per
`PROJECT_RULES.md` Section 9 (item 7). Disk and inode usage are the
first case in this project where **no such file exists**: there's no
single `/proc` entry that reports "total/used/available bytes and
inodes for every mounted filesystem" the way `/proc/meminfo` does for
memory. Computing this from scratch (walking `/proc/mounts` and calling
`statvfs()` for each mount point) would just be reimplementing exactly
what `df` already does, using the exact same underlying system call —
with no benefit, only more code to maintain. `df` is the canonical,
purpose-built interface for this information, so this collector runs it
via `nodeiq.core.runner.run_command`, the same as any command-based
collector.

Two separate invocations are used because `df` can't report both facts
at once:

```
$ df -P -B1        # capacity, byte-precise
$ df -P -i          # inode usage
```

**Why `-P`:** without it, `df` can wrap a row onto two lines when a
device name is long enough to overflow its column — the filesystem name
prints alone on one line, and the rest of that row's fields print on the
next. `-P` forces POSIX-format output: exactly one line per filesystem,
every time, regardless of name length. This collector's own parser
assumes one line per filesystem and would break on a wrapped row, so
`-P` isn't optional — it's what makes `df`'s output reliably
machine-parseable at all. (This exact flag already appears as the
established convention in `docs/collector_guidelines.md`'s own
illustrative `disk.py` pseudocode, `run_command(["df", "-P", "-k"], ...)`
— this implementation follows that precedent.)

**Why `-B1`:** requests byte-precision block sizes directly, so
`total_bytes`/`used_bytes`/`available_bytes` need no unit conversion or
rounding — `df`'s own arithmetic is exact, and this collector just
reads the numbers it already computed.

Real output pulled from the Multipass VM before writing the parser:

```
$ df -P -B1
Filesystem       1-blocks       Used  Available Capacity Mounted on
tmpfs            99827712    1142784   98684928       2% /run
efivarfs           262044      14616     247428       6% /sys/firmware/efi/efivars
/dev/sda1      4083888128 2437246976 1629863936      60% /

$ df -P -i
Filesystem     Inodes  IUsed  IFree IUse% Mounted on
tmpfs          121855    688 121167    1% /run
efivarfs            0      0      0     - /sys/firmware/efi/efivars
/dev/sda1      524288 125657 398631   24% /
```

`efivarfs` (a virtual filesystem for UEFI variables) reports `-` for
every inode field — it doesn't support the inode concept at all. This is
parsed as `None`, not an error (see `_parse_percent`/`_parse_optional_int`
in `disk.py`) — the same "genuinely doesn't apply" vs. "couldn't
determine" distinction `PROJECT_RULES.md` Section 7 requires everywhere
else in this project.

---

## Merging Two Command Outputs Into One Structure

`df -P -B1` and `df -P -i` are parsed independently by two pure
functions (`_parse_df_output`, `_parse_df_inode_output`) — neither knows
the other exists. `_merge_filesystems` then combines them, keyed by
**mount point** (the one value both outputs share and that uniquely
identifies one mounted filesystem):

```python
def _merge_filesystems(filesystems: list[dict], inode_usage_by_mount: dict) -> list[dict]:
    merged = []
    for fs in filesystems:
        inode_fields = inode_usage_by_mount.get(fs["mount_point"], {...all None...})
        merged.append({**fs, **inode_fields})
    return merged
```

If a mount point present in the disk-usage output has no matching entry
in the inode-usage output (either the whole `df -P -i` command failed,
or — in principle — a future filesystem type omits itself from one
output but not the other), that filesystem's four inode fields become
`None` rather than the whole entry being dropped. Disk usage is still
real, useful evidence even without inode data attached.

---

## Error Handling

Disk usage and inode usage are gathered by two independent `try`/`except`
blocks in `collect()`, matching this task's explicit instruction ("if
one command fails, return whatever is still available"):

- **If `df -P -B1` fails:** nothing useful can be returned at all — there
  would be no filesystem list to attach inode data to — so `collect()`
  returns `{"filesystems": [], "highest_disk_usage_percent": None,
  "highest_inode_usage_percent": None}` plus one error entry.
- **If only `df -P -i` fails:** the full disk-usage list is still
  returned, every filesystem's four inode fields are `None`,
  `highest_inode_usage_percent` is `None`, and one error entry describes
  the inode command's failure — `highest_disk_usage_percent` is
  unaffected. Partial data always beats no data (`PROJECT_RULES.md`
  Section 7).

Verified for real: on macOS (whose `df` doesn't support `-B1` at all —
`invalid option -- B`), `collect()` correctly returns the empty-list
shape above with a clear error entry, rather than crashing.

---

## A Note on Naming and Schema Alignment

`docs/snapshot_schema.md` Section 6 defines a `disk` section with a
different field shape than this implementation produces:

```json
{
  "filesystems": [
    {
      "mount_point": "<string>", "device": "<string>", "filesystem_type": "<string>",
      "size_kb": 0, "used_kb": 0, "available_kb": 0, "used_percent": 0.0,
      "inodes_total": 0, "inodes_used": 0, "inodes_used_percent": 0.0
    }
  ]
}
```

Consistent with this project's established practice (the same treatment
given to every previous collector's schema divergence), the differences
are recorded here rather than silently resolved:

- **`filesystem` (this implementation) vs. `device`** and **`total_bytes`/
  `used_bytes`/`available_bytes` (bytes) vs. `size_kb`/`used_kb`/
  `available_kb`** (kB) — the same naming/unit-convention tension already
  open for `cpu_memory.py` and `processes.py`. Not reconciled here either.
- **`inode_available` is new** — not in the original schema, which has
  `inodes_total`/`inodes_used`/`inodes_used_percent` but no explicit
  "how many inodes are left" field. Included here per this task's
  explicit field list.
- **`filesystem_type` (e.g. `ext4`) is not collected.** Neither `df -P
  -B1` nor `df -P -i` reports it — a third command (`df -T`) or parsing
  `/proc/mounts` would be needed. Not part of this task's scope.
- **`highest_disk_usage_percent`/`highest_inode_usage_percent` are new**
  — scan-wide summary fields with no equivalent in the original schema
  at all, added per this task's explicit instruction. These make "what's
  the fullest filesystem" answerable without a consumer computing a max
  over the list itself.

None of this is resolved by editing `docs/snapshot_schema.md` itself —
tracked here and in `CHECKLIST.md`/`LOGS.md`, consistent with how every
other collector left its own schema-alignment question open.

---

## Testing

- **Unit tests** (`tests/collectors/test_disk.py`, 24 tests): `_parse_df_output`
  and `_parse_df_inode_output` tested with literal sample text (including
  a mount point containing a space, a malformed line, and the real
  `efivarfs`-style `-` inode case); `_parse_percent`/`_parse_optional_int`
  tested for valid values, `-`, and garbage; `_merge_filesystems` tested
  for a full match and for a missing inode entry; `_highest` tested for
  the normal case, `None`-filtering, an all-`None` list, and an empty
  list; `collect()` tested end-to-end for the happy path, total
  disk-usage-command failure, and inode-command-only failure.
- **Integration test** (`tests/collectors/test_disk_integration.py`, 1
  test): calls the real `collect()` with nothing mocked, automatically
  skipped unless running on Linux. Verified by copying the code to the
  Multipass Ubuntu 24.04 VM (`main-cattle`) and running the full test
  suite — all 111 tests passed, including this one and the coordinator's
  end-to-end integration test (now covering all four collectors),
  producing a real, correctly-merged 8-filesystem snapshot with accurate
  `None` handling for `efivarfs`/`/boot/efi`.

---

## Collector Review Checklist

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — both anticipated failure points (either `df` command failing or producing unparseable output) are caught and turned into error entries.
- [x] Disk usage and inode usage are independent data sources — an inode-command failure never loses the disk-usage data already gathered.
- [x] Uses `nodeiq.core.runner.run_command` for both `df` invocations — never raw `subprocess`, per `docs/collector_guidelines.md`.
- [x] Parsing is separated from command execution: `_parse_df_output`, `_parse_df_inode_output`, `_parse_percent`, and `_parse_optional_int` are pure functions, tested with literal sample text, never touching a real subprocess.
- [x] Merge logic (`_merge_filesystems`) is a small, readable, single-purpose function, kept separate from both parsing functions.
- [x] `-` values (filesystems with no inode concept, e.g. `efivarfs`) degrade gracefully to `None` rather than raising.
- [x] No unnecessary abstractions — no generic "command output merger" framework, just one small function for this one merge.
- [x] Field names use `snake_case`; no collector-invented redaction, logging, retries, or presentation logic.
- [x] Unit tests cover parsing, merging, the `highest_*` computation, and `collect()` end-to-end (happy path and both partial-failure modes); an integration test verifies real behavior on the Multipass VM.
- [ ] *(Deferred, not yet reconciled)* Field names/units and `filesystem_type` fully match `docs/snapshot_schema.md`'s original `disk` section — see "A Note on Naming and Schema Alignment" above.
