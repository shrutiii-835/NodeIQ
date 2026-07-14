"""Collectors — one module per snapshot section, each gathering one
category of Linux system information (see docs/snapshot_schema.md).

No collector modules exist yet; this package is scaffolding for Phase 3.2.
Every collector built here will use `nodeiq.core.runner.run_command` to
execute external commands, and will be run independently by the future
scan coordinator in `nodeiq.core.coordinator`.
"""
