from crewai import Agent
from config.config_llm import get_llm
from tools.search_tool import search_contracts

def create_rag_agent():
    return Agent(
    role="Contract Intelligence Retriever",
    goal="Retrieve complete, high-quality contract information by running multiple targeted searches from different angles.",
    backstory="""
    You are a specialist in semantic search and document retrieval with deep knowledge of enterprise contracts.
    You know exactly what questions to ask to surface critical information.
    You never rely on a single search — you run multiple queries to ensure nothing is missed.
    You are the eyes of the entire analysis team.""",
    tools=[search_contracts],
    llm=get_llm(),
    max_iter=5,
    verbose=True
)
