# 📄 Document Intelligence Crew

![Python](https://img.shields.io/badge/Python-3.12-blue)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-green)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-orange)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4)

> A production-grade multi-agent AI system for enterprise contract analysis.
> Upload vendor contracts (PDF, DOCX, XLSX) and get instant risk assessment,
> compliance flags, and executive recommendations — powered by Agentic RAG
> and a 5-agent CrewAI pipeline.

---

## 🏗️ Architecture

📄 Documents (PDF + DOCX + XLSX)
↓
[RAG Pipeline]   → chunk → embed → ChromaDB
↓
[RAG Agent]      → autonomous search + rerank + reflect
↓
[Extractor]      → ExtractedDoc (Pydantic)
↓
[Analyst]        → AnalysisResult (Pydantic)
↓
[Action Planner] → ActionPlan (Pydantic)
↓
[Summary Agent]  → Executive Report
↓
[FastAPI]        → REST endpoints
[Streamlit]      → Interactive UI

---

## ✨ Key Features

- **Multi-Agent Orchestration** — 5 specialized CrewAI agents with typed handoffs
- **Agentic RAG** — autonomous retrieval with re-ranking and self-reflection
- **Multi-Format Ingestion** — PDF, DOCX, XLSX document support
- **Pydantic Typed Contracts** — strongly typed inter-agent schemas
- **Vector Semantic Search** — ChromaDB + Google text-embedding-001
- **Re-ranking** — cross-encoder scoring for precision retrieval
- **Self-Reflection** — agent evaluates its own retrieval completeness
- **REST API** — FastAPI with 4 endpoints + Swagger docs
- **Interactive UI** — Streamlit with file upload and live agent traces
- **PII Detection** — sensitive data flagged in contract analysis
- **Structured Logging** — timestamped log files per run

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Agent Orchestration** | CrewAI |
| **LLM** | Google Gemini 2.5 Flash |
| **Embeddings** | Google gemini-embedding-001 |
| **Vector Store** | ChromaDB |
| **RAG Strategy** | Agentic RAG + Re-ranking + Reflection |
| **Typed Contracts** | Pydantic AI |
| **Backend API** | FastAPI + Uvicorn |
| **Frontend UI** | Streamlit |
| **Document Parsing** | PyMuPDF, python-docx, openpyxl |
| **Observability** | Structured logging |
| **Language** | Python 3.12 |

---

## 📁 Project Structure
doc-intelligence-crew/
├── agents/                    # CrewAI agent definitions
│   ├── rag_agent.py           # Agentic RAG with search + rerank + reflect
│   ├── extractor_agent.py     # Contract data extraction
│   ├── analyst_agent.py       # Risk classification
│   ├── action_agent.py        # Action planning
│   └── summary_agent.py      # Executive summary
├── tasks/                     # Task definitions per agent
├── schemas/                   # Pydantic typed inter-agent contracts
│   └── contract_schemas.py    # ExtractedDoc, AnalysisResult, ActionPlan
├── tools/                     # CrewAI tools
│   ├── search_tool.py         # ChromaDB semantic search
│   ├── reranker_tool.py       # Cross-encoder re-ranking
│   └── reflection_tool.py     # Coverage self-reflection
├── config/                    # Configuration
│   └── llm_config.py          # LLM + ChromaDB setup
├── pipeline/                  # RAG ingestion pipeline
│   └── rag_pipeline.py        # Load → chunk → embed → store
├── api/                       # FastAPI routes
│   └── routes/
│       ├── analyze.py         # POST /analyze
│       ├── documents.py       # GET /documents, POST /upload
│       └── health.py          # GET /health
├── data/                      # Contract documents (PDF, DOCX, XLSX)
├── logs/                      # Timestamped run logs
├── app.py                     # FastAPI entry point
├── streamlit_app.py           # Streamlit UI
└── orchestrator.py            # Full crew orchestration

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Google Gemini API key ([get one here](https://aistudio.google.com))

### Installation

```bash
# clone the repo
git clone https://github.com/YOUR_USERNAME/doc-intelligence-crew.git
cd doc-intelligence-crew

# create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# create env file
mkdir env
cp .env.example env/.env

# add your API keys
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_API_KEY=your-gemini-api-key
CHROMA_GOOGLE_GENAI_API_KEY=your-gemini-api-key
```

### Run

```bash
# Step 1 — ingest documents into ChromaDB
python pipeline/rag_pipeline.py

# Step 2 — start FastAPI backend
uvicorn app:app --reload --port 8000

# Step 3 — start Streamlit UI (new terminal)
streamlit run streamlit_app.py
```

Open 👉 `http://localhost:8501`

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check |
| `GET` | `/documents` | List ingested documents |
| `POST` | `/documents/upload` | Upload new contracts |
| `POST` | `/ingest` | Re-ingest all documents |
| `POST` | `/analyze` | Run full 5-agent analysis |

Interactive docs: `http://localhost:8000/docs`

---

## 📊 Results

| Metric | Value |
|---|---|
| Documents supported | PDF, DOCX, XLSX |
| Agents in pipeline | 5 |
| Avg retrieval precision | High (re-ranked) |
| Contracts analyzed | 6 vendor contracts |
| Total contract value analyzed | $25.1M |
| Risk findings identified | 35+ across all contracts |
| PII elements detected | SSN, Email, Phone, Bank Account |

---

## 🤖 Agent Pipeline

| Agent | Role | Output Schema |
|---|---|---|
| RAG Agent | Autonomous retrieval + rerank + reflect | Raw context |
| Extractor Agent | Structured data extraction | `ExtractedDoc` |
| Analyst Agent | Risk classification by severity | `AnalysisResult` |
| Action Agent | Prioritized action planning | `ActionPlan` |
| Summary Agent | Executive brief | Plain prose |

---

## 👩‍💻 Author

**Dipti Joshi**
Senior Software Engineer → Agentic AI Engineer
[LinkedIn](https://linkedin.com/in/joshidipti) | [GitHub](https://github.com/diptij85)