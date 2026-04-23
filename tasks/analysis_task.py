from crewai import Task
from schemas.contract_schemas import AnalysisResult

def create_analysis_task(analyst_agent, extraction_task):
    return Task(
        description="""
        Using the extracted contract data, perform a thorough risk analysis.
        Classify each risk as CRITICAL, HIGH, MODERATE, LOW.
        Calculate overall financial exposure.
        Flag any compliance or regulatroy issues.
        """,
        expected_output="Risk analysis with risks classified by severity and overall risk score",
        output_pydantic=AnalysisResult,
        agent=analyst_agent,
        context=[extraction_task]
    )