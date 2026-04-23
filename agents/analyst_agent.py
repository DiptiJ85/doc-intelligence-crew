from crewai import Agent
from config.config_llm import get_llm

def create_analyst_agent():
    return Agent(
    role="Contract Risk Analyst",
    goal="Analyse extracted contract data and classify all risks by severity",
    backstory="""Former legal and compliance officer with deep expertise in vendor risk management.
    You categorize risks methodically and never downplay issues.""",
    llm = get_llm(),
    verbose=True
)