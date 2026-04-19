"""CLI entry point for running built-in eval suites."""

from __future__ import annotations

import argparse
import asyncio
import sys

import anthropic

from consequence.eval import run_suite
from consequence.reporter import print_suite_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="consequence",
        description="Run MCP-backed agent evaluations.",
    )
    parser.add_argument(
        "--suite",
        choices=["calculator", "database", "all"],
        default="all",
        help="Which built-in eval suite to run (default: all)",
    )
    parser.add_argument(
        "--model",
        default="claude-3-5-haiku-20241022",
        help="Anthropic model to use for the agent",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.5,
        help="Minimum score to mark a task as passed (default: 0.5)",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    from consequence.evals.calculator import calculator_suite
    from consequence.evals.database import database_suite

    suites_to_run = []
    if args.suite in ("calculator", "all"):
        suites_to_run.append(calculator_suite)
    if args.suite in ("database", "all"):
        suites_to_run.append(database_suite)

    client = anthropic.AsyncAnthropic()
    any_failed = False

    for suite in suites_to_run:
        report = await run_suite(
            suite=suite,
            anthropic_client=client,
            model=args.model,
            pass_threshold=args.pass_threshold,
        )
        print_suite_report(report)
        if report.failed > 0 or report.errored > 0:
            any_failed = True

    return 1 if any_failed else 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
