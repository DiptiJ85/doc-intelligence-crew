from crewai import Agent
from config.config_llm import get_llm
from tools.search_tool import search_contracts
from tools.reranker_tool import rerank_chunks

def create_rag_agent():
    return Agent(
    role="Contract Intelligence Retriever",
    goal="""Retrieve high quality, complete contract information by:
        1. Searching ChromaDB with targeted queries
        2. Re-ranking results to keep only highly relevant chunks
    """,
    backstory="""
    You are a specialist in semantic search and document retrieval with deep knowledge of enterprise contracts.
    You use re-ranking to filter noise and catch blind spots.
    You know exactly what questions to ask to surface critical information. You never rely on a single search - you run multiple queries from different angles to ensure nothing is missed.
    You are the eyes of the entire analysis team.""",
    tools=[search_contracts, rerank_chunks],
    llm = get_llm(),
    verbose=True
)