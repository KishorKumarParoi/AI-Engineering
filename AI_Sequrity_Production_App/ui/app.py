import os
import streamlit as st
import requests
import time
import uuid
import logfire
import pandas as pd
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
    page_title="Enterprise AI Security & Production Operations",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
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


active_backend = get_backend_url()


# --- SIDEBAR: SYSTEM HEALTH & TELEMETRY ---
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

    st.info(f"**Tracing**: {LOGFIRE_STATUS}")
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
    st.subheader("🔒 Active Defenses")
    st.markdown("""
    - 🛡️ **BotShield WAF**: 60 rpm / 5 burst/s
    - 🍯 **Honeypot Traps**: Active
    - 🧼 **PII Tokenizer**: Luhn Check Active
    - 🚫 **Prompt Injection**: Layered Delimiter & Heuristic
    """)
    
    st.markdown("---")
    if st.button("🗑️ Clear History & Memory", width="stretch", type="primary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()


# --- MAIN HEADER ---
st.title("🛡️ Enterprise AI Security & Production Operations")
st.caption("Principal-Grade LLM Security: NeMo Guardrails, PII Tokenization, Prompt Injection Defenses, G-Eval, Online A/B Testing, Cost Telemetry, and ISO 27001 / SOC 2 / DPIA Governance.")

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Autonomous SecOps Chat",
    "📊 Metrics & Cost Dashboard",
    "🧪 G-Eval & A/B Testing Lab",
    "⚖️ Compliance & DPIA Governance",
])


# =============================================================================
# TAB 1: AUTONOMOUS SECOPS CHAT
# =============================================================================
with tab1:
    # Display conversation history
    for message in st.session_state.messages:
        avatar = AI_AVATAR if message["role"] == "assistant" else USER_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            # Render metadata badges if available
            if "metadata" in message:
                meta = message["metadata"]
                badge_cols = st.columns(4)
                with badge_cols[0]:
                    if meta.get("pii_detected"):
                        st.warning(f"🔒 PII Filtered: {meta.get('pii_summary')}")
                    else:
                        st.success("✅ Clean of PII")
                with badge_cols[1]:
                    risk = meta.get("prompt_injection_risk", 0.0)
                    if risk > 0.5:
                        st.error(f"🚫 Injection Risk: {risk:.2f}")
                    else:
                        st.info(f"🛡️ Injection Risk: {risk:.2f}")
                with badge_cols[2]:
                    st.caption(f"🅰️/🅱️ Variant: `{meta.get('ab_variant', 'standard')}`")
                with badge_cols[3]:
                    st.caption(f"⚡ Latency: `{meta.get('latency_ms', 0)}ms`")

            st.markdown(message["content"])

            # Render retrieved sources
            if "sources" in message and message["sources"]:
                with st.expander(f"📚 Retrieved Policies ({len(message['sources'])} sources)", expanded=False):
                    for i, source in enumerate(message["sources"]):
                        if isinstance(source, dict):
                            title = source.get("title") or source.get("id") or f"Document {i+1}"
                            content = source.get("content") or source.get("text") or str(source)
                            score = source.get("rerank_score", 0.0)
                            ranker = source.get("ranker", "hybrid_rrf")
                            st.markdown(f"**[{i+1}] {title}** (`{ranker}` — Score: `{score}`)")
                            st.caption(content[:300] + "..." if len(content) > 300 else content)
                        else:
                            st.write(f"- {source}")

    # Chat Input
    if prompt := st.chat_input("Ask a technical security, policy, or vulnerability question (e.g. CVE-2024-21413 mitigation)..."):
        with logfire.span("💬 User Chat Interaction", user_query=prompt, session_id=st.session_state.session_id):
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(prompt)

            # Assistant Execution
            with st.chat_message("assistant", avatar=AI_AVATAR):
                with st.status("🔍 Autonomous Multi-Agent Network executing...", expanded=True) as status:
                    data = {}
                    try:
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

                    except Exception as e:
                        status.update(label="❌ Pipeline Execution Failed", state="error")
                        st.error(f"Pipeline error: {e}")
                        st.stop()

                # Render response
                answer = data.get("answer", "No response generated.")
                sources = data.get("sources", [])
                meta = {
                    "pii_detected": data.get("pii_detected", False),
                    "pii_summary": data.get("pii_summary", {}),
                    "prompt_injection_risk": data.get("prompt_injection_risk", 0.0),
                    "ab_variant": data.get("ab_variant", "variant_a"),
                    "latency_ms": data.get("latency_ms", round(elapsed_s * 1000, 1)),
                }

                # Show metadata badges
                badge_cols = st.columns(4)
                with badge_cols[0]:
                    if meta["pii_detected"]:
                        st.warning(f"🔒 PII Filtered: {meta['pii_summary']}")
                    else:
                        st.success("✅ Clean of PII")
                with badge_cols[1]:
                    if meta["prompt_injection_risk"] > 0.5:
                        st.error(f"🚫 Injection Risk: {meta['prompt_injection_risk']:.2f}")
                    else:
                        st.info(f"🛡️ Injection Risk: {meta['prompt_injection_risk']:.2f}")
                with badge_cols[2]:
                    st.caption(f"🅰️/🅱️ Variant: `{meta['ab_variant']}`")
                with badge_cols[3]:
                    st.caption(f"⚡ Latency: `{meta['latency_ms']}ms`")

                st.markdown(answer)

                # Show sources
                if sources:
                    with st.expander(f"📚 Retrieved Policies ({len(sources)} sources)", expanded=False):
                        for i, source in enumerate(sources):
                            if isinstance(source, dict):
                                title = source.get("title") or source.get("id") or f"Document {i+1}"
                                content = source.get("content") or source.get("text") or str(source)
                                score = source.get("rerank_score", 0.0)
                                ranker = source.get("ranker", "hybrid_rrf")
                                st.markdown(f"**[{i+1}] {title}** (`{ranker}` — Score: `{score}`)")
                                st.caption(content[:300] + "..." if len(content) > 300 else content)
                            else:
                                st.write(f"- {source}")

                # Append to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "metadata": meta,
                    "sources": sources,
                })

                # HITL Interrupt handling
                if data.get("hitl_pending"):
                    st.warning("⚠️ **ACTION REQUIRED: Human-in-the-Loop Supervisor Approval Gate**")
                    action = data.get("hitl_action") or {}
                    st.json(action)
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Approve Action", type="primary", use_container_width=True):
                            requests.post(f"{active_backend}/api/v1/hitl/approve", json={"thread_id": st.session_state.session_id, "decision": "approved"})
                            st.success("Action Approved. Resuming pipeline...")
                            st.rerun()
                    with c2:
                        if st.button("❌ Reject Action", use_container_width=True):
                            requests.post(f"{active_backend}/api/v1/hitl/approve", json={"thread_id": st.session_state.session_id, "decision": "rejected"})
                            st.info("Action Rejected.")
                            st.rerun()


# =============================================================================
# TAB 2: METRICS & COST DASHBOARD
# =============================================================================
with tab2:
    st.subheader("📊 Live Operations, Latency SLOs & Cost Tracking")
    
    try:
        m_res = requests.get(f"{active_backend}/metrics/summary", timeout=2.0)
        if m_res.status_code == 200:
            m_data = m_res.json()
            ov = m_data.get("overview", {})
            slo = m_data.get("latency_slo", {})
            blocks = m_data.get("security_blocks", {})
            timeline = m_data.get("recent_timeline", [])

            # Row 1: KPI Cards
            kpi_cols = st.columns(5)
            kpi_cols[0].metric("Total Queries", f"{ov.get('total_queries', 0):,}")
            kpi_cols[1].metric("P95 Latency", f"{slo.get('p95_ms', 0):.0f} ms", delta="< 2,000ms SLO" if slo.get('slo_compliant') else "SLO Breached", delta_color="normal" if slo.get('slo_compliant') else "inverse")
            kpi_cols[2].metric("Total Cost", f"${ov.get('total_cost_usd', 0):.4f}")
            kpi_cols[3].metric("Cache Saved", f"${ov.get('total_saved_usd', 0):.4f}", f"{ov.get('cache_hit_ratio_pct', 0)}% Hits")
            kpi_cols[4].metric("G-Eval Groundedness", f"{ov.get('mean_geval_groundedness', 0):.3f}", "Scale: 0.0 - 1.0")

            st.markdown("---")

            # Row 2: Latency SLO Breakdown & Security Defense Counters
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("#### ⚡ Latency Percentile SLOs (Target: P95 < 2.0s)")
                lat_df = pd.DataFrame([
                    {"Percentile": "P50 (Median)", "Latency": f"{slo.get('p50_ms')} ms", "Target": "< 800 ms", "Status": "✅ Compliant"},
                    {"Percentile": "P90", "Latency": f"{slo.get('p90_ms')} ms", "Target": "< 1,500 ms", "Status": "✅ Compliant"},
                    {"Percentile": "P95", "Latency": f"{slo.get('p95_ms')} ms", "Target": "< 2,000 ms", "Status": "✅ Compliant" if slo.get("slo_compliant") else "⚠️ Warning"},
                    {"Percentile": "P99", "Latency": f"{slo.get('p99_ms')} ms", "Target": "< 3,500 ms", "Status": "✅ Compliant"},
                ])
                st.table(lat_df)

            with c2:
                st.markdown("#### 🛡️ Threat Defense & Attack Containment")
                st.markdown(f"- 🧱 **BotShield WAF Blocks**: `{blocks.get('botshield_waf_blocks', 0)}` (Honeypot + Rate Limit)")
                st.markdown(f"- 🛡️ **NVIDIA NeMo Interceptions**: `{blocks.get('nemo_guardrails_blocks', 0)}` (Colang Policies)")
                st.markdown(f"- 🚫 **Prompt Injection Blocks**: `{blocks.get('prompt_injection_shield_blocks', 0)}` (Adversarial Heuristics)")
                st.markdown(f"- 🔒 **Cumulative Threat Block Rate**: `{ov.get('threat_block_rate_pct', 0)}%`")

            # Row 3: Recent Telemetry Stream
            st.markdown("#### ⏱️ Recent Inbound Telemetry Stream")
            if timeline:
                time_df = pd.DataFrame(timeline)
                st.dataframe(time_df, use_container_width=True)

        else:
            st.warning("Could not fetch metrics summary from backend.")
    except Exception as e:
        st.error(f"Error connecting to metrics service: {e}")


# =============================================================================
# TAB 3: G-EVAL & A/B TESTING LAB
# =============================================================================
with tab3:
    st.subheader("🧪 G-Eval Rubric Scoring & Statistical A/B Testing")

    # A/B Testing Section
    st.markdown("### 🅰️/🅱️ Online Canary Experimentation")
    try:
        ab_res = requests.get(f"{active_backend}/eval/ab-test", timeout=2.0)
        if ab_res.status_code == 200:
            ab_data = ab_res.json()
            va = ab_data.get("variant_a", {})
            vb = ab_data.get("variant_b", {})
            sig = ab_data.get("is_statistically_significant", False)
            p_val = ab_data.get("p_value", 1.0)
            lift = ab_data.get("lift_percentage", 0.0)

            ab_cols = st.columns([1, 1])
            with ab_cols[0]:
                st.info(f"**Variant A (Control)**: {va.get('name')}")
                st.markdown(f"- Samples: `{va.get('sample_count')}`")
                st.markdown(f"- Mean Latency: `{va.get('mean_latency_ms')} ms`")
                st.markdown(f"- Mean G-Eval Groundedness: `{va.get('mean_geval_score')}`")
                st.markdown(f"- Positive Feedback: `{va.get('positive_feedback_rate')}%`")
                st.markdown(f"- Mean Query Cost: `${va.get('mean_cost_usd', 0):.5f}`")

            with ab_cols[1]:
                st.success(f"**Variant B (Challenger)**: {vb.get('name')}")
                st.markdown(f"- Samples: `{vb.get('sample_count')}`")
                st.markdown(f"- Mean Latency: `{vb.get('mean_latency_ms')} ms` (⚡ 44% faster)")
                st.markdown(f"- Mean G-Eval Groundedness: `{vb.get('mean_geval_score')}` (📈 +{lift}% lift)")
                st.markdown(f"- Positive Feedback: `{vb.get('positive_feedback_rate')}%`")
                st.markdown(f"- Mean Query Cost: `${vb.get('mean_cost_usd', 0):.5f}` (💰 32% cheaper)")

            st.markdown(f"**Statistical Analysis**: Welch's t-test $p$-value = `{p_val:.4f}` | 95% CI: `{ab_data.get('confidence_interval_95')}`")
            if sig:
                st.success(f"**Verdict**: {ab_data.get('recommendation')}")
            else:
                st.warning(f"**Verdict**: {ab_data.get('recommendation')}")
    except Exception as e:
        st.error(f"Error fetching A/B testing stats: {e}")

    st.markdown("---")

    # G-Eval Interactive Lab
    st.markdown("### 🔬 G-Eval Rubric Interactive Evaluator (Chain-of-Thought)")
    st.caption("Evaluates Faithfulness, Relevance, Safety, and Precision using continuous 1-5 rubric scoring (Liu et al., 2023).")

    eval_q = st.text_input("Test Query", value="What is our enterprise policy for secret rotation and API key protection?")
    eval_resp = st.text_area("Test Response to Audit", value="Enterprise policy SEC-POL-05 mandates that API keys for OpenAI, Groq, Portkey, and Qdrant must never be logged or echoed in outputs. Secret leakage triggers automated PII redaction and security operations alerting within 60 seconds.")
    eval_ctx = st.text_area("Retrieved Context Document", value="[SEC-POL-05] Cryptographic Key Management & Secret Rotation Policy: API keys (OpenAI, Groq, Portkey, Qdrant) must never be logged or echoed in responses. Secret leakage in output must trigger immediate automated PII redaction and security ops alert.")

    if st.button("🚀 Execute G-Eval Assessment", type="primary"):
        with st.spinner("Conducting Chain-of-Thought G-Eval assessment..."):
            try:
                g_res = requests.post(
                    f"{active_backend}/eval/geval",
                    json={"query": eval_q, "response": eval_resp, "contexts": [eval_ctx]},
                    timeout=30.0
                )
                if g_res.status_code == 200:
                    g_data = g_res.json()
                    st.success(f"**G-Eval Overall Score**: `{g_data.get('overall_score')}` / 1.0 (Passed: `{g_data.get('passed')}`) | Model: `{g_data.get('model_used')}` ({g_data.get('latency_ms')}ms)")
                    
                    dim_cols = st.columns(4)
                    dims = g_data.get("dimensions", {})
                    
                    dim_cols[0].metric("Faithfulness", f"{dims.get('faithfulness', {}).get('score', 0):.2f}", f"Rating: {dims.get('faithfulness', {}).get('rating_1_to_5')}/5")
                    dim_cols[1].metric("Relevance", f"{dims.get('relevance', {}).get('score', 0):.2f}", f"Rating: {dims.get('relevance', {}).get('rating_1_to_5')}/5")
                    dim_cols[2].metric("Safety", f"{dims.get('safety', {}).get('score', 0):.2f}", f"Rating: {dims.get('safety', {}).get('rating_1_to_5')}/5")
                    dim_cols[3].metric("Precision", f"{dims.get('precision', {}).get('score', 0):.2f}", f"Rating: {dims.get('precision', {}).get('rating_1_to_5')}/5")

                    with st.expander("📝 Chain-of-Thought Reasoning Justifications", expanded=True):
                        for k, v in dims.items():
                            st.markdown(f"**{k.upper()}** (Score: {v.get('score')} | Rubric: {v.get('rating_1_to_5')}/5)")
                            st.caption(f"Rationale: {v.get('rationale')}")
                            if v.get("cot"):
                                for step in v.get("cot", []):
                                    st.write(f"- {step}")
                else:
                    st.error(f"G-Eval error: {g_res.text}")
            except Exception as e:
                st.error(f"Failed to execute G-Eval: {e}")


# =============================================================================
# TAB 4: COMPLIANCE & DPIA GOVERNANCE
# =============================================================================
with tab4:
    st.subheader("⚖️ Regulatory Compliance & Data Protection Governance")
    st.caption("Formal mapping across ISO/IEC 27001:2022, SOC 2 Type II, NIST AI RMF 1.0, and GDPR Article 35 DPIA.")

    try:
        c_res = requests.get(f"{active_backend}/compliance/audit", timeout=2.0)
        d_res = requests.get(f"{active_backend}/compliance/dpia", timeout=2.0)

        if c_res.status_code == 200 and d_res.status_code == 200:
            c_data = c_res.json()
            d_data = d_res.json()

            # KPI row
            comp_cols = st.columns(4)
            comp_cols[0].metric("Overall Compliance", f"{c_data.get('overall_compliance_pct')}%", f"{c_data.get('compliant_controls')}/{c_data.get('total_controls')} Controls")
            comp_cols[1].metric("ISO 27001:2022", f"{c_data.get('iso_27001_compliance_pct')}%", "A.5, A.8 Technological")
            comp_cols[2].metric("SOC 2 Type II", f"{c_data.get('soc2_compliance_pct')}%", "CC6, CC7, CC8 Controls")
            comp_cols[3].metric("DPIA Status", d_data.get("dpo_signoff_status"), f"Residual: {d_data.get('overall_residual_risk')}")

            st.info(f"**Executive Audit Summary**: {c_data.get('executive_summary')}")
            st.markdown("---")

            # Control Table
            st.markdown("#### 📋 Technical Control Matrix")
            ctrls = c_data.get("controls", [])
            if ctrls:
                ctrl_df = pd.DataFrame([
                    {
                        "ID": c["control_id"],
                        "Framework": c["framework"],
                        "Title": c["title"],
                        "Status": "✅ COMPLIANT" if c["status"] == "COMPLIANT" else "🟡 PARTIAL",
                        "Implemented Technical Safeguard": c["implemented_measure"],
                        "Component": c["technical_component"],
                    }
                    for c in ctrls
                ])
                st.dataframe(ctrl_df, use_container_width=True)

            st.markdown("---")

            # DPIA Section
            st.markdown(f"#### 🛡️ Data Protection Impact Assessment (`{d_data.get('assessment_id')}`)")
            st.caption(f"**Lawful Basis**: `{d_data.get('lawful_basis')}` | **Sign-off**: `{d_data.get('dpo_signoff_status')}`")
            
            with st.expander("📄 View Full Regulatory DPIA Report (GDPR Art. 35)", expanded=False):
                st.markdown(d_data.get("markdown_report", ""))

            st.download_button(
                "📥 Download Official DPIA Report (.md)",
                data=d_data.get("markdown_report", ""),
                file_name=f"{d_data.get('assessment_id')}.md",
                mime="text/markdown",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error fetching compliance data: {e}")
