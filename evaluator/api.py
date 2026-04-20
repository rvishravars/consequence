"""FastAPI server for evaluation engine."""

import json
import os
import uuid
from typing import Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

from evaluator.types import SuiteReport
from evaluator.orchestrator import run_suite
from evaluator.registry import get_suite, discover_plugins, list_agents
from evaluator.transport.sse import router as sse_router

app = FastAPI(title="Consequence Python API")
app.include_router(sse_router)

JOBS_FILE = os.getenv("JOBS_FILE", "/data/jobs_db.json")

# Simple persistent store for jobs
_jobs: dict[str, dict[str, Any]] = {}

def _load_jobs():
    global _jobs
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                _jobs = json.load(f)
        except Exception as e:
            print(f"Error loading jobs: {e}")
            _jobs = {}

def _save_jobs():
    try:
        with open(JOBS_FILE, "w") as f:
            json.dump(_jobs, f, indent=2)
    except Exception as e:
        print(f"Error saving jobs: {e}")

_load_jobs()


class StartEvalRequest(BaseModel):
    model: str = "gemma4"
    agent_name: str = "default"
    pass_threshold: float = 0.5
    llm_judge: bool = False
    gpus: int | None = None


class JobStatus(BaseModel):
    status: str
    report: SuiteReport | None = None
    connection_url: str | None = None


def _background_run_eval(job_id: str, suite_name: str, options: StartEvalRequest):
    """Run the suite in the background via subprocess-based orchestration."""
    import anyio
    
    # Dynamically discover and load the suite and runners via registry
    discover_plugins("eval.suites")
    discover_plugins("eval.runners")
    suite = get_suite(suite_name)
    
    if not suite:
        _jobs[job_id] = {"status": "FAILED", "error": "Unknown suite"}
        _save_jobs()
        return
        
    try:
        # Run it asynchronously
        report = anyio.run(
            run_suite, 
            suite, 
            options.model, 
            options.pass_threshold, 
            options.llm_judge,
            options.agent_name
        )
        # Convert report to dict for storage
        report_data = report.model_dump() if hasattr(report, "model_dump") else str(report)
        _jobs[job_id]["status"] = "COMPLETED"
        _jobs[job_id]["report"] = report_data
    except Exception as e:
        _jobs[job_id]["status"] = "FAILED"
        _jobs[job_id]["error"] = str(e)
    finally:
        _save_jobs()


@app.post("/evaluate/suite/{suite_name}")
async def start_evaluation(
    suite_name: str, 
    background_tasks: BackgroundTasks,
    request: StartEvalRequest = StartEvalRequest()
):
    """Start an evaluation job and return its ID."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "RUNNING", 
        "report": None,
        "suite": suite_name,
        "model": request.model,
        "gpus": request.gpus
    }
    _save_jobs()
    
    background_tasks.add_task(_background_run_eval, job_id, suite_name, request)
    return {"job_id": job_id}


@app.get("/evaluate/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Check the status of a job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = _jobs[job_id]
    if job["status"] == "FAILED":
        raise HTTPException(status_code=500, detail=job.get("error", "Unknown error"))
        
    return JobStatus(status=job["status"], report=job.get("report"))


@app.get("/evaluate/jobs")
async def list_jobs():
    """List all jobs in the system."""
    return _jobs


@app.delete("/evaluate/jobs")
async def delete_jobs():
    """Delete all job history in the system."""
    global _jobs
    _jobs.clear()
    _save_jobs()
    return {"status": "success", "message": "All jobs deleted"}
