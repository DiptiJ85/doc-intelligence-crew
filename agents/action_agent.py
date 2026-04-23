from crewai import Agent
from config.config_llm import get_llm

def create_action_agent():
    return Agent(
    role="Procurement Action Planner",
    goal="Convert risk analysis into a concrete, prioritized action plan with clear owners",
    backstory="""Senior procurement director who has managed $500M+ in vendor contracts.
    You turn risk findings into clear, actionable steps with realistic timelines""",
    llm = get_llm(),
    verbose=True
)