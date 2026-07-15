# NodeIQ

NodeIQ is a Python command-line tool that answers natural-language questions
about the health and state of a Linux server, using **real system data** —
not guesses, and not hallucinated facts.

You ask questions like:

- "What service failed?"
- "What is consuming memory?"
- "What ports are open?"
- "What cron jobs exist?"
- "Why might disk space be running out?"

NodeIQ collects real evidence from the Linux system, and only then hands that
evidence to an LLM to interpret and summarize. The LLM never runs commands
itself and never invents facts that aren't in the evidence.

---

## Project Documentation

This project is developed across many sessions, so it leans heavily on
written documentation to stay consistent. Start here:

- [CONTEXT.md](CONTEXT.md) — permanent architectural context: objective,
  architecture, snapshot and safety philosophy, design principles
- [PROJECT_RULES.md](PROJECT_RULES.md) — permanent engineering standards:
  style, error handling, testing, git workflow, Definition of Done
- [CHECKLIST.md](CHECKLIST.md) — phase-by-phase progress tracker
- [DECISIONS.md](DECISIONS.md) — Architecture Decision Record (ADR log)
- [ROADMAP.md](ROADMAP.md) — high-level milestones, current and future
- [LEARNING_NOTES.md](LEARNING_NOTES.md) — beginner-friendly explanations of
  every concept introduced along the way
- [LOGS.md](LOGS.md) — append-only development diary

---

## Why NodeIQ exists

Diagnosing a Linux server usually means running a dozen different commands
(`systemctl`, `journalctl`, `df`, `ss`, `crontab -l`, ...), mentally piecing
the output together, and figuring out what's actually wrong. NodeIQ automates
the "gather evidence" step and adds a natural-language layer on top, so you
can ask plain-English questions and get answers grounded in what the system
actually reports.

---

## Architecture

NodeIQ is built around a **snapshot-first** design. This is a deliberate,
non-negotiable architectural choice — see [CONTEXT.md](CONTEXT.md) for the
full reasoning. In short: the tool never lets an LLM run commands live on
your system. Instead, it works in two clearly separated layers:

### Layer 1 — Data Collection

Small, independent "collectors" gather facts from the Linux system using
standard tools and files:

- `systemctl` — services and their status
- `journalctl` — system and service logs
- `ss` / `ip` — network connections and interfaces
- `df` / `du` / `findmnt` — disk usage and mounted filesystems
- `/proc` — CPU, memory, and process information
- `crontab`, systemd timers — scheduled jobs
- `iptables` / `nftables` / `ufw` — firewall rules
- filesystem metadata — permissions and ownership

Each collector writes its findings into a single structured JSON document
called a **snapshot**. Collectors are independent: if one fails (for example,
a firewall tool isn't installed), the rest of the scan still completes.

### Layer 2 — AI Interpretation

The LLM is given **only** the JSON snapshot plus the user's question. It:

- interprets the evidence,
- never executes arbitrary shell commands,
- never invents facts that aren't present in the snapshot.

### The pipeline

```
scan    → collect Linux system information → store structured JSON snapshot
report  → summarize an existing snapshot into a human-readable report
ask     → load a snapshot, send it + a question to the LLM, get an answer
```

---

## Planned Features

- `nodeiq scan` — collect a full snapshot of system state into JSON
- `nodeiq report` — print a human-readable summary of the latest snapshot
- `nodeiq ask "<question>"` — ask a natural-language question, answered
  strictly from evidence in the snapshot
- Collectors for: system metadata, CPU, memory, processes, disk, inodes,
  services, logs, network, scheduled jobs, and permissions
- Robust handling of partial failures, timeouts, missing tools, and secret
  redaction (e.g., not leaking credentials found in config files)

---

## Folder Structure

```
NodeIQ/
├── README.md            # This file — public project documentation
├── CONTEXT.md           # Permanent project context and philosophy
├── PROJECT_RULES.md      # Engineering standards and conventions
├── LOGS.md               # Append-only development diary
├── requirements.txt      # Python dependencies
├── pyproject.toml        # pytest configuration
├── .gitignore
├── docs/                 # Design notes, schemas, and architecture docs
│   ├── snapshot_schema.md
│   ├── data_model_design.md
│   ├── architecture.md
│   ├── collector_guidelines.md
│   ├── system_collector.md
│   └── resource_collector.md
├── snapshots/            # JSON snapshots produced by `nodeiq scan`
├── src/
│   └── nodeiq/           # Application source code (Python package)
│       ├── core/         # Shared execution infrastructure (runner, etc.)
│       └── collectors/   # One module per snapshot section — system.py
│                         # and resource.py are built; more to come
└── tests/                # Automated tests (pytest), mirroring src/nodeiq/
```

---

## Development Roadmap

NodeIQ is built in strict, incremental phases. We do not skip ahead.

1. **Project architecture** — repository structure and documentation (this phase)
2. **Data model** — define the shape of a snapshot (the JSON contract)
3. **Collectors** — implement each data collector one at a time
4. **Report generation** — turn a snapshot into a human-readable report
5. **CLI** — wire up `scan`, `report`, and `ask` commands
6. **LLM integration** — connect the `ask` command to a real LLM
7. **Robustness** — timeouts, partial failures, secret redaction, edge cases
8. **Testing** — validation and demo preparation

See [CONTEXT.md](CONTEXT.md) for the full architectural reasoning behind
these phases, and [PROJECT_RULES.md](PROJECT_RULES.md) for coding standards.

---

## Future Improvements

Ideas that are explicitly **out of scope** for now, but worth revisiting once
the core pipeline is solid:

- Support for remote hosts (currently single-server, local-only)
- Historical snapshot comparison ("what changed since yesterday?")
- Alerting / scheduled scans via cron or systemd timers
- Multiple LLM provider support
- Web-based report viewer

---

## Setup Instructions (placeholder)

> The `scan`/`report`/`ask` commands don't exist yet (Phase 5+), but the
> test suite for the code built so far does.

```bash
# Clone the repository
git clone <repo-url>
cd NodeIQ

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the test suite
python -m pytest

# (Future) Run a scan
python -m nodeiq scan
```
