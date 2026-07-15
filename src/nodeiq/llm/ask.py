"""Ask orchestration: the one place that composes an already-loaded
snapshot, the Summary Engine, the Prompt Builder, and the OpenAI client
into a single answer.

This is a pure composition layer, not a new architectural piece —
every function it calls (`load_snapshot`/`load_latest_snapshot`,
`summarize_snapshot`, `build_prompt`, `ask_openai`) already existed and
is unchanged by this module. `nodeiq.cli.main._cmd_ask` calls
`answer_question()` instead of orchestrating these four calls itself,
so the CLI stays a thin dispatcher and this one function is the single
place the full "question -> answer" pipeline is assembled.

Typical usage (this is exactly what `nodeiq ask` does):

    from nodeiq.llm.ask import answer_question

    result = answer_question("What service failed?")
    print(result["answer"])
"""

from pathlib import Path

from nodeiq.core.snapshot import load_latest_snapshot, load_snapshot
from nodeiq.llm.client import ask_openai
from nodeiq.llm.prompt import build_prompt
from nodeiq.summary import summarize_snapshot


def answer_question(question: str, snapshot_path: Path | str | None = None) -> dict:
    """Answer one natural-language question about the machine.

    Pipeline: load a snapshot (`snapshot_path` if given, otherwise the
    latest one already saved under `snapshots/`) -> summarize it ->
    build a prompt from `question` and that Summary -> send it to
    OpenAI -> return `{"answer": <str>, "snapshot_metadata": <dict>}`.

    `answer` is the answer text exactly as `ask_openai()` returned it,
    unchanged. `snapshot_metadata` is the snapshot's own `metadata`
    dict (see `docs/snapshot_schema.md`) — returned so a caller can
    check the evidence's age (e.g. `nodeiq.cli.freshness.
    check_snapshot_freshness()`) without loading or resolving the
    snapshot path a second time; this function is already the one place
    that decides which snapshot to use.

    Raises whatever the functions it calls already raise —
    `nodeiq.core.exceptions.SnapshotError` for a missing/malformed
    snapshot, or one of `nodeiq.llm.exceptions`' `LLMError` subclasses
    for anything that goes wrong talking to OpenAI. This function adds
    no error handling of its own; translating an exception into a
    clean, user-facing message and an exit code is the CLI's job
    (`nodeiq.cli.main._cmd_ask`), exactly like it already is for
    `report`'s own `SnapshotError` handling.
    """
    snapshot = load_snapshot(snapshot_path) if snapshot_path else load_latest_snapshot()
    summary = summarize_snapshot(snapshot)
    prompt = build_prompt(question, summary)
    answer = ask_openai(prompt)
    return {"answer": answer, "snapshot_metadata": snapshot.get("metadata") or {}}
