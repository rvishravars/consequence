"""CLI entry point for running built-in eval suites."""

from __future__ import annotations

import argparse
import asyncio
import sys


from evaluator.orchestrator import run_suite
from evaluator.reporter import print_suite_report
from evaluator.registry import get_suite, discover_plugins, list_suites, list_agents


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="consequence",
        description="Run MCP-backed agent evaluations.",
    )
    # We discover suites and runners to populate choices
    discover_plugins("eval.suites")
    discover_plugins("eval.runners")
    suite_choices = list_suites() + ["all"]
    agent_choices = list_agents()
    
    parser.add_argument(
        "--suite",
        choices=suite_choices,
        default="all",
        help="Which built-in eval suite to run (default: all)",
    )
    parser.add_argument(
        "--agent",
        choices=agent_choices,
        default="default",
        help="Which registered agent runner to use (default: default)",
    )
    parser.add_argument(
        "--model",
        default="gemma4",
        help="OpenAI-compatible model to use (e.g. gemma4)",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.5,
        help="Minimum score to mark a task as passed (default: 0.5)",
    )
    parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="Use an LLM (as-a-judge) to score results instead of deterministic metrics",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    suites_to_run = []
    if args.suite == "all":
        for name in list_suites():
            suite = get_suite(name)
            if suite:
                suites_to_run.append(suite)
    else:
        suite = get_suite(args.suite)
        if suite:
            suites_to_run.append(suite)

    client = None # run_suite will create AsyncOpenAI default if None
    any_failed = False

    for suite in suites_to_run:
        report = await run_suite(
            suite=suite,
            model=args.model,
            pass_threshold=args.pass_threshold,
            llm_judge=args.llm_judge,
            agent_name=args.agent,
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
