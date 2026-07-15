"""Unit tests for nodeiq.collectors.processes.

All I/O is mocked or redirected to tmp_path — no test here depends on the
real machine's actual running processes, per PROJECT_RULES.md Section 11
and docs/collector_guidelines.md's Testing Expectations. See
tests/collectors/test_processes_integration.py for a test against the
real /proc on a real Linux system.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from nodeiq.collectors import processes
from nodeiq.core.collector import CollectorContext

# --- _parse_state --------------------------------------------------------


def test_parse_state_extracts_the_single_letter_code():
    assert processes._parse_state("State:\tS (sleeping)") == "S"


def test_parse_state_handles_zombie():
    assert processes._parse_state("State:\tZ (zombie)") == "Z"


def test_parse_state_raises_when_empty():
    with pytest.raises(ValueError):
        processes._parse_state("State:")


# --- _parse_vmrss ---------------------------------------------------------


def test_parse_vmrss_converts_kb_to_bytes():
    assert processes._parse_vmrss("VmRSS:\t    3120 kB") == 3120 * 1024


def test_parse_vmrss_raises_when_no_value():
    with pytest.raises(ValueError):
        processes._parse_vmrss("VmRSS:")


def test_parse_vmrss_raises_when_value_is_not_numeric():
    with pytest.raises(ValueError):
        processes._parse_vmrss("VmRSS:\tnotanumber kB")


# --- _parse_uid -------------------------------------------------------------


def test_parse_uid_takes_the_first_value():
    assert processes._parse_uid("Uid:\t1000\t1000\t1000\t1000") == 1000


def test_parse_uid_raises_when_no_value():
    with pytest.raises(ValueError):
        processes._parse_uid("Uid:")


# --- _parse_cmdline ---------------------------------------------------------


def test_parse_cmdline_joins_nul_separated_arguments():
    raw = "bash\0-c\0echo hello\0"
    assert processes._parse_cmdline(raw) == "bash -c echo hello"


def test_parse_cmdline_is_empty_for_a_kernel_thread():
    # Kernel threads (e.g. kthreadd) have an empty cmdline file — this must
    # be treated as a normal, expected case, not a parsing failure.
    assert processes._parse_cmdline("") == ""


# --- _parse_status -----------------------------------------------------------


def test_parse_status_extracts_all_three_fields():
    sample = (
        "Name:\tbash\n"
        "State:\tS (sleeping)\n"
        "Pid:\t2835\n"
        "Uid:\t1000\t1000\t1000\t1000\n"
        "VmRSS:\t    3120 kB\n"
        "Threads:\t1\n"
    )
    result = processes._parse_status(sample)
    assert result == {"state": "S", "memory_rss_bytes": 3120 * 1024, "uid": 1000}


def test_parse_status_defaults_memory_to_zero_when_vmrss_is_absent():
    # Kernel threads have no VmRSS line at all — no memory address space
    # to report — this must degrade gracefully, not raise.
    sample = "Name:\tkthreadd\nState:\tS (sleeping)\nUid:\t0\t0\t0\t0\n"
    result = processes._parse_status(sample)
    assert result["memory_rss_bytes"] == 0


def test_parse_status_raises_when_state_is_missing():
    sample = "Name:\tbash\nUid:\t1000\t1000\t1000\t1000\n"
    with pytest.raises(ValueError):
        processes._parse_status(sample)


def test_parse_status_raises_when_uid_is_missing():
    sample = "Name:\tbash\nState:\tS (sleeping)\n"
    with pytest.raises(ValueError):
        processes._parse_status(sample)


# --- _resolve_owner -----------------------------------------------------------


def test_resolve_owner_returns_username_when_lookup_succeeds(monkeypatch):
    class _FakePasswdEntry:
        pw_name = "shruti"

    monkeypatch.setattr(processes.pwd, "getpwuid", lambda uid: _FakePasswdEntry())

    assert processes._resolve_owner(1000) == "shruti"


def test_resolve_owner_falls_back_to_uid_string_when_lookup_fails(monkeypatch):
    def _raise_keyerror(uid):
        raise KeyError(uid)

    monkeypatch.setattr(processes.pwd, "getpwuid", _raise_keyerror)

    assert processes._resolve_owner(99999) == "99999"


# --- _discover_pids -----------------------------------------------------------


def test_discover_pids_returns_only_numeric_directory_names(tmp_path, monkeypatch):
    (tmp_path / "1").mkdir()
    (tmp_path / "42").mkdir()
    (tmp_path / "self").mkdir()  # not a PID — must be excluded
    (tmp_path / "meminfo").touch()  # a file, not a directory, not numeric

    monkeypatch.setattr(processes, "_PROC_ROOT", tmp_path)

    assert processes._discover_pids() == [1, 42]


def test_discover_pids_raises_when_proc_root_does_not_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(processes, "_PROC_ROOT", tmp_path / "does_not_exist")

    with pytest.raises(ValueError):
        processes._discover_pids()


# --- _read_process -----------------------------------------------------------


def _make_pid_dir(root: Path, pid: int, status: str, comm: str, cmdline: str) -> None:
    pid_dir = root / str(pid)
    pid_dir.mkdir()
    (pid_dir / "status").write_text(status)
    (pid_dir / "comm").write_text(comm)
    (pid_dir / "cmdline").write_text(cmdline)


def test_read_process_returns_a_complete_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(processes, "_PROC_ROOT", tmp_path)
    _make_pid_dir(
        tmp_path,
        2835,
        status=(
            "Name:\tbash\nState:\tS (sleeping)\n"
            "Uid:\t1000\t1000\t1000\t1000\nVmRSS:\t    3120 kB\n"
        ),
        comm="bash\n",
        cmdline="bash\0-c\0echo hi\0",
    )
    monkeypatch.setattr(processes, "_resolve_owner", lambda uid: "shruti")

    result = processes._read_process(2835)

    assert result == {
        "pid": 2835,
        "process_name": "bash",
        "memory_rss_bytes": 3120 * 1024,
        "owner": "shruti",
        "state": "S",
        "command": "bash -c echo hi",
    }


def test_read_process_returns_none_when_the_process_has_disappeared(tmp_path, monkeypatch):
    # No directory created for this PID at all — simulates a process that
    # exited between being discovered and being read.
    monkeypatch.setattr(processes, "_PROC_ROOT", tmp_path)

    assert processes._read_process(99999) is None


def test_read_process_returns_none_when_status_is_malformed(tmp_path, monkeypatch):
    monkeypatch.setattr(processes, "_PROC_ROOT", tmp_path)
    _make_pid_dir(
        tmp_path,
        123,
        status="Name:\tweird\n",  # missing State and Uid
        comm="weird\n",
        cmdline="",
    )

    assert processes._read_process(123) is None


# --- _summarize ----------------------------------------------------------------


def _proc(pid: int, memory_rss_bytes: int, state: str = "S") -> dict:
    return {
        "pid": pid,
        "process_name": f"proc{pid}",
        "memory_rss_bytes": memory_rss_bytes,
        "owner": "root",
        "state": state,
        "command": f"proc{pid}",
    }


def test_summarize_counts_zombies_and_blocked_processes():
    entries = [
        _proc(1, 100, state="S"),
        _proc(2, 200, state="Z"),
        _proc(3, 300, state="D"),
        _proc(4, 400, state="Z"),
    ]

    result = processes._summarize(entries)

    assert result["process_count"] == 4
    assert result["zombie_count"] == 2
    assert result["blocked_process_count"] == 1


def test_summarize_top_by_memory_is_sorted_descending_and_capped_at_ten():
    entries = [_proc(pid, memory_rss_bytes=pid * 10) for pid in range(1, 16)]

    result = processes._summarize(entries)

    assert len(result["top_by_memory"]) == 10
    memory_values = [p["memory_rss_bytes"] for p in result["top_by_memory"]]
    assert memory_values == sorted(memory_values, reverse=True)
    assert result["top_by_memory"][0]["pid"] == 15  # highest memory_rss_bytes


def test_summarize_handles_an_empty_process_list():
    result = processes._summarize([])

    assert result == {
        "process_count": 0,
        "zombie_count": 0,
        "blocked_process_count": 0,
        "top_by_memory": [],
    }


# --- collect() end-to-end ------------------------------------------------------


def _context() -> CollectorContext:
    return CollectorContext(scan_start_time=datetime.now(timezone.utc))


def test_collect_summarizes_every_discovered_process(monkeypatch):
    monkeypatch.setattr(processes, "_discover_pids", lambda: [1, 2, 3])
    fake_processes = {
        1: _proc(1, 1000, state="S"),
        2: _proc(2, 2000, state="Z"),
        3: _proc(3, 3000, state="D"),
    }
    monkeypatch.setattr(processes, "_read_process", lambda pid: fake_processes[pid])

    result = processes.collect(_context())

    assert result.collector_name == "processes"
    assert result.errors == []
    assert result.data["process_count"] == 3
    assert result.data["zombie_count"] == 1
    assert result.data["blocked_process_count"] == 1
    assert len(result.data["top_by_memory"]) == 3


def test_collect_skips_processes_that_disappear_mid_scan(monkeypatch):
    monkeypatch.setattr(processes, "_discover_pids", lambda: [1, 2, 3])

    def _fake_read(pid):
        if pid == 2:
            return None  # this one "disappeared"
        return _proc(pid, pid * 100)

    monkeypatch.setattr(processes, "_read_process", _fake_read)

    result = processes.collect(_context())

    assert result.errors == []  # a disappearing process is never an error
    assert result.data["process_count"] == 2


def test_collect_reports_an_error_when_proc_cannot_be_listed_at_all(monkeypatch):
    def _raise(*args, **kwargs):
        raise ValueError("could not list /proc: [Errno 2] No such file or directory")

    monkeypatch.setattr(processes, "_discover_pids", _raise)

    result = processes.collect(_context())

    assert result.data == {
        "process_count": None,
        "zombie_count": None,
        "blocked_process_count": None,
        "top_by_memory": None,
    }
    assert len(result.errors) == 1
    assert result.errors[0]["severity"] == "error"
    assert result.success is False
