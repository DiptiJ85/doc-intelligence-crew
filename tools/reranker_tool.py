from crewai.tools import tool
from google import genai
import os
import json
from config.config_llm import get_llm

@tool
def rerank_chunks(query_and_chunks:str)->str:
    """
    Re-rank retrieved chunks by relevance to the query.
    Input format : JSON string with 'query' and 'chunks' keys.
    Returns top 3 most relevant chinks scored and sorted.
    Use this after search_contracts to improve quality.
    """
    try:
        data = json.loads(query_and_chunks)
        query = data["query"]
        chunks = data["chunks"]
    except Exception:
        return "Error: input must be JSON with 'query' and 'chunks'"
    llm = get_llm()
    model_name = llm.model.replace("gemini/","")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    scored_chunks = []
    for chunk in chunks:
        prompt=f"""
        Query:{query}
        Chunk:{chunk['content'][:500]}

        Score how relevant this chunk is to the query on a scale of 0.0 to 1.0
        Consider: does it directly answer the query? Does it contain related information?
        Repond with ONLY a number between 0.0 and 1.0. Nothing else.chunk
        """
    try:    
        response = client.models.generate_content(
            model=model_name,
            contents=prompt)
        score = float(response.text.strip())
        scored_chunks.append({
            "content": chunk["content"],
            "source": chunk["source"],
            "section_id": chunk["section_id"],
            "score": score
        })
    except Exception:
        scored_chunks.append({
             "content": chunk["content"],
            "source": chunk["source"],
            "section_id": chunk["section_id"],
            "score": 0.0
        })
    
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored_chunks[:3]
    output = f"Re-ranked results for :'{query}' \n"
    output+="=" * 50 + "\n"
    for i, chunk in enumerate(top_chunks):  
       output += f"\n[Rank {i+1} | Score: {chunk['score']:.2f}]\n"
       output += f"Source: {chunk['source']} | Section: {chunk['section_id']}\n"
       output += f"Content:\n{chunk['content']}\n"
       output += "-" * 30 + "\n"
    
    return output
