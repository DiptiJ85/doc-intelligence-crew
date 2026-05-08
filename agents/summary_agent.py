from crewai import Agent
from config.config_llm import get_llm

def create_summary_agent():
    return Agent(
    role="Executive Communications Specialist",
    goal = "Produce a concise executive summary that tells the full story clearly",
    backstory="""Former McKinsey consultant who specializes in distilling complex contract reviews into sharp executive briefs.
    You write C-suite audiences who have 2 minutes to read and need to make a decision.""",
    llm=get_llm(),
    max_iter=5,
    verbose=True
)