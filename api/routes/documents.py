from fastapi import APIRouter, UploadFile, File
import shutil
from pipeline.rag_pipeline import run_pipeline, SUPPORTED_FORMATS
import os
from typing import List
from google.cloud import storage

router = APIRouter()

MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB

@router.get("/documents")
def list_docs():
    """List of documents currently in data folder"""
    client = storage.Client()
    bucket = client.bucket("document-intelligence-crew-data")
    blobs = bucket.list_blobs(prefix="contracts/")

    files = [
        os.path.basename(blob.name) 
        for blob in blobs 
        if os.path.splitext(blob.name)[1].lower() in {".pdf", ".docx", ".xlsx"}
    ]

    return {
        "count": len(files),
        "documents": files
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
    client = storage.Client()
    bucket = client.bucket("document-intelligence-crew-data")
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

        try:
            content = await file.read()
            if len(content) > MAX_FILE_BYTES:
                failed.append({
                    "file": file.filename,
                    "reason": f"Exceeds 50 MB limit ({len(content) / (1024 * 1024):.1f} MB)"
                })
                continue

            from io import BytesIO
            blob = bucket.blob(f"contracts/{file.filename}")
            blob.upload_from_file(BytesIO(content))
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
        "message": f"{len(uploaded)} file(s) uploaded to GCS and ingested into PineVector DB"
    }