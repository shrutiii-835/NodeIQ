"""Collectors — one module per snapshot section, each gathering one
category of Linux system information (see docs/snapshot_schema.md).

`system.py` (Phase 3.2C) and `resource.py` (Phase 3.3) are built so far —
see docs/system_collector.md and docs/resource_collector.md. The rest are
still scaffolding. Every collector here uses `nodeiq.core.runner.run_command`
to execute external commands (or plain file I/O for `/proc`-backed data),
and will be run independently by the future scan coordinator in
`nodeiq.core.coordinator`.
"""
