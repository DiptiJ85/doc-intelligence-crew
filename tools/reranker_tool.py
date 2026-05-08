from crewai.tools import tool
from google import genai
import os
import json
from config.config_llm import get_llm


def _parse_input(raw: str) -> tuple[str, list]:
    """
    Accept two input forms:
    1. Proper JSON: {"query": "...", "chunks": [...]}
    2. The raw output from search_contracts (which embeds a STRUCTURED_CHUNKS: line)
    """
    raw = raw.strip()

    # Form 1: plain JSON object
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            return data["query"], data["chunks"]
        except Exception:
            pass

    # Form 2: search_contracts output with embedded STRUCTURED_CHUNKS marker
    marker = "STRUCTURED_CHUNKS:"
    idx = raw.find(marker)
    if idx != -1:
        try:
            data = json.loads(raw[idx + len(marker):].strip())
            return data["query"], data["chunks"]
        except Exception:
            pass

    raise ValueError("Could not parse input — expected JSON or search_contracts output")


@tool
def rerank_chunks(query_and_chunks: str) -> str:
    """
    Re-rank retrieved chunks by relevance to the query.
    Accepts either:
      - JSON string: {"query": "...", "chunks": [...]}
      - The direct output from search_contracts (pass it as-is)
    Returns top 3 most relevant chunks scored and sorted.
    Always call this after search_contracts to improve quality.
    """
    try:
        query, chunks = _parse_input(query_and_chunks)
    except Exception as e:
        return f"Error parsing input: {e}. Pass either JSON with 'query'+'chunks' or the raw search_contracts output."

    if not chunks:
        return "No chunks to re-rank."

    llm = get_llm()
    model_name = llm.model.replace("gemini/", "")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    scored_chunks = []
    for chunk in chunks:
        prompt = f"""
Query: {query}
Chunk: {chunk['content'][:500]}

Score how relevant this chunk is to the query on a scale of 0.0 to 1.0.
Consider: does it directly answer the query? Does it contain related information?
Respond with ONLY a number between 0.0 and 1.0. Nothing else.
"""
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            score = float(response.text.strip())
        except Exception:
            score = chunk.get("score", 0.0)

        scored_chunks.append({
            "content": chunk["content"],
            "source": chunk["source"],
            "section_id": chunk["section_id"],
            "score": score,
        })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored_chunks[:3]

    output = f"Re-ranked results for: '{query}'\n" + "=" * 50 + "\n"
    for i, chunk in enumerate(top_chunks):
        output += f"\n[Rank {i+1} | Score: {chunk['score']:.2f}]\n"
        output += f"Source: {chunk['source']} | Section: {chunk['section_id']}\n"
        output += f"Content:\n{chunk['content']}\n"
        output += "-" * 30 + "\n"

    return output
