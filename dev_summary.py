"""Temporary developer utility: run the NodeIQ pipeline end-to-end by hand.

Not part of the production CLI (Phase 5). Exists only so a developer can
manually exercise scan -> save -> summarize during development, without
argparse or any CLI wiring. Orchestrates existing components only; it
contains no business logic of its own.

Usage:
    python dev_summary.py
"""

from nodeiq.core.coordinator import run_scan
from nodeiq.core.snapshot import save_snapshot
from nodeiq.report import format_report
from nodeiq.summary import summarize_snapshot


def main() -> None:
    """Run a scan, save it, summarize it, and print the formatted report."""
    snapshot = run_scan()
    saved_path = save_snapshot(snapshot)
    summary = summarize_snapshot(snapshot)

    print(format_report(summary))
    print(f"Snapshot saved to: {saved_path}")


if __name__ == "__main__":
    main()
