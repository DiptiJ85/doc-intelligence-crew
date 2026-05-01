import streamlit as st
import requests
import os
import time

st.set_page_config(
    page_title="Document Intelligence Crew",
    page_icon="📄",
    layout="wide"
)

API_BASE = "http://localhost:8000"

st.title("📄 Document Intelligence Crew")
st.markdown("*Multi-agent AI system for enterprise contract analysis*")
st.divider()

with st.sidebar:
    st.header("⚙️ System Status")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=3)
        if response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline — run uvicorn app:app")

    st.divider()
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

# ── initialize session state FIRST ───────────────────
if "request_input" not in st.session_state:
    st.session_state.request_input = "Analyze all vendor contracts in our knowledge base. Identify critical risks, upcoming deadlines, compliance gaps, and provide a clear recommendation on which need immediate attention."

# ── Main Layout ───────────────────────────────────────
main_col1, main_col2 = st.columns([1, 1])  # ← renamed to avoid conflict


def set_prompt(prompt):
    st.session_state.user_request = prompt
    st.session_state.request_input = prompt  # ← also update the text area key directly


with main_col1:
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

    # quick prompt buttons — use different variable names
    st.markdown("**Quick prompts:**")
    prompt_col1, prompt_col2, prompt_col3 = st.columns(3)  # ← renamed

    with prompt_col1:
        st.button(
            "🔴 Critical risks",
            use_container_width=True,
            on_click=set_prompt,
            args=["Identify only CRITICAL and HIGH severity risks across all vendor contracts. What needs immediate attention in the next 48 hours?"]
        )
            

    with prompt_col2:
        st.button(
            "💰 Financial exposure",
            use_container_width=True,
            on_click=set_prompt,
            args=["What is our total financial exposure across all vendor contracts? Which contracts have the highest risk of unexpected costs?"]
        )
        
    with prompt_col3:
        st.button(
            "📋 Full analysis", 
            use_container_width=True,
            on_click=set_prompt,
            args=["Analyze all vendor contracts in our knowledge base. Identify critical risks, upcoming deadlines, compliance gaps, and provide a clear recommendation."]
        )

    # text area — always rendered, reads from session state
    user_request = st.text_area(
        "Or type your own request:",
        height=150,
        key="request_input"
    )

    # analyze button — outside any column
    analyze_btn = st.button(
        "🚀 Analyze Contracts",
        use_container_width=True,
        type="primary"
    )


with main_col2:
    st.subheader("📊 Analysis Results")

    if analyze_btn:
        if not user_request.strip():
            st.warning("Please enter a request first")
        else:
            st.markdown("**🤖 Agent Pipeline**")
            agents = [
                ("RAG Agent",        "Retrieving contract information..."),
                ("Extractor Agent",  "Extracting structured data..."),
                ("Analyst Agent",    "Analyzing risks..."),
                ("Action Agent",     "Building action plan..."),
                ("Summary Agent",    "Writing executive summary..."),
            ]

            placeholders = []
            for agent_name, _ in agents:
                ph = st.empty()
                ph.info(f"⏳ {agent_name} — waiting...")
                placeholders.append(ph)

            st.divider()
            result_placeholder = st.empty()

            with st.spinner("Running multi-agent analysis..."):
                try:
                    for i, (agent_name, message) in enumerate(agents):
                        placeholders[i].warning(f"🔄 {agent_name} — {message}")
                        time.sleep(0.5)

                    response = requests.post(
                        f"{API_BASE}/analyze",
                        json={"user_request": user_request},
                        timeout=300
                    )
                    # handle non-200 responses
                    if response.status_code != 200:
                        result_placeholder.error(f"API error: {response.status_code}")
                    else:
                        result = response.json()

                    for i, (agent_name, _) in enumerate(agents):
                        placeholders[i].success(f"✅ {agent_name} — complete")

                    if result["status"] == "success":
                        result_placeholder.success("✅ Analysis Complete!")
                        st.subheader("📋 Executive Summary")
                        st.markdown(result["summary"])
                        st.download_button(
                            label="⬇️ Download Report",
                            data=result["summary"],
                            file_name="contract_analysis_report.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    elif result["status"] == "error":
                        msg = result.get("message", "Unknown error")
                        if "429" in msg or "quota" in msg.lower():
                            result_placeholder.warning("⚠️ Rate limit reached — please wait 2 minutes and try again")
                        elif "503" in msg:
                            result_placeholder.warning("⚠️ Gemini API overloaded — please wait 2-3 minutes and try again")
                        else:
                            result_placeholder.error(f"Analysis failed: {msg}")

                except requests.exceptions.Timeout:
                    result_placeholder.error("⏱️ Request timed out — agents may still be running")
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower():
                        result_placeholder.warning("""
                        ⚠️ **Rate limit reached**
                        
                        Gemini API free tier has a request limit. 
                        
                        **Options:**
                        - Wait 1-2 minutes and try again
                        - The system will auto-retry shortly
                        """)
                    elif "503" in error_msg:
                        result_placeholder.warning("""
                        ⚠️ **Gemini API temporarily overloaded**
                        
                        Please wait 2-3 minutes and try again.
                        """)
                    else:
                        result_placeholder.error(f"Error: {error_msg}")
    else:
        st.info("👈 Upload documents and click **Analyze Contracts** to start")