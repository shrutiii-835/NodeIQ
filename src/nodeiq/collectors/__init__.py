"""Collectors — one module per snapshot section, each gathering one
category of Linux system information (see docs/snapshot_schema.md).

`system.py` is the first collector (Phase 3.2C) — see
docs/system_collector.md. The remaining eight are still scaffolding.
Every collector here uses `nodeiq.core.runner.run_command` to execute
external commands (or plain file I/O for `/proc`-backed data), and will
be run independently by the future scan coordinator in
`nodeiq.core.coordinator`.
"""
