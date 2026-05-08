from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from orchestrator import run_crew, CrewCancelledError
import threading
import uuid
import time

router = APIRouter()

# Module-level stores — live for the lifetime of the uvicorn process.
# Each browser session tracks its own job_id via Streamlit session_state,
# so multiple users can run independent jobs concurrently.
_jobs: dict[str, dict] = {}          # job_id -> {status, summary, message}
_job_events: dict[str, threading.Event] = {}   # job_id -> cancel event
_store_lock = threading.Lock()


class AnalyzeRequest(BaseModel):
    user_request: str = (
        "Analyze all vendor contracts, identify critical risks, upcoming deadlines, "
        "compliance gaps, and provide a clear recommendation on which need immediate attention"
    )


class StartResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    status: str   # "running" | "success" | "error" | "cancelled"
    summary: str = ""
    message: str = ""


class AnalyseResponse(BaseModel):
    status: str
    summary: str
    message: str = ""


def _run_crew_background(job_id: str, user_request: str, cancel_event: threading.Event) -> None:
    max_attempts = 3
    last_error = ""
    for attempt in range(max_attempts):
        try:
            result = run_crew(user_request, cancel_event=cancel_event)
            with _store_lock:
                _jobs[job_id] = {"status": "success", "summary": str(result), "message": ""}
            return
        except CrewCancelledError:
            with _store_lock:
                _jobs[job_id] = {"status": "cancelled", "summary": "", "message": "Cancelled by user"}
            return
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "quota" in last_error.lower() or "503" in last_error:
                wait = (attempt + 1) * 30
                with _store_lock:
                    _jobs[job_id]["message"] = (
                        f"Rate limited — retrying in {wait}s (attempt {attempt + 1}/{max_attempts})"
                    )
                # Check for cancellation during the sleep window
                if cancel_event.wait(timeout=wait):
                    with _store_lock:
                        _jobs[job_id] = {"status": "cancelled", "summary": "", "message": "Cancelled by user"}
                    return
            else:
                with _store_lock:
                    _jobs[job_id] = {"status": "error", "summary": "", "message": last_error}
                return

    with _store_lock:
        _jobs[job_id] = {
            "status": "error",
            "summary": "",
            "message": f"Max retries exceeded. Last error: {last_error}",
        }


@router.post("/analyze/start", response_model=StartResponse)
def start_analysis(request: AnalyzeRequest):
    """
    Start a background crew run and return a job_id immediately.
    Multiple users can call this concurrently — each gets an isolated job.
    Poll GET /analyze/status/{job_id} to check progress.
    Cancel with POST /analyze/cancel/{job_id}.
    """
    job_id = str(uuid.uuid4())
    cancel_event = threading.Event()
    with _store_lock:
        _jobs[job_id] = {"status": "running", "summary": "", "message": ""}
        _job_events[job_id] = cancel_event

    thread = threading.Thread(
        target=_run_crew_background,
        args=(job_id, request.user_request, cancel_event),
        daemon=True,
    )
    thread.start()
    return StartResponse(job_id=job_id)


@router.get("/analyze/status/{job_id}", response_model=StatusResponse)
def get_status(job_id: str):
    """Poll the status of a running or completed job."""
    with _store_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(**job)


@router.post("/analyze/cancel/{job_id}")
def cancel_job(job_id: str):
    """
    Signal a running job to stop between agents (best-effort).
    Cannot interrupt a mid-flight LLM call — the current agent finishes before the
    cancellation takes effect.
    """
    with _store_lock:
        event = _job_events.get(job_id)
        job = _jobs.get(job_id)
    if event is None or job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "running":
        return {"detail": f"Job is already {job['status']} — no action taken"}
    event.set()
    return {"detail": "Cancellation signal sent — current agent will finish before stopping"}


@router.delete("/analyze/jobs")
def clear_completed_jobs():
    """Remove finished (success/error/cancelled) jobs from memory. Does not cancel running jobs."""
    with _store_lock:
        done = [jid for jid, j in _jobs.items() if j["status"] != "running"]
        for jid in done:
            del _jobs[jid]
            _job_events.pop(jid, None)
    return {"cleared": len(done)}


# ── Kept for backwards compatibility / direct API use ─────────────────────────
@router.post("/analyze", response_model=AnalyseResponse)
def analyze_contracts(request: AnalyzeRequest):
    """Blocking endpoint — prefer /analyze/start + polling for UI use."""
    max_attempts = 3
    last_error = ""
    for attempt in range(max_attempts):
        try:
            result = run_crew(request.user_request)
            return AnalyseResponse(status="success", summary=str(result))
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "quota" in last_error.lower() or "503" in last_error:
                time.sleep((attempt + 1) * 30)
            else:
                return AnalyseResponse(status="error", summary="", message=last_error)
    return AnalyseResponse(status="error", summary="", message=last_error)
