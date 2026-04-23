import streamlit as st
import requests
import os
import time

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="Document Intelligence Crew",
    page_icon="📄",
    layout="wide"
)

API_BASE = "http://localhost:8000"

# ── Header ────────────────────────────────────────────
st.title("📄 Document Intelligence Crew")
st.markdown("*Multi-agent AI system for enterprise contract analysis*")
st.divider()

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ System Status")

    # health check
    try:
        response = requests.get(f"{API_BASE}/health", timeout=3)
        if response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline — run uvicorn app:app")

    st.divider()

    # documents in system
    st.header("📁 Documents in System")
    try:
        docs_response = requests.get(f"{API_BASE}/documents", timeout=3)
        if docs_response.status_code == 200:
            data = docs_response.json()
            st.metric("Total Documents", data["count"])
            for doc in data["documents"]:
                ext = os.path.splitext(doc)[1].upper()
                icon = "📕" if ext == ".PDF" else "📘" if ext == ".DOCX" else "📗"
                st.write(f"{icon} {doc}")
    except:
        st.warning("Could not fetch documents")

# ── Main Layout ───────────────────────────────────────
col1, col2 = st.columns([1, 1])

# ── Left Column — Upload + Request ───────────────────
with col1:
    st.subheader("📤 Upload Contracts")
    uploaded_files = st.file_uploader(
        "Drop your contract files here",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, XLSX"
    )

    if uploaded_files:
        if st.button("📥 Upload & Ingest", use_container_width=True):
            with st.spinner("Uploading and ingesting documents..."):
                files = [
                    ("files", (f.name, f.getvalue(), f.type))
                    for f in uploaded_files
                ]
                try:
                    upload_response = requests.post(
                        f"{API_BASE}/documents/upload",
                        files=files,
                        timeout=120
                    )
                    result = upload_response.json()
                    if result["status"] == "success":
                        st.success(result["message"])
                        for doc in result["uploaded"]:
                            st.write(f"✅ {doc}")
                        st.rerun()
                    else:
                        st.error("Upload failed")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    st.subheader("💬 Your Request")
    user_request = st.text_area(
        "What would you like to analyze?",
        value="Analyze all vendor contracts in our knowledge base. Identify critical risks, upcoming deadlines, compliance gaps, and provide a clear recommendation on which contracts need immediate attention.",
        height=150
    )

    analyze_btn = st.button(
        "🚀 Analyze Contracts",
        use_container_width=True,
        type="primary"
    )

# ── Right Column — Results ────────────────────────────
with col2:
    st.subheader("📊 Analysis Results")

    if analyze_btn:
        if not user_request.strip():
            st.warning("Please enter a request first")
        else:
            # agent trace display
            st.markdown("**🤖 Agent Pipeline**")
            agents = [
                ("RAG Agent",        "Retrieving contract information..."),
                ("Extractor Agent",  "Extracting structured data..."),
                ("Analyst Agent",    "Analyzing risks..."),
                ("Action Agent",     "Building action plan..."),
                ("Summary Agent",    "Writing executive summary..."),
            ]

            # create placeholders for each agent
            placeholders = []
            for agent_name, _ in agents:
                ph = st.empty()
                ph.info(f"⏳ {agent_name} — waiting...")
                placeholders.append(ph)

            st.divider()
            result_placeholder = st.empty()

            # kick off analysis
            with st.spinner("Running multi-agent analysis..."):
                try:
                    # animate agent statuses
                    for i, (agent_name, message) in enumerate(agents):
                        placeholders[i].warning(f"🔄 {agent_name} — {message}")
                        time.sleep(0.5)

                    # call API
                    response = requests.post(
                        f"{API_BASE}/analyze",
                        json={"user_request": user_request},
                        timeout=300       # 5 min timeout for full crew run
                    )

                    result = response.json()

                    # mark all agents complete
                    for i, (agent_name, _) in enumerate(agents):
                        placeholders[i].success(f"✅ {agent_name} — complete")

                    if result["status"] == "success":
                        result_placeholder.success("✅ Analysis Complete!")
                        st.subheader("📋 Executive Summary")
                        st.markdown(result["summary"])

                        # download button
                        st.download_button(
                            label="⬇️ Download Report",
                            data=result["summary"],
                            file_name="contract_analysis_report.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    else:
                        result_placeholder.error(f"Analysis failed: {result['message']}")

                except requests.exceptions.Timeout:
                    result_placeholder.error("⏱️ Request timed out — agents may still be running")
                except Exception as e:
                    result_placeholder.error(f"Error: {e}")
    else:
        st.info("👈 Upload documents and click **Analyze Contracts** to start")