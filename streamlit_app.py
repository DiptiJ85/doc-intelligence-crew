import streamlit as st
import requests
import os
import time

st.set_page_config(
    page_title="Document Intelligence Crew",
    page_icon="📄",
    layout="wide"
)

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.title("📄 Document Intelligence Crew")
st.markdown("*Multi-agent AI system for enterprise contract analysis*")
st.divider()

with st.sidebar:
    st.header("⚙️ System Status")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=30)
        if response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline — run uvicorn app:app")

    st.divider()
    st.header("📁 Documents in System")
    doc_count = 0
    try:
        docs_response = requests.get(f"{API_BASE}/documents", timeout=3)
        if docs_response.status_code == 200:
            data = docs_response.json()
            doc_count = data["count"]
            st.metric("Total Documents", doc_count)
            for doc in data["documents"]:
                ext = os.path.splitext(doc)[1].upper()
                icon = "📕" if ext == ".PDF" else "📘" if ext == ".DOCX" else "📗"
                st.write(f"{icon} {doc}")
    except:
        st.warning("Could not fetch documents")

# ── Session state defaults ────────────────────────────────────────────────────
_defaults = {
    "request_input": (
        "Analyze all vendor contracts in our knowledge base. Identify critical risks, "
        "upcoming deadlines, compliance gaps, and provide a clear recommendation on which "
        "need immediate attention."
    ),
    "job_id": None,           # UUID of the running/completed job
    "analysis_result": None,  # result dict once job succeeds
    "analysis_error": None,   # error message if job failed
}
for key, default in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

job_running = st.session_state.job_id is not None

AGENTS = [
    ("RAG Agent",       "Retrieving contract information..."),
    ("Extractor Agent", "Extracting structured data..."),
    ("Analyst Agent",   "Analyzing risks..."),
    ("Action Agent",    "Building action plan..."),
    ("Summary Agent",   "Writing executive summary..."),
]

# ── Main Layout ───────────────────────────────────────────────────────────────
main_col1, main_col2 = st.columns([1, 1])


def set_prompt(prompt):
    st.session_state.request_input = prompt


with main_col1:
    st.subheader("📤 Upload Contracts")
    uploaded_files = st.file_uploader(
        "Drop your contract files here",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, XLSX"
    )

    if uploaded_files:
        MAX_MB = 50
        oversized = [f for f in uploaded_files if f.size > MAX_MB * 1024 * 1024]
        valid_files = [f for f in uploaded_files if f.size <= MAX_MB * 1024 * 1024]

        if oversized:
            names = ", ".join(f.name for f in oversized)
            st.error(f"These files exceed the {MAX_MB} MB limit and will be skipped: {names}")

        if not valid_files:
            st.button("📥 Upload & Ingest", use_container_width=True, disabled=True)
        else:
            label = (
                f"📥 Upload {len(valid_files)} valid file(s) & Ingest"
                if oversized
                else "📥 Upload & Ingest"
            )
            if st.button(label, use_container_width=True, disabled=job_running):
                with st.spinner("Uploading and ingesting documents..."):
                    files = [
                        ("files", (f.name, f.getvalue(), f.type))
                        for f in valid_files
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

    st.markdown("**Quick prompts:**")
    prompt_col1, prompt_col2, prompt_col3 = st.columns(3)

    with prompt_col1:
        st.button(
            "🔴 Critical risks",
            use_container_width=True,
            on_click=set_prompt,
            args=["Identify only CRITICAL and HIGH severity risks across all vendor contracts. What needs immediate attention in the next 48 hours?"],
            disabled=job_running,
        )

    with prompt_col2:
        st.button(
            "💰 Financial exposure",
            use_container_width=True,
            on_click=set_prompt,
            args=["What is our total financial exposure across all vendor contracts? Which contracts have the highest risk of unexpected costs?"],
            disabled=job_running,
        )

    with prompt_col3:
        st.button(
            "📋 Full analysis",
            use_container_width=True,
            on_click=set_prompt,
            args=["Analyze all vendor contracts in our knowledge base. Identify critical risks, upcoming deadlines, compliance gaps, and provide a clear recommendation."],
            disabled=job_running,
        )

    user_request = st.text_area(
        "Or type your own request:",
        height=150,
        key="request_input",
        disabled=job_running,
    )

    if not job_running:
        no_docs = doc_count == 0
        analyze_btn = st.button(
            "🚀 Analyze Contracts",
            use_container_width=True,
            type="primary",
            disabled=no_docs,
            help="Upload documents first to enable analysis." if no_docs else None,
        )
        cancel_btn = False
    else:
        analyze_btn = False
        cancel_btn = st.button(
            "🛑 Cancel Analysis",
            use_container_width=True,
            help="Signals agents to stop. The current LLM call finishes before cancellation takes effect.",
        )


# ── Results column ────────────────────────────────────────────────────────────
with main_col2:
    st.subheader("📊 Analysis Results")

    # ── Cancel: signal backend, then reset state ──────────────────────────────
    if cancel_btn and st.session_state.job_id:
        try:
            requests.post(
                f"{API_BASE}/analyze/cancel/{st.session_state.job_id}",
                timeout=5,
            )
        except Exception:
            pass  # best-effort; clean up UI regardless
        st.session_state.job_id = None
        st.session_state.analysis_result = None
        st.session_state.analysis_error = "Cancelled by user"
        st.rerun()

    # ── Start: kick off a new background job ─────────────────────────────────
    if analyze_btn:
        if not user_request.strip():
            st.warning("Please enter a request first")
        else:
            try:
                resp = requests.post(
                    f"{API_BASE}/analyze/start",
                    json={"user_request": user_request},
                    timeout=15,
                )
                if resp.status_code == 200:
                    st.session_state.job_id = resp.json()["job_id"]
                    st.session_state.analysis_result = None
                    st.session_state.analysis_error = None
                    st.rerun()
                else:
                    st.error(f"Failed to start analysis: {resp.text}")
            except Exception as e:
                st.error(f"Could not reach API: {e}")

    # ── Poll: job is running ──────────────────────────────────────────────────
    elif st.session_state.job_id is not None:
        st.markdown("**🤖 Agent Pipeline**")
        for agent_name, message in AGENTS:
            st.warning(f"🔄 {agent_name} — {message}")

        try:
            status_resp = requests.get(
                f"{API_BASE}/analyze/status/{st.session_state.job_id}",
                timeout=10,
            )
            if status_resp.status_code == 200:
                data = status_resp.json()

                if data["status"] == "running":
                    msg = data.get("message", "")
                    hint = f" — {msg}" if msg else ""
                    st.divider()
                    st.caption(f"⏱️ Multi-agent pipeline running{hint}. This typically takes 5–15 minutes.")
                    time.sleep(3)
                    st.rerun()

                elif data["status"] == "success":
                    st.session_state.analysis_result = data
                    st.session_state.job_id = None
                    st.rerun()

                elif data["status"] in ("error", "cancelled"):
                    st.session_state.analysis_error = data.get("message", data["status"])
                    st.session_state.job_id = None
                    st.rerun()

            else:
                st.error(f"Status check failed ({status_resp.status_code}) — clearing job")
                st.session_state.job_id = None
        except Exception as e:
            st.error(f"Error polling status: {e}")
            st.session_state.job_id = None

    # ── Done: show result ─────────────────────────────────────────────────────
    elif st.session_state.analysis_result is not None:
        result = st.session_state.analysis_result
        st.markdown("**🤖 Agent Pipeline**")
        for agent_name, _ in AGENTS:
            st.success(f"✅ {agent_name} — complete")

        st.divider()
        result_placeholder = st.empty()
        result_placeholder.success("✅ Analysis Complete!")
        st.subheader("📋 Executive Summary")
        st.markdown(result["summary"])
        st.download_button(
            label="⬇️ Download Report",
            data=result["summary"],
            file_name="contract_analysis_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # ── Error / cancelled ─────────────────────────────────────────────────────
    elif st.session_state.analysis_error is not None:
        error_msg = st.session_state.analysis_error
        if error_msg == "Cancelled by user":
            st.warning("⚠️ Analysis was cancelled.")
        elif "429" in error_msg or "quota" in error_msg.lower():
            st.warning("⚠️ Rate limit reached — please wait 2 minutes and try again")
        elif "503" in error_msg:
            st.warning("⚠️ Gemini API overloaded — please wait 2-3 minutes and try again")
        else:
            st.error(f"Analysis failed: {error_msg}")

    # ── Idle ──────────────────────────────────────────────────────────────────
    else:
        st.info("👈 Upload documents and click **Analyze Contracts** to start")
