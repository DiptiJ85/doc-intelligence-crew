from crewai import Task

def create_rag_task(rag_agent):
    return Task(
    description="""
    User request: {user_request}

    STEP 0 — IDENTIFY SCOPE
    Read the user request carefully.
    - If the request mentions a specific document by filename (e.g. "acme_contract.pdf", "vendor_agreement.docx"),
      set source_filter to that exact filename for ALL your search_contracts calls.
    - If no specific document is mentioned, leave source_filter empty to search across all documents.

    STEP 1 — SEARCH
    Run separate searches for each relevant area below.
    Pass source_filter consistently in every call if a specific document was identified.
    1. Contract metadata — vendor names, contract IDs, values, periods
    2. Auto-renewal clauses and upcoming deadlines
    3. Risk findings — HIGH, MODERATE, LOW severity
    4. Services breakdown and pricing details
    5. Compliance issues — GDPR, SOC2, data residency, insurance
    6. Key contacts and approvers
    7. Recommended actions

    Run a minimum of 5 searches with different queries.
    Compile ALL retrieved information into one comprehensive context document.

    search_contracts already returns the top 3 results ranked by relevance score.
    Compile ALL search results into one comprehensive context document.
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