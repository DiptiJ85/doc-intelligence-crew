import os
import sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "env", ".env"))

from fastapi import FastAPI
from api.routes.health import router as health_router
from api.routes.documents import router as documents_router
from api.routes.analyze import router as analyze_router

app = FastAPI(
    title="Document Intelligence Crew",
    description="Multi-agent AI system for enterprise contract analysis",
    version="0.1.0"
)

app.include_router(health_router, tags=["Health"])
app.include_router(documents_router, tags=["Documents"])
app.include_router(analyze_router, tags=["Analyze"])

@app.get("/")
def root():
    return {
        "service": "Document Intelligence Crew API",
        "version": "1.0.0",
        "endpoints": {
            "health":    "GET  /health",
            "documents": "GET  /documents",
            "uploads":   "POST /documents/upload",
            "ingest":    "POST /ingest",
            "analyze":   "POST /analyze"
        }
    }