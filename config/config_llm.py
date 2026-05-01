import os
import chromadb
import google.generativeai as genai
from chromadb.utils import embedding_functions
from crewai.llm import LLM

# ── LLM ──────────────────────────────────────────────
def get_llm():
    return LLM(
        model="gemini/gemini-2.5-flash",
        temperature=0,
        api_key=os.environ.get("GEMINI_API_KEY") ,
        max_retries=3,
        timeout=60
    )