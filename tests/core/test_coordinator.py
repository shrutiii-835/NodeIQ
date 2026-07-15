"""Unit tests for nodeiq.core.coordinator.run_scan.

Everything here uses fake "collector modules" (simple objects with a
`collect(context)` method and a `__name__` attribute, standing in for a
real collector module) instead of the real `system`/`cpu_memory`
collectors — so these tests verify the coordinator's own orchestration
logic (running collectors, aggregating errors, building metadata) without
depending on the real machine's actual hostname, memory, or load. See
tests/core/test_coordinator_integration.py for a test against the real
collectors.
"""

import pytest

from nodeiq import __version__ as nodeiq_version
from nodeiq.core import coordinator
from nodeiq.core.collector import CollectorResult


class _FakeCollectorModule:
    """Stands in for a real collector module: something with a `collect`
    function and a dotted `__name__`, which is all `run_scan` needs."""

    def __init__(self, name: str, collect_fn):
        self.__name__ = f"nodeiq.collectors.{name}"
        self.collect = collect_fn


def _succeeding_collector(name: str, data: dict, errors: list | None = None):
    def collect(context):
        return CollectorResult(
            collector_name=name, data=data, errors=errors or [], duration_ms=1.0
        )

    return _FakeCollectorModule(name, collect)


def _crashing_collector(name: str, exception: Exception):
    def collect(context):
        raise exception

    return _FakeCollectorModule(name, collect)


# --- run_scan(): basic orchestration -----------------------------------------


def test_run_scan_executes_every_registered_collector(monkeypatch):
    # Uses "system"/"cpu_memory"/"processes" as the fake names (not
    # "alpha"/"beta"/"gamma") so this still satisfies _validate_snapshot's
    # required-section check — that check is exercised separately below.
    calls = []

    def make_tracking_collector(name):
        def collect(context):
            calls.append(name)
            return CollectorResult(
                collector_name=name, data={}, errors=[], duration_ms=1.0
            )

        return _FakeCollectorModule(name, collect)

    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            make_tracking_collector("system"),
            make_tracking_collector("cpu_memory"),
            make_tracking_collector("processes"),
        ],
    )

    coordinator.run_scan()

    assert calls == ["system", "cpu_memory", "processes"]


def test_run_scan_assembles_data_from_every_collector_under_its_own_name(monkeypatch):
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _succeeding_collector("system", {"hostname": "myhost"}),
            _succeeding_collector("cpu_memory", {"memory_used_bytes": 123}),
            _succeeding_collector("processes", {"process_count": 42}),
        ],
    )

    snapshot = coordinator.run_scan()

    assert snapshot["system"] == {"hostname": "myhost"}
    assert snapshot["cpu_memory"] == {"memory_used_bytes": 123}
    assert snapshot["processes"] == {"process_count": 42}


def test_run_scan_returns_expected_top_level_sections(monkeypatch):
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _succeeding_collector("system", {}),
            _succeeding_collector("cpu_memory", {}),
            _succeeding_collector("processes", {}),
        ],
    )

    snapshot = coordinator.run_scan()

    assert set(snapshot.keys()) == {
        "metadata",
        "collection_errors",
        "system",
        "cpu_memory",
        "processes",
    }


# --- collection_errors aggregation -------------------------------------------


def test_run_scan_aggregates_errors_reported_by_a_collector(monkeypatch):
    error_entry = {
        "message": "could not read something",
        "severity": "error",
        "exception_type": "ValueError",
    }
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _succeeding_collector("system", {"hostname": None}, errors=[error_entry]),
            _succeeding_collector("cpu_memory", {}),
            _succeeding_collector("processes", {}),
        ],
    )

    snapshot = coordinator.run_scan()

    assert snapshot["collection_errors"] == {"system": [error_entry]}


def test_run_scan_collection_errors_is_empty_when_nothing_went_wrong(monkeypatch):
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _succeeding_collector("system", {}),
            _succeeding_collector("cpu_memory", {}),
            _succeeding_collector("processes", {}),
        ],
    )

    snapshot = coordinator.run_scan()

    assert snapshot["collection_errors"] == {}


def test_run_scan_continues_and_records_a_crash_when_a_collector_raises(monkeypatch):
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _crashing_collector("system", RuntimeError("boom")),
            _succeeding_collector("cpu_memory", {"memory_used_bytes": 123}),
            _succeeding_collector("processes", {}),
        ],
    )

    snapshot = coordinator.run_scan()

    assert snapshot["system"] is None
    assert snapshot["cpu_memory"] == {"memory_used_bytes": 123}
    assert len(snapshot["collection_errors"]["system"]) == 1
    assert snapshot["collection_errors"]["system"][0]["exception_type"] == "RuntimeError"
    assert "boom" in snapshot["collection_errors"]["system"][0]["message"]


# --- metadata -----------------------------------------------------------------


def test_run_scan_populates_metadata_fields(monkeypatch):
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _succeeding_collector("system", {"hostname": "myhost"}),
            _succeeding_collector("cpu_memory", {}),
            _succeeding_collector("processes", {}),
        ],
    )

    snapshot = coordinator.run_scan()
    metadata = snapshot["metadata"]

    assert metadata["collector_count"] == 3
    assert metadata["nodeiq_version"] == nodeiq_version
    assert metadata["hostname"] == "myhost"
    assert metadata["scan_duration_ms"] >= 0
    assert isinstance(metadata["scan_timestamp"], str)


def test_run_scan_metadata_hostname_is_none_when_system_data_has_no_hostname(
    monkeypatch,
):
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _succeeding_collector("system", {}),
            _succeeding_collector("cpu_memory", {}),
            _succeeding_collector("processes", {}),
        ],
    )

    snapshot = coordinator.run_scan()

    assert snapshot["metadata"]["hostname"] is None


def test_run_scan_metadata_hostname_is_none_when_system_collector_crashes(monkeypatch):
    monkeypatch.setattr(
        coordinator,
        "_REGISTERED_COLLECTORS",
        [
            _crashing_collector("system", RuntimeError("boom")),
            _succeeding_collector("cpu_memory", {}),
            _succeeding_collector("processes", {}),
        ],
    )

    snapshot = coordinator.run_scan()

    assert snapshot["metadata"]["hostname"] is None


# --- snapshot validation -------------------------------------------------------


def test_validate_snapshot_passes_when_all_required_sections_are_present():
    coordinator._validate_snapshot(
        {
            "metadata": {},
            "system": {},
            "cpu_memory": {},
            "processes": {},
            "collection_errors": {},
        }
    )


def test_validate_snapshot_raises_when_a_required_section_is_missing():
    with pytest.raises(ValueError, match="cpu_memory"):
        coordinator._validate_snapshot(
            {"metadata": {}, "system": {}, "collection_errors": {}}
        )
