from fastapi import APIRouter, UploadFile, File
import shutil
from pipeline.rag_pipeline import run_pipeline, DATA_FOLDER, SUPPORTED_FORMATS
import os
from typing import List

router = APIRouter()

@router.get("/documents")
def list_docs():
    """List of documents currently in data folder"""
    files = [
        f for f in os.listdir(DATA_FOLDER)
        if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS
    ]
    return {
        "count": len(files),
        "documents": files,
        "data_folder": DATA_FOLDER
    }

@router.post("/ingest")
def ingest_documents():
    """Trigger RAG pipeline to reload all documents into ChromaDB"""
    try:
        run_pipeline()
        return {
            "status": "success",
            "message": "Documents ingested into ChromaDB successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload one or more contract documents (PDF, DOCX, XLSX).
    Automatically ingests into ChromaDB after upload.
    """
    uploaded = []
    failed = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in SUPPORTED_FORMATS:
            failed.append({
                "file": file.filename,
                "reason": f"Unsupported format {ext}. Supported: PDF, DOCX, XLSX"
            })
            continue

        dest_path = os.path.join(DATA_FOLDER, file.filename)
        try:
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded.append(file.filename)
        except Exception as e:
            failed.append({"file": file.filename, "reason": str(e)})

    # auto-ingest uploaded files into ChromaDB
    if uploaded:
        run_pipeline()

    return {
        "status": "success",
        "uploaded": uploaded,
        "failed": failed,
        "message": f"{len(uploaded)} file(s) uploaded and ingested into ChromaDB"
    }