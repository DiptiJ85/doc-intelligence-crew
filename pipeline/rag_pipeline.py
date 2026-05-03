import fitz
from docx import Document
import openpyxl
import google.generativeai as genai
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../env", ".env"))


# ── Constants ─────────────────────────────────────────

BUCKET_NAME = "document-intelligence-crew-data"
TMP_FOLDER = "/tmp/contracts"
COLLECTION_NAME = "contract_docs"
SUPPORTED_FORMATS = {".pdf", ".docx", ".xlsx"}
INDEX_NAME = os.environ.get("PINECONE_INDEX", "doc-intelligence")


# ── Pinecone + Gemini setup ───────────────────────────
def get_pinecone_index():
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    return pc.Index(INDEX_NAME)

def get_embedding(text: str) -> list:
    """Generate embedding using Gemini"""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]

def download_from_gcs():
    """Download all contracts from GCS to local tmp folder"""
    os.makedirs(TMP_FOLDER, exist_ok=True)
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix="contracts/")

    downloaded = []
    for blob in blobs:
        filename = os.path.basename(blob.name)
        ext = os.path.splitext(filename)[1].lower()
        if ext in SUPPORTED_FORMATS:
            local_path = os.path.join(TMP_FOLDER, filename)
            blob.download_to_filename(local_path)
            downloaded.append(filename)
            print(f"  ✅ Downloaded: {filename}")

    print(f"\n✅ Downloaded {len(downloaded)} files from GCS")
    return TMP_FOLDER

#Extractors
def extract_pdf(filepath):
    """Extract text from PDF file using pymupdf"""
    doc =fitz.open(filepath)
    sections=[]
    for page_num, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            sections.append(
                {
                    "content" : text,
                    "section_type" : "page",
                    "section_id" : f"page_{page_num+1}"
                }
            )
    doc.close()
    print(f"PDF extracted : {len(sections)} pages extracted")
    return sections

def extract_docx(filepath):
    doc = Document(filepath)
    sections = []
    current_heading = "Introduction"
    current_content = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        # detect headings
        if para.style.name.startswith("Heading"):
            # save previous section
            if current_content:
                sections.append({
                    "content": "\n".join(current_content),
                    "section_type": "heading_section",
                    "section_id": current_heading
                })
            current_heading = text
            current_content = []
        else:
            current_content.append(text)

    # also extract tables as their own sections
    for i, table in enumerate(doc.tables):
        rows = []
        for row in table.rows:
            row_text = " | ".join(
                cell.text.strip() for cell in row.cells if cell.text.strip()
            )
            if row_text:
                rows.append(row_text)
        if rows:
            sections.append({
                "content": "\n".join(rows),
                "section_type": "table",
                "section_id": f"table_{i+1}"
            })

    # save last section
    if current_content:
        sections.append({
            "content": "\n".join(current_content),
            "section_type": "heading_section",
            "section_id": current_heading
        })

    print(f"✅ DOCX: {len(sections)} sections extracted")
    return sections

def extract_xlsx(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)
    sections = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            row_values = [str(cell) for cell in row if cell is not None]
            if row_values:
                rows.append(" | ".join(row_values))
        if rows:
            sections.append({
                "content": "\n".join(rows),
                "section_type": "sheet",
                "section_id": sheet_name
            })

    print(f"✅ XLSX: {len(sections)} sheets extracted")
    return sections

def load_all_documents(folder_path):
    SUPPORTED_FORMATS = {".pdf", ".docx", ".xlsx"}
    documents = {} 
    files = [
        f for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS
    ]
    
    print(f"📁 Found {len(files)} files in '{folder_path}'")
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".pdf":
                documents[filename] = extract_pdf(filepath)
            elif ext == ".docx":
                documents[filename] = extract_docx(filepath)
            elif ext == ".xlsx":
                documents[filename] = extract_xlsx(filepath)
        except Exception as e:
            print(f"❌ Failed: {filename} — {e}")
    
    print(f"✅ Loaded {len(documents)} documents")
    return documents   

#-- chunker --------
def chunk_sections(sections, source_filename, chunk_size=200, overlap=50):
    """
    Chunks within each section separately.
    Sections never bleed into each other.
    """
    all_chunks = []

    for section in sections:
        content = section["content"].strip()
        if not content:
            continue

        words = content.split()

        if len(words) <= chunk_size:
            # entire section fits — keep as one chunk
            all_chunks.append({
                "content": content,
                "source": source_filename,
                "section_type": section["section_type"],
                "section_id": section["section_id"]
            })
        else:
            # section too large — split with overlap
            start = 0
            part = 0
            while start < len(words):
                end = start + chunk_size
                chunk = " ".join(words[start:end])
                all_chunks.append({
                    "content": chunk,
                    "source": source_filename,
                    "section_type": section["section_type"],
                    "section_id": f"{section['section_id']}_part_{part}"
                })
                start += chunk_size - overlap
                part += 1

    return [c for c in all_chunks if len(c["content"].strip()) > 50]


# ── Pinecone Storage ──────────────────────────────────
def store_in_pinecone(all_chunks):
    index = get_pinecone_index()

    # clear existing vectors only if present
    stats = index.describe_index_stats()
    if stats["total_vector_count"] > 0:
        print("🧹  Clearing existing vectors...")
        index.delete(delete_all=True)
        print("🗑️  Cleared existing vectors")
    else:
        print("Index is empty - skipping delete")    

    # embed and store in batches of 50
    batch_size = 50
    vectors = []

    for i, chunk in enumerate(all_chunks):
        print(f"  Embedding chunk {i+1}/{len(all_chunks)}...")
        embedding = get_embedding(chunk["content"])
        vectors.append({
            "id": f"{chunk['source']}_chunk_{i}",
            "values": embedding,
            "metadata": {
                "content": chunk["content"],
                "source": chunk["source"],
                "section_type": chunk["section_type"],
                "section_id": chunk["section_id"],
                "format": os.path.splitext(chunk["source"])[1].lower()
            }
        })

        # store in batches
        if len(vectors) >= batch_size:
            index.upsert(vectors=vectors)
            print(f"  ✅ Stored batch of {len(vectors)}")
            vectors = []

    # store remaining
    if vectors:
        index.upsert(vectors=vectors)
        print(f"  ✅ Stored final batch of {len(vectors)}")

    stats = index.describe_index_stats()
    print(f"\n✅ Total vectors in Pinecone: {stats['total_vector_count']}")

# ── Main Pipeline ─────────────────────────────────────
def run_pipeline():
    print("\n" + "=" * 60)
    print("DOCUMENT INTELLIGENCE — RAG PIPELINE")
    print("=" * 60)

    # Step 0 — Load all documents from GCS
    data_folder = download_from_gcs()

    # Step 1 — Load all documents
    documents = load_all_documents(data_folder)

    # Step 2 — Chunk all documents
    all_chunks = []

    print("\n📄 Chunking documents...")
    for doc_name, sections in documents.items():
        chunks = chunk_sections(sections, doc_name)
        all_chunks.extend(chunks)
        print(f"  {doc_name}: {len(chunks)} chunks")

    print(f"\n✅ Total chunks: {len(all_chunks)}")

    # Step 3 — Store in Pinecone
    print("\n💾 Storing in PineCone...")
    store_in_pinecone(all_chunks)

    print("\n🎉 Pipeline complete! PineVector DB ready for agent queries.")

if __name__ == "__main__":
    run_pipeline()