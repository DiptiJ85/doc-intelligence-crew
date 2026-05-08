from crewai.tools import tool
from pinecone import Pinecone
import google.generativeai as genai
import os

INDEX_NAME = os.environ.get("PINECONE_INDEX", "doc-intelligence")


def get_query_embedding(text: str) -> list:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query"
    )
    return result["embedding"]


@tool
def search_contracts(query: str, source_filter: str = "") -> str:
    """
    Search vendor contracts and return the top 3 most relevant results ranked by similarity.
    Args:
        query: what to search for (e.g. "auto-renewal clauses", "payment terms", "GDPR compliance")
        source_filter: optional filename to restrict search to one document
                       (e.g. "acme_contract.pdf"). Leave empty to search all documents.
    Always call multiple times with different queries to get a complete picture.
    """
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)

    query_embedding = get_query_embedding(query)

    kwargs = dict(vector=query_embedding, top_k=3, include_metadata=True)
    if source_filter.strip():
        kwargs["filter"] = {"source": {"$eq": source_filter.strip()}}

    results = index.query(**kwargs)

    if not results["matches"]:
        suffix = f" in '{source_filter}'" if source_filter.strip() else ""
        return f"No relevant information found{suffix}."

    output = f"Search results for: '{query}'"
    if source_filter.strip():
        output += f" (filtered to: {source_filter})"
    output += "\n" + "=" * 50 + "\n"

    for i, match in enumerate(results["matches"]):
        meta = match["metadata"]
        output += f"\n[Rank {i+1} | Score: {match['score']:.3f}]\n"
        output += f"Source: {meta['source']} | Section: {meta['section_id']}\n"
        output += f"Content:\n{meta['content']}\n"
        output += "-" * 30 + "\n"

    return output
