from crewai.tools import tool
from config.config_llm import get_collection

_collection = None

def get_collection_instance():
    global _collection
    if _collection is None:
        _collection = get_collection()
    return _collection

@tool
def search_contracts(query:str)-> str:
    """
    Search across all vendor contracts for relevant informaiton.
    Use this tool to find specific clauses, risks, financial details, deadlines, contacts, or any information from contracts.
    Always search multiple times with different queries to get complete picture.
    """
    collection = get_collection_instance()  
    results = collection.query(query_texts=[query],
                               n_results=3)
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not chunks:
        return "No relevant information found."
    
    output = f"Search results for '{query}' \n"
    output+="=" * 50 + "\n"
    for i, (chunk, meta) in enumerate(zip(chunks, metadatas)):
        output+=f"\nResult {i+1}]\n"
        output+=f"Source: {meta['source']} | Section: {meta['section_id']}\n"
        output+=f"Content:\n{chunk}\n"
        output+="-"*30+"\n"
    
    return output