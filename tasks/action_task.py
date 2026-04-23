from crewai import Task
from schemas.contract_schemas import ActionPlan

def create_action_task(action_agent, analysis_task):
    return Task(
        description="""
        Based on the risk analysis, create a prioritized action plan.
        Separate immediate actions (24-48 hrs) from short-term actions (30 days).
        Assign clear ownership to each action item.
        Determine if executive escalation is required.
        """,
        expected_output="Actionable plan with prioroties, owners and escalation recommendation",
        output_pydantic=ActionPlan,
        agent = action_agent,
        context=[analysis_task]
    )