# Network Collector — NodeIQ

**Status:** Implemented and tested (`src/nodeiq/collectors/network.py`),
both with mocked unit tests and a real integration test verified against
the Multipass Ubuntu 24.04 VM (`DECISIONS.md` ADR-002). This is the
eighth real Linux collector (Collector Sprint 2, alongside `logs.py`),
following the same `CollectorContext` → `collect()` → `CollectorResult`
pattern as every previous collector.

Read this alongside [collector_guidelines.md](collector_guidelines.md)
(the general contract every collector follows) and
[snapshot_schema.md](snapshot_schema.md) (the existing `network`
section, Section 9, whose `interfaces`/`listening_ports` shape this
implementation extends — see "Schema Alignment" below).

---

## Responsibilities

The Network Collector answers "what ports are open?" — one of NodeIQ's
headline example questions — plus basic connectivity context, gathered
from four independent sources:

- **Interfaces**: `ip -o link show` (state) merged with `ip -o addr show`
  (IPv4/IPv6 addresses), by interface name.
- **Default route**: `ip route show default` — the gateway and
  interface for outbound traffic, or `None` if no default route is
  configured.
- **Listening ports**: `ss -tulpn` — protocol, local address, port, and
  (where privilege allows) the owning process.
- **Firewall**: best-effort detection of whichever of `ufw`, `nft`, or
  `iptables` is usable on this system.

Deliberately excluded, per this task's "do not attempt deep networking
diagnostics" instruction: routing tables beyond the default route,
non-listening (established/connected) sockets, interface statistics
(bytes/packets sent/received), and DNS configuration.

---

## Why `-o` (Oneline) Mode for `ip`

`ip addr show` and `ip link show`, without `-o`, print multi-line,
indented, human-oriented blocks per interface — genuinely awkward to
parse reliably (continuation lines, variable indentation). `-o` forces
exactly one line per fact (one line per interface for `link`, one line
per address for `addr`), the same "prefer a flag that produces a
stable, parseable format" reasoning already established for `df -P`
(`docs/disk_collector.md`) and `systemctl --plain --no-legend`
(`docs/services_collector.md`).

## Why Interface State Comes From `<FLAGS>`, Not the `state` Keyword

Real `ip -o link show` output pulled from the Multipass VM:

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT ...
2: enp0s1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode ...
```

Every line has both a `<FLAGS,...>` bracket *and* a `state <WORD>`
keyword — but they don't agree for loopback: `lo`'s `state` keyword says
`UNKNOWN` (a real, standard kernel quirk — loopback interfaces don't
track operational state the way a physical NIC does), while its flags
bracket correctly contains `UP`. Since the task asks for "state
(UP/DOWN where available)" — a simple binary answer — this collector
reads the `<FLAGS>` bracket instead of the `state` keyword: `"up"` if
`UP` appears in the bracket, `"down"` otherwise. This gives a
consistent, meaningful answer for every interface, loopback included,
rather than leaking the kernel's more idiosyncratic internal
state-machine vocabulary (`UNKNOWN`, `DORMANT`, `NOTPRESENT`, ...) into
a field that's supposed to be a simple yes/no.

---

## Listening Ports: Handling Scoped and IPv6 Addresses

Real `ss -tulpn` output pulled from the Multipass VM:

```
Netid State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port  Process
udp   UNCONN 0      0       127.0.0.53%lo:53     0.0.0.0:*
tcp   LISTEN 0      4096    [::]:22              [::]:*             users:(("sshd",pid=851,fd=4))
```

Two real address shapes needed careful handling, not just a plain
"split on colon":

- **Scoped addresses** (`127.0.0.53%lo:53`) include a `%<interface>`
  suffix for link-local-style bindings. Splitting on the *last* colon
  (`rpartition(":")`) correctly separates `127.0.0.53%lo` from `53`
  regardless of the `%lo` suffix.
- **IPv6 bracket addresses** (`[::]:22`) contain colons *inside* the
  address itself. `rpartition(":")` still works correctly here too —
  it splits on the rightmost colon regardless of how many others
  precede it, giving `[::]` and `22`.

This is why `_parse_ss_output` uses `rpartition`, not `split`, to
separate address from port — one simple, correct operation handles
every real shape observed, rather than needing separate special-case
logic for IPv4/scoped/IPv6.

---

## Why Process Ownership Is Genuinely Optional

Real output confirms the task's own "process/program (where available)"
wording is not a hedge — it's a hard requirement:

```
$ ss -tulpn                          # as root
tcp LISTEN 0 4096 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=851,fd=3))

$ ss -tulpn                          # as a normal user
tcp LISTEN 0 4096 0.0.0.0:22 0.0.0.0:*
```

Without root, the Process column is simply absent from the line —
`_parse_ss_output` handles this by checking whether a 7th token exists
at all (`process_name`/`pid` become `None` when it doesn't), never
treating a missing process field as a parsing failure.

---

## Firewall Detection Is Necessarily Best-Effort

Real testing on the Multipass VM, run as the ordinary `ubuntu` user
(not root):

```
$ ufw status
ERROR: You need to be root to run this script

$ nft list ruleset
Operation not permitted (you must be root)

$ iptables -L -n
iptables v1.8.10 (nf_tables): Could not fetch rule set generation id: Permission denied (you must be root)
```

**All three firewall tools require root** to report their status at
all — this isn't a corner case, it's the default, expected outcome for
any unprivileged scan. `_detect_firewall` tries `ufw`, then `nft`, then
`iptables`, in that priority order (matching Ubuntu's own convention of
`ufw` as the user-facing front-end for the lower-level `nft`/`iptables`
layers), and reports `{"tool": None, "enabled": None}` if none are
usable — which, per the above, is the realistic common case for an
unprivileged scan, not a bug.

When a tool *is* usable, "enabled" means different things per tool:
`ufw status`'s first line literally says `Status: active` or
`Status: inactive` — a clean signal, but `_parse_ufw_status` deliberately
compares the exact word *after* the colon (`== "active"`) rather than
checking `"active" in line` — a naive substring check would incorrectly
match `"Status: inactive"` too, since `"inactive"` itself ends in the
six characters `"active"`. This was caught during this sprint's own
quality review, not assumed correct from the start — see this sprint's
Refactoring Opportunities / quality-review notes in `LOGS.md`.
`nft list ruleset`'s enabled state is inferred from whether any rules
are configured at all (empty output = no active ruleset). `iptables -L
-n` has no equally clean signal without inspecting individual rule
counts across every chain — genuine "deep networking diagnostics" this
task explicitly excludes — so `iptables`'s `enabled` is reported as
`None` (detected, but undeterminable) rather than guessed.

This entire best-effort path never contributes a `collection_errors`
entry, regardless of outcome — not detecting a firewall tool is a
normal, expected result for an unprivileged scan, not a collector
failure.

---

## Schema Alignment

`docs/snapshot_schema.md` Section 9's `interfaces` (`name`, `addresses`,
`state`) and `listening_ports` (`protocol`, `local_address`, `port`,
`pid`, `process_name`) shapes are extended, not replaced, by this
implementation:

- **`addresses` (one list) → `ipv4_addresses`/`ipv6_addresses` (two
  lists)** — a genuine improvement over the original schema, per this
  task's explicit "IPv4 addresses" and "IPv6 addresses" as separate
  requirements; a consumer that only cares about IPv4 no longer needs
  to inspect each address string to filter by family.
- **`default_route` and `firewall` are new** — neither existed in the
  original Section 9 draft at all, added per this task's explicit scope.

---

## Testing

- **Unit tests** (`tests/collectors/test_network.py`, 25 tests): every
  parser tested with literal sample text pulled from the Multipass VM
  (including the loopback `UNKNOWN`-state quirk, scoped and IPv6
  addresses, and a missing process field); `_merge_interfaces` tested
  for the combine case; `_parse_ufw_status` tested explicitly for both
  `active` and `inactive` (the substring bug described above would have
  passed the `active` case alone, so the `inactive` case is the one that
  actually guards against it); `collect()` tested end-to-end for the
  merged happy path, a link-command failure, and three firewall-detection
  branches (`ufw` active, `ufw` inactive, falling back to `nft`).
- **Integration test** (`tests/collectors/test_network_integration.py`,
  1 test): calls the real `collect()` with nothing mocked, automatically
  skipped unless running on Linux. Verified on the Multipass VM (real
  result: 2 interfaces both up, a real default route, 7 listening ports,
  no firewall tool detected as a non-root user — all as expected) as
  part of the full 193-test suite for this sprint.

---

## Collector Review Checklist

- [x] Exposes exactly one entry point: `collect(context: CollectorContext) -> CollectorResult`.
- [x] Never raises an unhandled exception — every command-based source is independently wrapped; firewall detection never raises or errors by design.
- [x] Interfaces are merged from two independent sources (`link` for state, `addr` for addresses) with graceful partial-failure handling, matching the established `disk.py`/`services.py` merge pattern.
- [x] Uses `nodeiq.core.runner.run_command` for every invocation — never raw `subprocess`.
- [x] Parsing is separated from command execution: every `_parse_*` function is pure, tested with literal sample text pulled from a real system.
- [x] Handles real, non-hypothetical address shapes (scoped `%interface` addresses, IPv6 brackets) correctly via `rpartition`, not naive splitting.
- [x] Process ownership degrades gracefully when this scan lacks the privilege to see it — never an error.
- [x] Firewall detection is explicitly best-effort and honestly reports `None`/undeterminable rather than guessing, consistent with "do not attempt deep networking diagnostics."
- [x] Field names use `snake_case`; no collector-invented redaction, logging, retries, or presentation logic.
- [x] Unit tests cover every parser, the interface merge, and `collect()` end-to-end (happy path, a source failure, and both firewall-detection branches); an integration test verifies real behavior on the Multipass VM.
