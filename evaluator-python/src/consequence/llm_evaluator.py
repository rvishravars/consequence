"""LLM-as-a-judge scoring for evaluations."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI
from consequence.types import EvalResult, EvalTask

_DEFAULT_JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-4o")
_DEFAULT_JUDGE_URL = os.environ.get("JUDGE_BASE_URL", "https://api.openai.com/v1")
_DEFAULT_JUDGE_KEY = os.environ.get("JUDGE_API_KEY", "")

JUDGE_PROMPT = """
You are an impartial judge evaluating the performance of an AI assistant.
Evaluate the assistant's response to the user's task.

[Task Description]
{task_description}

[User Message]
{user_message}

[Expected Output / Criteria]
{expected}

[Assistant's Response]
{actual}

Result:
Provide a score between 0.0 and 1.0, where 1.0 is a perfect response and 0.0 is completely wrong or failed to follow instructions.
Return ONLY a JSON object in this format:
{{
  "score": 0.0,
  "reasoning": "A brief explanation of why the score was given."
}}
"""

def make_llm_judge(
    model: str = _DEFAULT_JUDGE_MODEL,
    base_url: str = _DEFAULT_JUDGE_URL,
    api_key: str = _DEFAULT_JUDGE_KEY
) -> Any:
    """Create a judge function that uses an LLM to score results."""
    client = OpenAI(base_url=base_url, api_key=api_key)

    def judge(result: EvalResult, task: EvalTask) -> float:
        if result.error:
            return 0.0
            
        prompt = JUDGE_PROMPT.format(
            task_description=task.description,
            user_message=task.user_message,
            expected=task.expected_output or "No specific output expected, judge based on utility.",
            actual=result.output or "(No output received)"
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return float(data.get("score", 0.0))
        except Exception:
            # Fallback to simple regex if JSON fails or model doesn't support it
            try:
                raw_content = response.choices[0].message.content
                match = re.search(r'"score":\s*([0-9.]+)', raw_content)
                if match:
                    return float(match.group(1))
            except Exception:
                pass
            return 0.0

    return judge
