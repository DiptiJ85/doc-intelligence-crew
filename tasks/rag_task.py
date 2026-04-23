from crewai import Task

def create_rag_task(rag_agent):
    return Task(
    description="""
    User request : {user_request}
    Based on above request, search the contract knowledge base thoroughly to retrieve all critical information.
    STEP 1 - 
    You must run separate searches for each of these areas:
    1. Contract metadata - vendor names, contract IDS, values, periods
    2. Auto-renewal clauses and upcoming deadlines
    3. All risk findings - HIGH, MODERATE, LOW severity
    4. Services breakdown and pricing details
    5. Compliance issues- GDPR, SOC2, data residency, insurance
    6. Key contacts and approvers
    7. Recommend actions

    Run a minimum of 5 searches with different queries.
    Compile ALL retrieved information into one comprehensive context document.

    STEP 2 — RE-RANK (MANDATORY)
    You MUST call rerank_chunks after EVERY search_contracts call.
    Never pass raw search results downstream without re-ranking first.
    Format input as: {{"query": "your query", "chunks": [list of chunk dicts]}}

    """,
    expected_output="""
    A comprehensive context document containing ALL retrieved information
    organized by category:
    - Contract Metadata (all vendors)
    - Financial Details (services + costs)
    - Risk Findings (by severity)
    - Compliance Issues
    - Key Contacts
    - Recommended Actions
    - Source attribution for every piece of information
    """,
    agent=rag_agent
)