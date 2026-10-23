import os
import streamlit as st
import requests
import time
import uuid
import logfire
from dotenv import load_dotenv


# Load environment variables without overriding existing container environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path=env_path, override=False)


# Initialize Logfire safely
token = os.getenv("LOGFIRE_TOKEN")
if token:
    try:
        logfire.configure(token=token)
        LOGFIRE_STATUS = "Connected & Tracing"
    except Exception as e:
        LOGFIRE_STATUS = f"Standby ({e})"
else:
    try:
        logfire.configure(send_to_logfire=False)
    except Exception:
        pass
    LOGFIRE_STATUS = "Offline (Local Only)"


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Enterprise AI Security & Multi-Agent RAG",
    page_icon="🛡️",
    layout="wide",
)

# --- AVATARS ---
AI_AVATAR = "🛡️"
USER_AVATAR = "👤"


@st.cache_resource(ttl=15)
def get_backend_url() -> str:
    """
    Dynamically auto-detects the active FastAPI backend URL across local and container networks.
    Ensures zero 'Connection Failed' errors whether running locally (port 8000/8080) or in Docker (api:8080).
    """
    explicit = os.getenv("BACKEND_URL", "").strip().rstrip("/")
    candidates = []
    if explicit:
        candidates.append(explicit)
    
    # Priority network candidates
    candidates.extend([
        "http://api:8080",        # Docker internal network (deploy.sh / compose)
        "http://127.0.0.1:8000",  # Local main.py default port
        "http://127.0.0.1:8080",  # Local docker port-forward / uvicorn
        "http://localhost:8000",  # Localhost fallback
        "http://localhost:8080",
    ])
    
    for cand in candidates:
        try:
            r = requests.get(f"{cand}/health", timeout=1.2)
            if r.status_code == 200:
                return cand
        except Exception:
            continue
            
    return explicit or "http://127.0.0.1:8000"


# --- SESSION MANAGEMENT ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    logfire.info(f"✨ New User Session Created: {st.session_state.session_id}")

if "messages" not in st.session_state:
    st.session_state.messages = []


# --- SIDEBAR: SYSTEM HEALTH & TELEMETRY ---
active_backend = get_backend_url()

with st.sidebar:
    st.title("🛡️ SecOps Control Plane")
    st.markdown("---")
    
    # Backend Connectivity Badge
    try:
        health_res = requests.get(f"{active_backend}/health", timeout=1.5)
        if health_res.status_code == 200:
            h_data = health_res.json()
            st.success(f"🟢 Backend Online: `{active_backend}`")
            st.caption(f"**WAF:** `{h_data.get('bot_shield', 'active')}` | **Guardrails:** `{h_data.get('guardrails', 'ready')}`")
        else:
            st.warning(f"🟡 Backend Responding HTTP {health_res.status_code}")
    except Exception:
        st.error(f"🔴 Backend Offline (`{active_backend}`)")

    st.info(f"Logfire: {LOGFIRE_STATUS}")
    st.caption(f"**Session ID:** `{st.session_state.session_id[:8]}`")
    
    st.markdown("---")
    st.subheader("⚡ Multi-Agent Ecosystem")
    st.markdown("""
    - 👑 **Security Supervisor** (LangGraph)
    - 🕵️ **Threat Researcher** (Tavily + Serper)
    - 💥 **Exploit Analyst** (OWASP LLM)
    - 📚 **Retrieval Agent** (Hybrid RRF)
    - ⚖️ **Compliance Auditor** (NIST AI RMF)
    - 🛠️ **Remediation Patcher** (WAF Rules)
    """)
    
    st.markdown("---")
    if st.button("🗑️ Clear History & Memory", width="stretch", type="primary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()


# --- MAIN CHAT INTERFACE ---
st.title("🛡️ Enterprise AI Security & Production Agentic RAG")
st.caption("Powered by LangGraph Supervisor, NVIDIA NeMo Guardrails, BotShield WAF, and Hybrid Re-Ranking (Cohere v3.5 + FlashRank).")

# Display conversation history
for message in st.session_state.messages:
    avatar = AI_AVATAR if message["role"] == "assistant" else USER_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# User Chat Input
if prompt := st.chat_input("Ask a technical security or cloud architecture question (e.g., CVE-2024-21413 mitigation)..."):
    with logfire.span("💬 User Chat Interaction", user_query=prompt, session_id=st.session_state.session_id):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        # Assistant Multi-Agent Response
        with st.chat_message("assistant", avatar=AI_AVATAR):
            with st.status("🔍 Autonomous Multi-Agent Network executing...", expanded=True) as status:
                data = {}
                try:
                    # Query execution with live backend detection
                    url = f"{active_backend}/query"
                    payload = {"q": prompt, "thread_id": st.session_state.session_id}
                    
                    t0 = time.perf_counter()
                    response = requests.post(url, json=payload, timeout=90)
                    elapsed_s = time.perf_counter() - t0
                    
                    if response.status_code != 200:
                        status.update(label=f"❌ Backend HTTP {response.status_code}", state="error")
                        st.error(f"Backend error: {response.text}")
                        st.stop()
                        
                    data = response.json()
                    
                    # Display multi-agent reasoning steps safely
                    steps = data.get("thought_process", [])
                    for step in steps:
                        st.write(f"⚙️ {step}")
                        
                    status.update(label=f"✅ Response Synthesized ({elapsed_s:.2f}s)", state="complete", expanded=False)

                    # --- SAFELY RENDER RETRIEVED SOURCES (DICT OR STR) ---
                    sources = data.get("sources", [])
                    if sources:
                        with st.expander(f"📚 Retrieved Knowledge & Policies ({len(sources)} sources)", expanded=False):
                            for i, source in enumerate(sources):
                                if isinstance(source, dict):
                                    title = source.get("title") or source.get("id") or f"Document {i+1}"
                                    content = source.get("content") or source.get("text") or str(source)
                                    score = source.get("rerank_score", 0.0)
                                    ranker = source.get("ranker", "hybrid_rrf")
                                    category = source.get("category", "Security Policy")
                                    with st.expander(f"📄 [{i+1}] {title} (Score: {score})"):
                                        st.caption(f"**Ranker:** `{ranker}` | **Category:** `{category}` | **ID:** `{source.get('id')}`")
                                        st.markdown(content)
                                elif isinstance(source, str):
                                    preview = source[:100].replace("\n", " ") + "..."
                                    with st.expander(f"📄 [{i+1}] {preview}"):
                                        st.info(source)

                except Exception as e:
                    logfire.error(f"❌ UI-Backend Execution Failed: {e}")
                    status.update(label="❌ Execution Failed", state="error")
                    st.error(f"Error communicating with backend at `{active_backend}`: {e}")
                    st.stop()

            # Final Answer Rendering
            full_answer = data.get("answer", "No response generated.")
            st.markdown(full_answer)
            st.session_state.messages.append({"role": "assistant", "content": full_answer})

            # Check for Human-In-The-Loop Interrupt Gate
            if data.get("hitl_pending"):
                action = data.get("hitl_action") or {}
                st.warning(f"⏸️ **High-Impact Action Awaiting Human Approval**: `{action.get('tool_name')}` (Severity: `{action.get('severity')}`)")
                if st.button("✅ Authorize & Deploy Action", key=f"hitl_{st.session_state.session_id}"):
                    try:
                        res_approve = requests.post(
                            f"{active_backend}/api/v1/hitl/approve",
                            json={
                                "thread_id": st.session_state.session_id,
                                "action_id": action.get("action_id"),
                                "decision": "approved",
                                "approver": "SecOps Supervisor"
                            },
                            timeout=10
                        )
                        if res_approve.status_code == 200:
                            st.success("Action Approved! Refreshing security perimeter...")
                            time.sleep(1)
                            st.rerun()
                    except Exception as app_err:
                        st.error(f"Approval failed: {app_err}")

            logfire.info("✅ Chat interaction completed successfully.")
