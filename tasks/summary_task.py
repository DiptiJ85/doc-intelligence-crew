from crewai import Task

def create_summary_task(summary_agent, extraction_task,analysis_task, action_task):
    return Task(
        description="""
        Write a concise executive summary of the entire contract review.
        Structure:
        1. Situation — contracts under review and total value at risk
        2. Critical Findings — top 3 risks across all vendors
        3. Immediate Actions — what needs to happen in next 48 hours
        4. Recommendation — overall go/no-go on contract renewals

        Write for CFO or General Counsel. Maximum 350 words.
        Be direct, specific, use numbers.""",
        expected_output="A sharp executive summary in plan prose, max 300 words",
        agent = summary_agent,
        context=[extraction_task, analysis_task, action_task]
    )