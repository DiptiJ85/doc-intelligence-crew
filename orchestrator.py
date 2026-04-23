from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "env", ".env"))
import sys
import logging
from datetime import datetime
from crewai import Crew, Process
from agents.rag_agent import create_rag_agent
from agents.extractor_agent import create_extractor_agent
from agents.analyst_agent import create_analyst_agent
from agents.action_agent import create_action_agent
from agents.summary_agent import create_summary_agent   

from tasks.rag_task import create_rag_task
from tasks.extraction_task import create_extraction_task
from tasks.analysis_task import create_analysis_task
from tasks.action_task import create_action_task
from tasks.summary_task import create_summary_task  
from utils.logger import get_logger

logger = get_logger(__name__)

def run_crew(user_request:str):
    logger.info("="*60)
    logger.info("Crew Run Started")
    logger.info(f"User Request: {user_request}")
    logger.info("="*60)
    logger.info("Initializing agents..")        
                
    rag_agent = create_rag_agent()
    extractor_agent = create_extractor_agent()  
    analyst_agent = create_analyst_agent()
    action_agent = create_action_agent()
    summary_agent = create_summary_agent()
    logger.info("✅ All agents initialized")
    
    logger.info("Initializing tasks..")  
    rag_task = create_rag_task(rag_agent)   
    extraction_task = create_extraction_task(extractor_agent, rag_task)
    analysis_task = create_analysis_task(analyst_agent, extraction_task)
    action_task = create_action_task(action_agent, analysis_task)
    summary_task = create_summary_task(summary_agent, extraction_task, analysis_task, action_task ) 
    logger.info("✅ All tasks initialized")
    
    crew = Crew(
        agents=[rag_agent, extractor_agent, analyst_agent, action_agent, summary_agent],
        tasks=[rag_task, extraction_task, analysis_task, action_task, summary_task],
        process=Process.sequential,
        verbose=True
    )
    logger.info("Kicking off crew...")
    result = crew.kickoff(inputs={'user_request': user_request})
    logger.info("=" * 60)
    logger.info("CREW RUN COMPLETE")
    logger.info("EXECUTIVE SUMMARY:")
    logger.info(str(result))
    logger.info("=" * 60)
    return result

if __name__ == "__main__":  
    # redirect ALL stdout to both console and log file
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"crew_run_{timestamp}.log")

    # tee output to file AND console
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()

    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = Tee(sys.stdout, log_file)
    sys.stderr = Tee(sys.stderr, log_file)

    result = run_crew(
        """Analyze all vendor contracts in our knowledge base.
        Identify critical risks, upcoming deadlines, compliance gaps,
        and provide a clear recommendation on which need immediate attention."""
    )

    print("\n" + "=" * 60)
    print("EXECUTIVE SUMMARY")
    print("=" * 60)
    print(result)

                                       