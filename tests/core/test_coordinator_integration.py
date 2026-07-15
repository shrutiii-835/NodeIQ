"""End-to-end integration test for nodeiq.core.coordinator.run_scan.

Unlike test_coordinator.py, nothing here is faked — this calls the real
`run_scan()`, which runs the real `system`, `cpu_memory`, `processes`,
`disk`, `services`, `scheduled_jobs`, and `permissions` collectors
against the real machine. That only makes sense on a real Linux system
(see DECISIONS.md ADR-002: development and integration testing happens
in a Multipass Ubuntu VM), so this test is skipped automatically
everywhere else rather than failing for an unrelated reason (e.g. macOS
has no `/proc` or `/etc/os-release`, so several fields would
legitimately come back `None` there — not a bug, just not what this test
is checking).
"""

import platform

import pytest

from nodeiq.core.coordinator import run_scan

pytestmark = pytest.mark.skipif(
    platform.system() != "Linux",
    reason="requires a real Linux system (see DECISIONS.md ADR-002); "
    "run this inside the Multipass Ubuntu VM",
)


def test_run_scan_produces_a_complete_snapshot_on_a_real_linux_system():
    snapshot = run_scan()

    # All seven collectors ran and contributed their own section.
    assert set(snapshot.keys()) == {
        "metadata",
        "collection_errors",
        "system",
        "cpu_memory",
        "processes",
        "disk",
        "services",
        "scheduled_jobs",
        "permissions",
    }

    # On a healthy VM, every collector should succeed completely.
    assert snapshot["collection_errors"] == {}

    # metadata is populated with real values.
    metadata = snapshot["metadata"]
    assert metadata["collector_count"] == 7
    assert metadata["scan_duration_ms"] >= 0
    assert metadata["hostname"] == snapshot["system"]["hostname"]
    assert metadata["nodeiq_version"]

    # system and cpu_memory sections have real, sane data.
    assert snapshot["system"]["hostname"]
    assert snapshot["system"]["operating_system"]
    assert snapshot["system"]["kernel_version"]
    assert snapshot["system"]["architecture"]
    assert snapshot["system"]["uptime_seconds"] > 0

    assert snapshot["cpu_memory"]["memory_used_bytes"] > 0
    assert snapshot["cpu_memory"]["memory_available_bytes"] >= 0
    assert isinstance(snapshot["cpu_memory"]["load_average_1m"], float)

    # processes section has real, sane data.
    processes = snapshot["processes"]
    assert processes["process_count"] > 0
    assert processes["zombie_count"] >= 0
    assert processes["blocked_process_count"] >= 0
    assert len(processes["top_by_memory"]) <= 10

    # disk section has real, sane data.
    disk = snapshot["disk"]
    assert len(disk["filesystems"]) >= 1
    assert 0.0 <= disk["highest_disk_usage_percent"] <= 100.0

    # services section has real, sane data.
    services = snapshot["services"]
    assert services["systemd_available"] is True
    assert services["running_services_count"] > 0

    # scheduled_jobs section has real, sane data.
    scheduled_jobs = snapshot["scheduled_jobs"]
    assert scheduled_jobs["cron_job_count"] == len(scheduled_jobs["cron_jobs"])
    assert scheduled_jobs["timer_count"] == len(scheduled_jobs["systemd_timers"])

    # permissions section has real, sane data.
    permissions = snapshot["permissions"]
    assert len(permissions["checked_paths"]) > 0
