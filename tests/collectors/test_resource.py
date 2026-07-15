"""Unit tests for nodeiq.collectors.resource.

Everything here is mocked (fake files via monkeypatched path constants) so
these tests never depend on the real state of the machine running them —
per PROJECT_RULES.md Section 11 and docs/collector_guidelines.md's Testing
Expectations. See tests/collectors/test_resource_integration.py for tests
that run against a real Linux system.
"""

from datetime import datetime, timezone

import pytest

from nodeiq.collectors import resource
from nodeiq.core.collector import CollectorContext

SAMPLE_MEMINFO = """\
MemTotal:         974844 kB
MemFree:          572636 kB
MemAvailable:     706648 kB
Buffers:           16796 kB
Cached:           179120 kB
SwapCached:            0 kB
SwapTotal:        2097152 kB
SwapFree:         2097152 kB
"""

SAMPLE_MEMINFO_NO_SWAP = """\
MemTotal:         974844 kB
MemAvailable:     706648 kB
SwapTotal:             0 kB
SwapFree:              0 kB
"""

SAMPLE_LOADAVG = "0.56 0.12 0.04 4/138 1069\n"


def _context() -> CollectorContext:
    return CollectorContext(scan_start_time=datetime.now(timezone.utc))


# --- Pure parsing functions: /proc/meminfo ----------------------------------


def test_parse_meminfo_extracts_required_fields():
    raw_kb = resource._parse_meminfo(SAMPLE_MEMINFO)

    assert raw_kb == {
        "MemTotal": 974844,
        "MemAvailable": 706648,
        "SwapTotal": 2097152,
        "SwapFree": 2097152,
    }


def test_parse_meminfo_raises_when_a_required_field_is_missing():
    raw = "MemTotal:  974844 kB\nMemAvailable:  706648 kB\n"

    with pytest.raises(ValueError):
        resource._parse_meminfo(raw)


def test_parse_meminfo_raises_on_non_numeric_value():
    raw = SAMPLE_MEMINFO.replace("974844", "not-a-number")

    with pytest.raises(ValueError):
        resource._parse_meminfo(raw)


# --- Pure computation: memory/swap fields -----------------------------------


def test_compute_memory_fields_computes_bytes_and_percentages():
    raw_kb = {
        "MemTotal": 974844,
        "MemAvailable": 706648,
        "SwapTotal": 2097152,
        "SwapFree": 2097152,
    }

    fields = resource._compute_memory_fields(raw_kb)

    assert fields["memory_used_bytes"] == (974844 - 706648) * 1024
    assert fields["memory_available_bytes"] == 706648 * 1024
    assert fields["memory_usage_percent"] == pytest.approx(27.51, abs=0.01)
    assert fields["swap_used_bytes"] == 0
    assert fields["swap_usage_percent"] == 0.0


def test_compute_memory_fields_handles_zero_swap_total_without_error():
    raw_kb = {
        "MemTotal": 974844,
        "MemAvailable": 706648,
        "SwapTotal": 0,
        "SwapFree": 0,
    }

    fields = resource._compute_memory_fields(raw_kb)

    assert fields["swap_used_bytes"] == 0
    assert fields["swap_usage_percent"] == 0.0


def test_percent_returns_zero_when_whole_is_zero():
    assert resource._percent(part=5, whole=0) == 0.0


def test_percent_rounds_to_two_decimal_places():
    assert resource._percent(part=1, whole=3) == 33.33


# --- Pure parsing functions: /proc/loadavg ----------------------------------


def test_parse_loadavg_extracts_three_values():
    fields = resource._parse_loadavg(SAMPLE_LOADAVG)

    assert fields == {
        "load_average_1m": 0.56,
        "load_average_5m": 0.12,
        "load_average_15m": 0.04,
    }


def test_parse_loadavg_raises_on_too_few_tokens():
    with pytest.raises(ValueError):
        resource._parse_loadavg("0.56 0.12\n")


def test_parse_loadavg_raises_on_non_numeric_values():
    with pytest.raises(ValueError):
        resource._parse_loadavg("not numeric at all\n")


# --- File-based getters -------------------------------------------------------


def test_get_memory_fields_reads_the_configured_path(tmp_path, monkeypatch):
    fake_path = tmp_path / "meminfo"
    fake_path.write_text(SAMPLE_MEMINFO_NO_SWAP)
    monkeypatch.setattr(resource, "_MEMINFO_PATH", fake_path)

    fields = resource._get_memory_fields()

    assert fields["memory_available_bytes"] == 706648 * 1024
    assert fields["swap_usage_percent"] == 0.0


def test_get_memory_fields_raises_when_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(resource, "_MEMINFO_PATH", tmp_path / "does-not-exist")

    with pytest.raises(ValueError):
        resource._get_memory_fields()


def test_get_load_average_fields_reads_the_configured_path(tmp_path, monkeypatch):
    fake_path = tmp_path / "loadavg"
    fake_path.write_text(SAMPLE_LOADAVG)
    monkeypatch.setattr(resource, "_LOADAVG_PATH", fake_path)

    fields = resource._get_load_average_fields()

    assert fields["load_average_1m"] == 0.56


def test_get_load_average_fields_raises_when_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(resource, "_LOADAVG_PATH", tmp_path / "does-not-exist")

    with pytest.raises(ValueError):
        resource._get_load_average_fields()


# --- collect() end to end -----------------------------------------------------


def test_collect_returns_all_fields_when_everything_succeeds(tmp_path, monkeypatch):
    meminfo_path = tmp_path / "meminfo"
    meminfo_path.write_text(SAMPLE_MEMINFO)
    monkeypatch.setattr(resource, "_MEMINFO_PATH", meminfo_path)

    loadavg_path = tmp_path / "loadavg"
    loadavg_path.write_text(SAMPLE_LOADAVG)
    monkeypatch.setattr(resource, "_LOADAVG_PATH", loadavg_path)

    result = resource.collect(_context())

    assert result.collector_name == "resource"
    assert result.errors == []
    assert result.success is True
    assert result.data["memory_used_bytes"] == (974844 - 706648) * 1024
    assert result.data["load_average_1m"] == 0.56
    assert result.duration_ms >= 0


def test_collect_continues_when_memory_source_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(resource, "_MEMINFO_PATH", tmp_path / "does-not-exist")

    loadavg_path = tmp_path / "loadavg"
    loadavg_path.write_text(SAMPLE_LOADAVG)
    monkeypatch.setattr(resource, "_LOADAVG_PATH", loadavg_path)

    result = resource.collect(_context())

    assert result.data["memory_used_bytes"] is None
    assert result.data["swap_usage_percent"] is None
    assert result.data["load_average_1m"] == 0.56
    assert len(result.errors) == 1
    assert result.success is False


def test_collect_continues_when_load_average_source_fails(tmp_path, monkeypatch):
    meminfo_path = tmp_path / "meminfo"
    meminfo_path.write_text(SAMPLE_MEMINFO)
    monkeypatch.setattr(resource, "_MEMINFO_PATH", meminfo_path)

    monkeypatch.setattr(resource, "_LOADAVG_PATH", tmp_path / "does-not-exist")

    result = resource.collect(_context())

    assert result.data["load_average_1m"] is None
    assert result.data["load_average_5m"] is None
    assert result.data["load_average_15m"] is None
    assert result.data["memory_used_bytes"] == (974844 - 706648) * 1024
    assert len(result.errors) == 1
    assert result.success is False
