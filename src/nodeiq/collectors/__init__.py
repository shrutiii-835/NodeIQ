"""Collectors — one module per snapshot section, each gathering one
category of Linux system information (see docs/snapshot_schema.md).

`system.py` (Phase 3.2C), `cpu_memory.py` (Phase 3.3, renamed from
`resource.py` in Phase 3.4), `processes.py` (Phase 3.5B), and `disk.py`
(Phase 3.6) are built so far — see docs/system_collector.md,
docs/cpu_memory_collector.md, docs/process_collector.md, and
docs/disk_collector.md. The rest are still scaffolding. Every collector
here uses `nodeiq.core.runner.run_command` to execute external commands
(or plain file I/O for `/proc`-backed data), and is run independently by
the scan coordinator in `nodeiq.core.coordinator`.
"""
