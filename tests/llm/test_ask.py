"""Unit tests for nodeiq.llm.ask.

answer_question() is a pure composition of four already-tested
functions (load_snapshot/load_latest_snapshot, summarize_snapshot,
build_prompt, ask_openai) — every test here mocks those four seams
directly, per PROJECT_RULES.md Section 11. No real snapshot file, no
real OpenAI call.
"""

import pytest

from nodeiq.core.exceptions import SnapshotError
from nodeiq.llm import ask as ask_module
from nodeiq.llm.exceptions import LLMAuthenticationError, LLMConfigurationError

_FAKE_SNAPSHOT = {
    "metadata": {"scan_timestamp": "2026-07-16T09:00:00+00:00", "hostname": "test-host"},
    "collection_errors": {},
    "system": {
        "hostname": "test-host",
        "operating_system": "Ubuntu 24.04.4 LTS",
        "kernel_version": "6.8.0-134-generic",
        "architecture": "aarch64",
        "uptime_seconds": 3600.0,
    },
}


def _install(monkeypatch, *, snapshot=None, snapshot_error=None, prompt_seen=None, answer="the answer"):
    """Wire up fake load_latest_snapshot/load_snapshot, real
    summarize_snapshot (unmocked — it's pure and already tested),
    a build_prompt spy, and a fake ask_openai. Returns a dict of call
    records the test can inspect.
    """
    calls = {"load_latest": 0, "load_path": None, "prompt_args": None, "openai_prompt": None}

    def _load_latest():
        calls["load_latest"] += 1
        if snapshot_error:
            raise snapshot_error
        return snapshot if snapshot is not None else _FAKE_SNAPSHOT

    def _load(path):
        calls["load_path"] = path
        if snapshot_error:
            raise snapshot_error
        return snapshot if snapshot is not None else _FAKE_SNAPSHOT

    real_build_prompt = ask_module.build_prompt

    def _build_prompt(question, evidence, **kwargs):
        calls["prompt_args"] = (question, evidence)
        return real_build_prompt(question, evidence, **kwargs)

    def _ask_openai(prompt):
        calls["openai_prompt"] = prompt
        return answer

    monkeypatch.setattr(ask_module, "load_latest_snapshot", _load_latest)
    monkeypatch.setattr(ask_module, "load_snapshot", _load)
    monkeypatch.setattr(ask_module, "build_prompt", _build_prompt)
    monkeypatch.setattr(ask_module, "ask_openai", _ask_openai)
    return calls


# --- Successful answer --------------------------------------------------------------


def test_successful_answer_is_returned_unchanged(monkeypatch):
    _install(monkeypatch, answer="According to the evidence, nothing has failed.")

    result = ask_module.answer_question("Is anything wrong?")

    assert result["answer"] == "According to the evidence, nothing has failed."


def test_result_includes_the_snapshots_metadata(monkeypatch):
    _install(monkeypatch)

    result = ask_module.answer_question("Is anything wrong?")

    assert result["snapshot_metadata"] == _FAKE_SNAPSHOT["metadata"]


# --- Latest snapshot loading ----------------------------------------------------------


def test_default_loads_latest_snapshot(monkeypatch):
    calls = _install(monkeypatch)

    ask_module.answer_question("What OS is this?")

    assert calls["load_latest"] == 1
    assert calls["load_path"] is None


# --- Explicit snapshot path ------------------------------------------------------------


def test_explicit_snapshot_path_is_used_instead_of_latest(monkeypatch):
    calls = _install(monkeypatch)

    ask_module.answer_question("What OS is this?", snapshot_path="snapshots/specific.json")

    assert calls["load_path"] == "snapshots/specific.json"
    assert calls["load_latest"] == 0


# --- Missing snapshot --------------------------------------------------------------------


def test_missing_snapshot_propagates_snapshot_error(monkeypatch):
    _install(monkeypatch, snapshot_error=SnapshotError("no snapshot files found in snapshots"))

    with pytest.raises(SnapshotError, match="no snapshot files found"):
        ask_module.answer_question("What OS is this?")


# --- Malformed snapshot --------------------------------------------------------------------


def test_malformed_snapshot_propagates_snapshot_error(monkeypatch):
    _install(monkeypatch, snapshot_error=SnapshotError("snapshot bad.json is not valid JSON"))

    with pytest.raises(SnapshotError, match="not valid JSON"):
        ask_module.answer_question("What OS is this?", snapshot_path="bad.json")


# --- Missing API key / authentication failure -------------------------------------------


def test_missing_api_key_propagates_llm_configuration_error(monkeypatch):
    _install(monkeypatch)

    def _raise(prompt):
        raise LLMConfigurationError(
            "OPENAI_API_KEY is not configured. Create a .env file or "
            "export the environment variable."
        )

    monkeypatch.setattr(ask_module, "ask_openai", _raise)

    with pytest.raises(LLMConfigurationError, match="OPENAI_API_KEY is not configured"):
        ask_module.answer_question("What OS is this?")


def test_authentication_failure_propagates_llm_authentication_error(monkeypatch):
    _install(monkeypatch)

    def _raise(prompt):
        raise LLMAuthenticationError("OpenAI rejected the configured API key.")

    monkeypatch.setattr(ask_module, "ask_openai", _raise)

    with pytest.raises(LLMAuthenticationError):
        ask_module.answer_question("What OS is this?")


# --- Timeout (one representative LLMError subclass propagating unchanged) ---------------


def test_timeout_propagates_unchanged(monkeypatch):
    from nodeiq.llm.exceptions import LLMTimeoutError

    _install(monkeypatch)

    def _raise(prompt):
        raise LLMTimeoutError("The request to OpenAI timed out after 3 attempt(s).")

    monkeypatch.setattr(ask_module, "ask_openai", _raise)

    with pytest.raises(LLMTimeoutError, match="timed out"):
        ask_module.answer_question("What OS is this?")


# --- Prompt pass-through: build_prompt is the only place a prompt is built --------------


def test_question_is_passed_to_build_prompt_verbatim(monkeypatch):
    calls = _install(monkeypatch)

    ask_module.answer_question("What is consuming memory?")

    question_seen, _evidence_seen = calls["prompt_args"]
    assert question_seen == "What is consuming memory?"


def test_summary_not_raw_snapshot_is_passed_to_build_prompt(monkeypatch):
    calls = _install(monkeypatch)

    ask_module.answer_question("What OS is this?")

    _question_seen, evidence_seen = calls["prompt_args"]
    # A Summary has "sections"/"generated_at"; a raw snapshot does not.
    assert "sections" in evidence_seen
    assert "generated_at" in evidence_seen


def test_build_prompts_output_is_sent_to_ask_openai_unmodified(monkeypatch):
    calls = _install(monkeypatch)

    ask_module.answer_question("What OS is this?")

    sent_prompt = calls["openai_prompt"]
    assert set(sent_prompt.keys()) == {"system", "user", "prompt_version"}
    assert "What OS is this?" in sent_prompt["user"]


# --- Answer returned unchanged -----------------------------------------------------------


def test_answer_text_is_not_reformatted_or_wrapped(monkeypatch):
    _install(monkeypatch, answer="  Exactly this, including odd spacing.  ")

    result = ask_module.answer_question("q")

    assert result["answer"] == "  Exactly this, including odd spacing.  "
