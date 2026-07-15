"""Unit tests for nodeiq.collectors.permissions.

All filesystem access is redirected to tmp_path — no test here depends
on the real machine's actual /etc/passwd, /etc/shadow, etc., per
PROJECT_RULES.md Section 11 and docs/collector_guidelines.md's Testing
Expectations. See tests/collectors/test_permissions_integration.py for
a test against the real paths on a real Linux system.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from nodeiq.collectors import permissions
from nodeiq.core.collector import CollectorContext

# --- _check_path -----------------------------------------------------------------


def test_check_path_returns_full_data_for_an_existing_file(tmp_path, monkeypatch):
    target = tmp_path / "passwd"
    target.write_text("root:x:0:0:root:/root:/bin/bash\n")
    os.chmod(target, 0o644)

    monkeypatch.setattr(permissions, "_resolve_owner", lambda uid: "root")
    monkeypatch.setattr(permissions, "_resolve_group", lambda gid: "root")

    entry, error = permissions._check_path(target)

    assert error is None
    assert entry == {
        "path": str(target),
        "exists": True,
        "owner": "root",
        "group": "root",
        "mode": "644",
        "world_writable": False,
    }


def test_check_path_detects_world_writable_files(tmp_path, monkeypatch):
    target = tmp_path / "oops"
    target.write_text("data")
    os.chmod(target, 0o666)

    monkeypatch.setattr(permissions, "_resolve_owner", lambda uid: "root")
    monkeypatch.setattr(permissions, "_resolve_group", lambda gid: "root")

    entry, error = permissions._check_path(target)

    assert entry["world_writable"] is True
    assert entry["mode"] == "666"


def test_check_path_reports_exists_false_for_a_missing_path(tmp_path):
    target = tmp_path / "does_not_exist"

    entry, error = permissions._check_path(target)

    assert error is None
    assert entry == {
        "path": str(target),
        "exists": False,
        "owner": None,
        "group": None,
        "mode": None,
        "world_writable": None,
    }


def test_check_path_records_an_error_when_stat_raises_an_unexpected_oserror(
    tmp_path, monkeypatch
):
    target = tmp_path / "unreadable"
    target.write_text("data")

    def fake_stat(self, *args, **kwargs):
        raise PermissionError("Permission denied")

    monkeypatch.setattr(Path, "stat", fake_stat)

    entry, error = permissions._check_path(target)

    assert entry["exists"] is None
    assert entry["owner"] is None
    assert error is not None
    assert error["severity"] == "error"
    assert error["exception_type"] == "PermissionError"


# --- _resolve_owner / _resolve_group -----------------------------------------------


def test_resolve_owner_returns_username_when_lookup_succeeds(monkeypatch):
    class _FakePasswdEntry:
        pw_name = "root"

    monkeypatch.setattr(permissions.pwd, "getpwuid", lambda uid: _FakePasswdEntry())

    assert permissions._resolve_owner(0) == "root"


def test_resolve_owner_falls_back_to_uid_string_when_lookup_fails(monkeypatch):
    def _raise_keyerror(uid):
        raise KeyError(uid)

    monkeypatch.setattr(permissions.pwd, "getpwuid", _raise_keyerror)

    assert permissions._resolve_owner(99999) == "99999"


def test_resolve_group_returns_group_name_when_lookup_succeeds(monkeypatch):
    class _FakeGroupEntry:
        gr_name = "root"

    monkeypatch.setattr(permissions.grp, "getgrgid", lambda gid: _FakeGroupEntry())

    assert permissions._resolve_group(0) == "root"


def test_resolve_group_falls_back_to_gid_string_when_lookup_fails(monkeypatch):
    def _raise_keyerror(gid):
        raise KeyError(gid)

    monkeypatch.setattr(permissions.grp, "getgrgid", _raise_keyerror)

    assert permissions._resolve_group(99999) == "99999"


# --- collect() end-to-end -------------------------------------------------------


def _context() -> CollectorContext:
    return CollectorContext(scan_start_time=datetime.now(timezone.utc))


def test_collect_checks_every_configured_path(monkeypatch, tmp_path):
    existing = tmp_path / "exists"
    existing.write_text("data")
    os.chmod(existing, 0o644)
    missing = tmp_path / "missing"

    monkeypatch.setattr(permissions, "_CHECKED_PATHS", [existing, missing])
    monkeypatch.setattr(permissions, "_resolve_owner", lambda uid: "root")
    monkeypatch.setattr(permissions, "_resolve_group", lambda gid: "root")

    result = permissions.collect(_context())

    assert result.collector_name == "permissions"
    assert result.errors == []
    assert len(result.data["checked_paths"]) == 2
    assert result.data["checked_paths"][0]["exists"] is True
    assert result.data["checked_paths"][1]["exists"] is False


def test_collect_continues_past_a_path_that_cannot_be_checked(monkeypatch, tmp_path):
    good = tmp_path / "good"
    good.write_text("data")
    os.chmod(good, 0o644)
    bad = tmp_path / "bad"
    bad.write_text("data")

    real_check_path = permissions._check_path

    def fake_check_path(path):
        if path == bad:
            return permissions._empty_entry(path, exists=None), {
                "message": "boom",
                "severity": "error",
                "exception_type": "PermissionError",
            }
        return real_check_path(path)

    monkeypatch.setattr(permissions, "_CHECKED_PATHS", [good, bad])
    monkeypatch.setattr(permissions, "_check_path", fake_check_path)
    monkeypatch.setattr(permissions, "_resolve_owner", lambda uid: "root")
    monkeypatch.setattr(permissions, "_resolve_group", lambda gid: "root")

    result = permissions.collect(_context())

    assert len(result.data["checked_paths"]) == 2
    assert result.data["checked_paths"][0]["exists"] is True
    assert result.data["checked_paths"][1]["exists"] is None
    assert len(result.errors) == 1
    assert result.success is False
