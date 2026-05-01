from crewai.tools import tool
from pinecone import Pinecone
import google.generativeai as genai
import os
INDEX_NAME = os.environ.get("PINECONE_INDEX", "doc-intelligence")

def get_query_embedding(text: str) -> list:
    """Generate embedding for query using Gemini"""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query"   # ← query type, not document
    )
    return result["embedding"]

@tool
def search_contracts(query:str)-> str:
    """
    Search across all vendor contracts for relevant informaiton.
    Use this tool to find specific clauses, risks, financial details, deadlines, contacts, or any information from contracts.
    Always search multiple times with different queries to get complete picture.
    """
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)

    # embed the query
    query_embedding = get_query_embedding(query)

    # search Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True
    )
    if not results["matches"]:
        return "No relevant information found."

    output = f"Search results for: '{query}'\n"
    output += "=" * 50 + "\n"
    for i, match in enumerate(results["matches"]):
        meta = match["metadata"]
        output += f"\n[Result {i+1} | Score: {match['score']:.3f}]\n"
        output += f"Source: {meta['source']} | Section: {meta['section_id']}\n"
        output += f"Content:\n{meta['content']}\n"
        output += "-" * 30 + "\n"

    return output

