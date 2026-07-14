"""Project-specific exceptions.

Kept deliberately small. The runner (`runner.py`) is designed to never let
a *system-level* failure (a missing command, a timeout, a crash) escape as
an exception — those are reported as data inside a `CommandResult`
instead (see `result.py`). The one exception defined here exists for a
different kind of problem: a *programmer* calling the runner incorrectly,
which should fail fast and loudly rather than being silently absorbed.
"""


class NodeIQError(Exception):
    """Base class for all NodeIQ-specific exceptions.

    Not raised directly. It exists so that any future project-specific
    exception can share one common ancestor, letting calling code catch
    `except NodeIQError` to mean "something NodeIQ-specific went wrong"
    without also swallowing unrelated Python errors.
    """


class InvalidCommandError(NodeIQError):
    """Raised when `run_command` is called with something that isn't a
    valid command: a non-empty list of strings.

    This is a programmer error (calling the function wrong), not a
    system-level failure (the command failing to run) — so it is raised
    immediately rather than captured inside a `CommandResult`.
    """
