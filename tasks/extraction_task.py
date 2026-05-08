from crewai import Task
from schemas.contract_schemas import ExtractionResults


def create_extraction_task(extractor_agent, rag_task):
    return Task(
        description="""
        Using ONLY the retrieved context from the RAG agent,
        extract structured contract information for EVERY vendor mentioned.
        Do NOT make assumptions beyond what is in the context.

        For each vendor contract found, extract:
        1. contract_id — unique identifier (use vendor name + year if no ID present)
        2. vendor_name — name of the vendor
        3. contract_value — annual value in USD as a number (use 0.0 if not found)
        4. start_date — contract start date as a string
        5. end_date — contract end date as a string
        6. auto_renewal — true or false
        7. services — list of services covered
        8. risks — list of identified risks
        9. contacts — names and contact details found

        Return one entry per vendor in the contracts list.
        """,
        expected_output="An ExtractionResults object with a contracts list, one ExtractedDoc per vendor.",
        output_pydantic=ExtractionResults,
        agent=extractor_agent,
        context=[rag_task]
    )
