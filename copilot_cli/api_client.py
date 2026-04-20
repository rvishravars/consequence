"""Client for interacting with the Python Evaluation Engine REST API."""

import httpx
import os
from typing import Any

# Use environment variable or default to localhost for non-docker local testing
API_BASE_URL = os.getenv("PYTHON_EVAL_URL", "http://localhost:8000")

def start_evaluation(suite: str, agent_name: str = "default", model: str = "gemma4", llm_judge: bool = False, gpus: int | None = None) -> dict[str, Any]:
    """Start an evaluation job and return its ID."""
    url = f"{API_BASE_URL}/evaluate/suite/{suite}"
    payload = {
        "model": model,
        "agent_name": agent_name,
        "pass_threshold": 0.5,
        "llm_judge": llm_judge,
    }
    if gpus is not None:
        payload["gpus"] = gpus
        
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def check_job_status(job_id: str) -> dict[str, Any]:
    """Check the status of a specific job."""
    url = f"{API_BASE_URL}/evaluate/status/{job_id}"
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def list_jobs() -> dict[str, Any]:
    """List all evaluation jobs."""
    url = f"{API_BASE_URL}/evaluate/jobs"
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def delete_all_jobs() -> dict[str, Any]:
    """Clear all job history."""
    url = f"{API_BASE_URL}/evaluate/jobs"
    try:
        response = httpx.delete(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
