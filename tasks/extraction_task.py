from crewai import Task
from schemas.contract_schemas import ExtractedDoc


def create_extraction_task(extractor_agent, rag_task):
    return Task(
    description=f"""
        Using ONLY the retrieved context from the RAG agent,
        extract all structured contract information.
        Do NOT make assumptions beyond what is in the context.
        Extract data for ALL vendors mentioned.

        Extract the following:
        1. Vendor name and contract  ID
        2. Contract value and payment terms
        3. Contract start and end dates
        4. Auto-renewal status and critical deadlines
        5. List of all services with cost
        6. Number and contact details found in the document
        7. Names and contact details found in the document
        """,
    expected_output="""
    A clearly structured extraction with labeled sections for:
    - Contract Metadata (ID, vendor, dates, value)
    - Services Breakdown (itemized list)  
    - Risk Summary (count by severity)
    - Contacts Found (names, emails, phones)
    - Critical Alerts (anything requiring immediate action)
    """,
    output_pydantic=ExtractedDoc,
    agent=extractor_agent,
    context=[rag_task]
)