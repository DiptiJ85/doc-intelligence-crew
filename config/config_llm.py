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
        api_key=os.environ.get("GEMINI_API_KEY") 
    )

# ── Embeddings + ChromaDB ─────────────────────────────
def get_collection():
    api_key = os.environ.get("GEMINI_API_KEY")

    genai.configure(api_key=api_key)

    google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name= "models/gemini-2.0-flash-lite" #"models/gemini-embedding-001"
    )

    chroma_client = chromadb.PersistentClient(
        path=os.path.join(os.path.dirname(__file__), "../chroma_store")
    )

    collection = chroma_client.get_collection(
        name="contract_docs",
        embedding_function=google_ef
    )

    return collection