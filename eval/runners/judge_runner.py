"""Isolated runner for the LLM judge."""

import argparse
import asyncio
import json
import logging
import sys

from eval.llm_evaluator import make_llm_judge
from evaluator.types import EvalResult
from evaluator.registry import get_suite, discover_plugins

logging.basicConfig(level=logging.WARNING)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--result", required=True, help="JSON serialized EvalResult minus the task objects")
    args = parser.parse_args()

    # Support dynamic lookups via registry
    discover_plugins("eval.suites")
    suite = get_suite(args.suite)
    
    if not suite:
        print(json.dumps({"error": f"Unknown suite: {args.suite}"}))
        sys.exit(1)

    task = next((t for t in suite.tasks if t.id == args.task_id), None)
    if not task:
        print(json.dumps({"error": f"Unknown task ID: {args.task_id}"}))
        sys.exit(1)

    try:
        result_dict = json.loads(args.result)
        result = EvalResult(**result_dict)
        
        judge = make_llm_judge()
        score = await judge(result, task)
        
        print(json.dumps({"score": score}))
        
    except Exception as exc:
        print(json.dumps({"error": str(exc), "score": 0.0}))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
