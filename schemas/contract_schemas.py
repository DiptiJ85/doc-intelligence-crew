from pydantic import BaseModel, Field
from typing import List, Optional


class ExtractedDoc(BaseModel):
    contract_id: str = Field(description="Unique contract identifier")
    vendor_name: str = Field(description="Name of the vendor")
    contract_value: Optional[float] = Field(default=None, description="Annual contract value in USD — null if not found")
    start_date: str = Field(description="Contract start date")
    end_date: str = Field(description="Contract end date")
    auto_renewal: bool = Field(description="Whether auto-renewal is active")
    services: List[str] = Field(description="List of services covered")
    risks: List[str] = Field(description="List of identified risks")
    contacts: List[str] = Field(description="Names and contact details found")


class ExtractionResults(BaseModel):
    """Wrapper so the extractor agent can return data for multiple contracts at once."""
    contracts: List[ExtractedDoc] = Field(description="One entry per vendor contract found")


class AnalysisResult(BaseModel):
    critical_risks: List[str] = Field(description="Critical severity risks requiring immediate action")
    high_risks: List[str] = Field(description="High severity risks")
    medium_risks: List[str] = Field(description="Medium severity risks")
    low_risks: List[str] = Field(description="Low severity risks")
    financial_exposure: str = Field(description="Summary of financial risk")
    compliance_flags: List[str] = Field(description="Compliance issues found")
    overall_risk_score: str = Field(description="Overall risk: LOW, MEDIUM, HIGH, CRITICAL")


class ActionPlan(BaseModel):
    immediate_actions: List[str] = Field(description="Actions needed within 24-48 hours")
    short_term_actions: List[str] = Field(description="Actions needed within 30 days")
    owners: List[str] = Field(description="Teams responsible for each action")
    escalation_required: bool = Field(description="Whether executive escalation is needed")
