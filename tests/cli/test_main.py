"""Unit tests for nodeiq.cli.main.

These are integration-style tests against fixture snapshots and mocked
backend functions, per PROJECT_RULES.md Section 11 — none depend on the
real machine's state or the real filesystem beyond what a test itself
sets up.
"""

import pytest

from nodeiq.cli import main as cli_main
from nodeiq.core.exceptions import SnapshotError


def _fake_snapshot(**overrides) -> dict:
    """A small, hand-built snapshot — enough sections to exercise the
    CLI meaningfully without needing all 9 (missing sections are simply
    "unavailable", which nodeiq.summary already handles gracefully).
    """
    snapshot = {
        "metadata": {
            "scan_timestamp": "2026-07-15T08:35:17.525799+00:00",
            "scan_duration_ms": 12.3,
            "collector_count": 9,
            "nodeiq_version": "0.1.0",
            "hostname": "test-host",
        },
        "collection_errors": {},
        "system": {
            "hostname": "test-host",
            "operating_system": "Test OS 1.0",
            "kernel_version": "6.8.0-test",
            "architecture": "x86_64",
            "uptime_seconds": 3600.0,
        },
        "disk": {
            "filesystems": [{"mount_point": "/", "usage_percent": 10.0}],
            "highest_disk_usage_percent": 10.0,
            "highest_inode_usage_percent": 5.0,
        },
    }
    snapshot.update(overrides)
    return snapshot


# --- build_parser() ----------------------------------------------------------------


def test_parses_scan_command():
    args = cli_main.build_parser().parse_args(["scan"])
    assert args.command == "scan"


def test_parses_report_with_defaults():
    args = cli_main.build_parser().parse_args(["report"])
    assert args.command == "report"
    assert args.section is None
    assert args.snapshot is None
    assert args.fresh is False


def test_parses_report_with_section():
    args = cli_main.build_parser().parse_args(["report", "--section", "disk"])
    assert args.section == "disk"


def test_parses_report_with_snapshot_path():
    args = cli_main.build_parser().parse_args(["report", "--snapshot", "some/path.json"])
    assert args.snapshot == "some/path.json"


def test_parses_report_with_fresh():
    args = cli_main.build_parser().parse_args(["report", "--fresh"])
    assert args.fresh is True


def test_report_snapshot_and_fresh_are_mutually_exclusive(capsys):
    with pytest.raises(SystemExit):
        cli_main.build_parser().parse_args(["report", "--snapshot", "x.json", "--fresh"])
    assert "not allowed" in capsys.readouterr().err


def test_parses_ask_with_question():
    args = cli_main.build_parser().parse_args(["ask", "what failed?"])
    assert args.command == "ask"
    assert args.question == "what failed?"


def test_parses_ask_without_question():
    args = cli_main.build_parser().parse_args(["ask"])
    assert args.question is None


def test_no_command_is_an_invalid_argument(capsys):
    with pytest.raises(SystemExit):
        cli_main.build_parser().parse_args([])


def test_unknown_command_is_an_invalid_argument():
    with pytest.raises(SystemExit):
        cli_main.build_parser().parse_args(["bogus"])


# --- main() dispatch ----------------------------------------------------------------


def test_main_dispatches_to_scan(monkeypatch, capsys):
    snapshot = _fake_snapshot()
    monkeypatch.setattr(cli_main, "run_scan", lambda: snapshot)
    monkeypatch.setattr(cli_main, "save_snapshot", lambda snap: "snapshots/fake.json")

    exit_code = cli_main.main(["scan"])

    assert exit_code == cli_main.EXIT_OK
    assert "Snapshot saved to: snapshots/fake.json" in capsys.readouterr().out


def test_main_dispatches_to_report(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "load_latest_snapshot", lambda: _fake_snapshot())

    exit_code = cli_main.main(["report"])

    assert exit_code == cli_main.EXIT_OK
    assert "NodeIQ Report" in capsys.readouterr().out


def test_main_dispatches_to_ask(capsys):
    exit_code = cli_main.main(["ask", "anything"])

    assert exit_code == cli_main.EXIT_OK
    assert "Phase 6" in capsys.readouterr().out


# --- scan command ---------------------------------------------------------------------


def test_scan_command_prints_collectors_executed_and_snapshot_location(monkeypatch, capsys):
    snapshot = _fake_snapshot(collection_errors={})
    monkeypatch.setattr(cli_main, "run_scan", lambda: snapshot)
    monkeypatch.setattr(cli_main, "save_snapshot", lambda snap: "snapshots/snapshot_x.json")

    exit_code = cli_main._cmd_scan()

    out = capsys.readouterr().out
    assert exit_code == cli_main.EXIT_OK
    assert "9/9 collectors succeeded" in out
    assert "snapshots/snapshot_x.json" in out


def test_scan_command_reports_partial_collector_failure(monkeypatch, capsys):
    snapshot = _fake_snapshot(collection_errors={"services": [{"message": "boom"}]})
    monkeypatch.setattr(cli_main, "run_scan", lambda: snapshot)
    monkeypatch.setattr(cli_main, "save_snapshot", lambda snap: "snapshots/snapshot_x.json")

    exit_code = cli_main._cmd_scan()

    out = capsys.readouterr().out
    assert exit_code == cli_main.EXIT_OK
    assert "8/9 collectors succeeded" in out
    assert "1 error(s)" in out


def test_scan_command_handles_save_failure(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "run_scan", lambda: _fake_snapshot())

    def _boom(snapshot):
        raise OSError("disk full")

    monkeypatch.setattr(cli_main, "save_snapshot", _boom)

    exit_code = cli_main._cmd_scan()

    assert exit_code == cli_main.EXIT_INTERNAL_FAILURE
    assert "Could not complete scan" in capsys.readouterr().err


# --- report command ---------------------------------------------------------------------


def test_report_command_default_loads_latest_snapshot(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "load_latest_snapshot", lambda: _fake_snapshot())
    args = cli_main.build_parser().parse_args(["report"])

    exit_code = cli_main._cmd_report(args)

    out = capsys.readouterr().out
    assert exit_code == cli_main.EXIT_OK
    assert "NodeIQ Report" in out
    assert "test-host" in out
    assert "System [HEALTHY]" in out


def test_report_command_missing_snapshot(monkeypatch, capsys):
    def _raise(*a, **k):
        raise SnapshotError("no snapshot files found in snapshots")

    monkeypatch.setattr(cli_main, "load_latest_snapshot", _raise)
    args = cli_main.build_parser().parse_args(["report"])

    exit_code = cli_main._cmd_report(args)

    assert exit_code == cli_main.EXIT_NO_SNAPSHOT
    assert "No snapshot available" in capsys.readouterr().err


def test_report_command_malformed_snapshot(monkeypatch, capsys):
    def _raise(path):
        raise SnapshotError(f"snapshot {path} is not valid JSON")

    monkeypatch.setattr(cli_main, "load_snapshot", _raise)
    args = cli_main.build_parser().parse_args(["report", "--snapshot", "bad.json"])

    exit_code = cli_main._cmd_report(args)

    assert exit_code == cli_main.EXIT_NO_SNAPSHOT
    assert "not valid JSON" in capsys.readouterr().err


def test_report_command_uses_snapshot_flag(monkeypatch):
    seen_paths = []
    monkeypatch.setattr(
        cli_main, "load_snapshot", lambda path: seen_paths.append(path) or _fake_snapshot()
    )
    args = cli_main.build_parser().parse_args(["report", "--snapshot", "some/path.json"])

    cli_main._cmd_report(args)

    assert seen_paths == ["some/path.json"]


def test_report_command_fresh_scans_then_reports(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "run_scan", lambda: _fake_snapshot())
    monkeypatch.setattr(cli_main, "save_snapshot", lambda snap: "snapshots/fresh.json")
    args = cli_main.build_parser().parse_args(["report", "--fresh"])

    exit_code = cli_main._cmd_report(args)

    out = capsys.readouterr().out
    assert exit_code == cli_main.EXIT_OK
    assert "Snapshot saved to: snapshots/fresh.json" in out
    assert "NodeIQ Report" in out
    assert out.index("Snapshot saved to") < out.index("NodeIQ Report")


def test_report_command_fresh_handles_scan_failure(monkeypatch, capsys):
    def _boom():
        raise RuntimeError("scan crashed")

    monkeypatch.setattr(cli_main, "run_scan", _boom)
    args = cli_main.build_parser().parse_args(["report", "--fresh"])

    exit_code = cli_main._cmd_report(args)

    assert exit_code == cli_main.EXIT_INTERNAL_FAILURE
    assert "Could not complete report" in capsys.readouterr().err


def test_report_command_valid_section(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "load_latest_snapshot", lambda: _fake_snapshot())
    args = cli_main.build_parser().parse_args(["report", "--section", "disk"])

    exit_code = cli_main._cmd_report(args)

    out = capsys.readouterr().out
    assert exit_code == cli_main.EXIT_OK
    assert "Disk [HEALTHY]" in out
    assert "System" not in out


def test_report_command_invalid_section(monkeypatch, capsys):
    monkeypatch.setattr(cli_main, "load_latest_snapshot", lambda: _fake_snapshot())
    args = cli_main.build_parser().parse_args(["report", "--section", "not-a-real-section"])

    exit_code = cli_main._cmd_report(args)

    err = capsys.readouterr().err
    assert exit_code == cli_main.EXIT_INVALID_ARGS
    assert "Unknown section 'not-a-real-section'" in err
    assert "disk" in err
    assert "system" in err


# --- ask placeholder ---------------------------------------------------------------------


def test_ask_command_with_question_prints_placeholder(capsys):
    args = cli_main.build_parser().parse_args(["ask", "is anything wrong?"])

    exit_code = cli_main._cmd_ask(args)

    out = capsys.readouterr().out
    assert exit_code == cli_main.EXIT_OK
    assert "Phase 6" in out
    assert "is anything wrong?" not in out  # placeholder never echoes/answers the question


def test_ask_command_without_question_prints_placeholder(capsys):
    args = cli_main.build_parser().parse_args(["ask"])

    exit_code = cli_main._cmd_ask(args)

    assert exit_code == cli_main.EXIT_OK
    assert "Phase 6" in capsys.readouterr().out


# --- _scan_confirmation() (pure helper) ---------------------------------------------------


def test_scan_confirmation_all_succeeded():
    snapshot = _fake_snapshot(collection_errors={})
    line = cli_main._scan_confirmation(snapshot, "snapshots/x.json")
    assert "9/9 collectors succeeded." in line
    assert "error" not in line
    assert "Snapshot saved to: snapshots/x.json" in line


def test_scan_confirmation_partial_failure():
    snapshot = _fake_snapshot(collection_errors={"network": [{"message": "boom"}], "logs": [{"message": "boom"}]})
    line = cli_main._scan_confirmation(snapshot, "snapshots/x.json")
    assert "7/9 collectors succeeded" in line
    assert "2 error(s)" in line


def test_scan_confirmation_missing_collector_count():
    snapshot = _fake_snapshot(metadata={})
    line = cli_main._scan_confirmation(snapshot, "snapshots/x.json")
    assert line.startswith("Scan complete.")


# --- _select_section() (pure helper) ---------------------------------------------------


def test_select_section_returns_only_requested_section(monkeypatch):
    from nodeiq.summary import summarize_snapshot

    summary = summarize_snapshot(_fake_snapshot())
    filtered = cli_main._select_section(summary, "disk")

    assert list(filtered["sections"].keys()) == ["disk"]
    assert filtered["hostname"] == summary["hostname"]


def test_select_section_unknown_name_returns_none():
    from nodeiq.summary import summarize_snapshot

    summary = summarize_snapshot(_fake_snapshot())
    assert cli_main._select_section(summary, "not-a-section") is None


def test_select_section_does_not_mutate_original():
    import copy

    from nodeiq.summary import summarize_snapshot

    summary = summarize_snapshot(_fake_snapshot())
    before = copy.deepcopy(summary)
    cli_main._select_section(summary, "disk")

    assert summary == before
