from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator import run_crew
import time
router = APIRouter()

class AnalyzeRequest(BaseModel):
    user_request:str = "Analyze all vendor contracts, identify critical risks, upcoming deadlines, compliance gaps, and provide a clear recommendation on which need immediate attention"

class AnalyseResponse(BaseModel):
    status:str
    summary:str
    message:str = ""

@router.post("/analyze", response_model=AnalyseResponse)
def analyze_contracts(request:AnalyzeRequest):
    """
    Trigger the full 5-agent crew toanalyze all vendor contracts.
    Returns executive summary with risks and recommendations.
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            result = run_crew(request.user_request)
            return AnalyseResponse(
                status="success",
                summary=str(result)
            )
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "503" in error_msg:
                wait = (attempt + 1) * 30
                time.sleep(wait)
                continue
            else:
                return AnalyseResponse(
                    status="error",
                    summary = "",
                    message=error_msg
                )
    return AnalyseResponse(
                status="error",
                summary = "",
                message=error_msg
            )


