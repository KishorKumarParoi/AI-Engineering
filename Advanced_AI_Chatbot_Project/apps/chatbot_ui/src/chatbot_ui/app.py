from __future__ import annotations
import json
import html
import logging
from typing import Any
import uuid
import requests
import streamlit as st

from chatbot_ui.core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="Ecommerce Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🛍️",
)

def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — premium design with polished feedback UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero {
        padding: 1.1rem 1.4rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #1e293b 100%);
        color: white;
        box-shadow: 0 16px 48px rgba(15,23,42,0.22);
        margin-bottom: 1.1rem;
        border: 1px solid rgba(99,179,237,0.12);
    }
    .hero h1 {
        margin: 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em;
        background: linear-gradient(90deg,#fff 60%,#93c5fd);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero p { margin: 0.4rem 0 0 0; color: rgba(255,255,255,0.72); font-size: 0.9rem; }

    .answer-card {
        border: 1px solid rgba(148,163,184,0.18); border-radius: 22px;
        padding: 1.1rem 1.2rem 1rem 1.2rem; background: #ffffff;
        box-shadow: 0 10px 28px rgba(15,23,42,0.06); margin-bottom: 0.9rem;
    }
    .pill-row { display:flex; flex-wrap:wrap; gap:0.45rem; margin-top:0.4rem; }
    .pill {
        border-radius:999px; padding:0.3rem 0.7rem; font-size:0.78rem;
        background:rgba(37,99,235,0.09); color:#1e3a5f;
        border:1px solid rgba(37,99,235,0.14); font-weight:500;
    }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:0.9rem; margin-top:0.8rem; }
    .card { border:1px solid rgba(148,163,184,0.16); border-radius:18px; overflow:hidden; background:white; box-shadow:0 6px 20px rgba(15,23,42,0.06); transition:box-shadow .2s; }
    .card:hover { box-shadow:0 12px 32px rgba(15,23,42,0.11); }
    .card img { width:100%; height:180px; object-fit:cover; background:#f8fafc; display:block; }
    .card-body { padding:0.85rem; }
    .card-title { font-weight:800; font-size:0.96rem; line-height:1.3; margin-bottom:0.35rem; color:#0f172a; }
    .card-meta { font-size:0.78rem; opacity:0.8; margin-bottom:0.4rem; color:#334155; }
    .card-desc { font-size:0.84rem; line-height:1.4; color:#334155; }
    .sidebar-title { font-weight:800; font-size:1rem; margin-bottom:0.1rem; color:#0f172a; }
    .sidebar-subtitle { font-size:0.82rem; color:#64748b; margin-bottom:0.75rem; }
    .sidebar-card { border:1px solid rgba(148,163,184,0.18); border-radius:16px; overflow:hidden; background:white; margin-bottom:0.8rem; }
    .sidebar-card img { width:100%; height:148px; object-fit:cover; display:block; background:#f8fafc; }
    .sidebar-card-body { padding:0.75rem; }
    .sidebar-card-title { font-weight:800; font-size:0.9rem; line-height:1.3; margin-bottom:0.25rem; }
    .sidebar-card-meta { font-size:0.76rem; opacity:0.8; margin-bottom:0.35rem; }
    .sidebar-badges { display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.35rem; }
    .sidebar-badge { padding:0.16rem 0.48rem; border-radius:999px; font-size:0.71rem; background:rgba(15,23,42,0.06); color:#0f172a; }

    /* ── Feedback UI ── */
    .feedback-divider {
        height: 1px; background: rgba(148,163,184,0.18);
        margin: 0.8rem 0 0.6rem 0;
    }
    .feedback-label {
        font-size: 0.78rem; color: #64748b; font-weight: 600;
        margin-bottom: 0.45rem; display: block;
        letter-spacing: 0.02em; text-transform: uppercase;
    }
    .fb-toast {
        display: flex; align-items: center; gap: 0.5rem;
        padding: 0.55rem 0.9rem; border-radius: 12px;
        font-size: 0.83rem; font-weight: 500;
        margin-top: 0.6rem; animation: slideIn 0.3s ease;
    }
    .fb-toast.success { background:#f0fdf4; border:1px solid #bbf7d0; color:#15803d; }
    .fb-toast.error   { background:#fef2f2; border:1px solid #fecaca; color:#b91c1c; }
    @keyframes slideIn {
        from { opacity:0; transform:translateY(-6px); }
        to   { opacity:1; transform:translateY(0); }
    }
    .feedback-panel {
        margin-top: 0.75rem; padding: 1rem 1.1rem; border-radius: 16px;
        background: linear-gradient(135deg,#fafafa 0%,#f1f5f9 100%);
        border: 1px solid rgba(148,163,184,0.22);
        box-shadow: 0 4px 14px rgba(15,23,42,0.05);
        animation: fadePanel 0.25s ease;
    }
    @keyframes fadePanel {
        from { opacity:0; transform:translateY(-4px); }
        to   { opacity:1; transform:translateY(0); }
    }
    .panel-title { font-weight:700; font-size:0.9rem; color:#1e293b; margin-bottom:0.15rem; }
    .panel-sub   { font-size:0.78rem; color:#64748b; margin-bottom:0.75rem; line-height:1.45; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def api_call(method: str, url: str, **kwargs):
    try:
        response = getattr(requests, method)(url, timeout=120, **kwargs)
        try:
            payload = response.json()
        except Exception:
            payload = {"message": "Invalid response format from server"}
        return response.ok, payload
    except requests.exceptions.RequestException as exc:
        return False, {"message": str(exc)}


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _ensure_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _image_url(item: dict) -> str | None:
    images = _as_list(item.get("images"))
    if not images:
        return None
    first = images[0]
    if isinstance(first, dict):
        return first.get("hi_res") or first.get("large") or first.get("thumb")
    if isinstance(first, str):
        return first
    return None


def _meta_text(item: dict) -> str:
    details = item.get("details") or {}
    bits = []
    for key, label in [
        ("price","Price"),("rating_number","Ratings"),("average_rating","Avg rating"),
        ("brand","Brand"),("size","Size"),("color","Color"),("store","Store"),("main_category","Category"),
    ]:
        value = item.get(key)
        if value not in (None, "", [], {}):
            bits.append(f"{label}: {value}")
    if isinstance(details, dict):
        for key in ["size","color","brand","material","style","capacity","storage"]:
            value = details.get(key)
            if value not in (None, "", [], {}):
                bits.append(f"{key.title()}: {value}")
    categories = item.get("categories") or []
    if isinstance(categories, list) and categories:
        bits.append(", ".join(str(x) for x in categories[:3] if x))
    return " • ".join(bits)


def _normalize_suggestions(response_data: dict) -> list[dict]:
    suggestions: list[dict] = []
    if not isinstance(response_data, dict):
        return suggestions
    explicit = response_data.get("suggestions")
    if isinstance(explicit, list) and explicit:
        for item in explicit:
            if isinstance(item, str) and item.strip():
                suggestions.append({
                    "id": item[:40], "title": item.strip(), "text": item.strip(),
                    "images": [], "features": [], "price": None,
                    "rating_number": None, "size": "", "brand": "", "color": "", "details": {},
                })
        return suggestions
    used_context = response_data.get("used_context", []) or []
    if not isinstance(used_context, list):
        return suggestions
    for item in used_context:
        if not isinstance(item, dict):
            continue
        description = item.get("description", "")
        if isinstance(description, list):
            description = " ".join(str(x) for x in description if x)
        suggestions.append({
            "id": item.get("id", ""),
            "title": item.get("title") or item.get("review", "")[:80] or "Product",
            "text": item.get("review", ""),
            "images": item.get("images", []),
            "features": item.get("features", []),
            "price": item.get("price"),
            "rating_number": item.get("rating_number"),
            "size": item.get("size", ""),
            "brand": item.get("brand", ""),
            "color": item.get("color", ""),
            "details": item.get("details", {}),
            "description": description,
            "store": item.get("store", ""),
            "main_category": item.get("main_category", ""),
            "categories": item.get("categories", []),
        })
    return suggestions


def api_call_stream(method: str, url: str, **kwargs):
    """Make a streaming HTTP request and yield raw line bytes."""
    try:
        with getattr(requests, method)(url, timeout=120, **kwargs) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    yield line
    except requests.exceptions.RequestException as exc:
        import json as _json
        error_event = _json.dumps({"type": "error", "data": {"message": str(exc)}})
        yield f"data: {error_event}".encode("utf-8")


def submit_feedback(feedback_type=None, feedback_text=""):
    """Submit feedback to the API endpoint."""
    def _score(ft):
        if ft == "positive": return 1
        if ft == "negative": return 0
        return None

    feedback_data = {
        "feedback_score": _score(feedback_type),
        "feedback_text": feedback_text,
        "trace_id": st.session_state.trace_id,
        "thread_id": st.session_state.session_id,
        "feedback_source_type": "api",
    }
    logger.info(f"Feedback Data: {feedback_data}")
    status, response = api_call("post", f"{config.API_URL}/submit_feedback", json=feedback_data)
    return status, response


def _normalize_products(response_data: dict) -> list[dict]:
    return _normalize_suggestions(response_data)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR PRODUCT RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def _render_sidebar_products(products: list[dict]):
    st.markdown('<div class="sidebar-title">Suggestions & Products</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Quick follow-ups and product cards from the current answer.</div>', unsafe_allow_html=True)
    if not products:
        st.info("No product cards available yet.")
        return
    for product in products[:8]:
        product = _ensure_dict(product)
        image_url = _image_url(product)
        meta = _meta_text(product)
        features = _as_list(product.get("features"))
        with st.container(border=True):
            if image_url:
                st.image(image_url, use_container_width=True)
            st.markdown(f"**{product.get('title', 'Product')}**")
            if product.get("id"):
                st.caption(f"ID: {product.get('id')}")
            if meta:
                st.caption(meta)
            if product.get("description"):
                st.caption(str(product.get("description"))[:220])
            badge_cols = st.columns(2)
            badges = [("Price",product.get("price")),("Size",product.get("size")),
                      ("Brand",product.get("brand")),("Rating",product.get("rating_number"))]
            for i, (label, value) in enumerate(badges[:2]):
                if value not in (None, "", [], {}):
                    badge_cols[i].caption(f"{label}: {value}")
            for i, (label, value) in enumerate(badges[2:]):
                if value not in (None, "", [], {}):
                    badge_cols[i].caption(f"{label}: {value}")
            if features:
                st.markdown("**Highlights**")
                for feature in features[:4]:
                    if feature:
                        st.markdown(f"- {feature}")


# ─────────────────────────────────────────────────────────────────────────────
# FEEDBACK WIDGET — per-message, industry-grade UX
# ─────────────────────────────────────────────────────────────────────────────

_POS_TAGS = ["Accurate ✅", "Helpful 💡", "Well explained 📖", "Fast response ⚡", "Great suggestions 🛍️"]
_NEG_TAGS = ["Inaccurate ❌", "Off-topic 🔀", "Too vague 🌫️", "Missing details 📋", "Wrong products 🛒"]


def _render_feedback_widget(msg_key: str):
    """
    Self-contained per-message feedback widget.
    State is scoped to msg_key so each assistant message tracks independently.
    """
    def _sk(suffix):
        return f"fb_{msg_key}_{suffix}"

    # Initialise per-message state keys
    for key, default in [
        ("type", None), ("submitted", False), ("show_panel", False),
        ("tags", []), ("extra_done", False),
    ]:
        if _sk(key) not in st.session_state:
            st.session_state[_sk(key)] = default

    fb_type      = st.session_state[_sk("type")]
    fb_submitted = st.session_state[_sk("submitted")]
    show_panel   = st.session_state[_sk("show_panel")]
    extra_done   = st.session_state[_sk("extra_done")]

    # ── Divider + label ────────────────────────────────────────────────────
    st.markdown('<div class="feedback-divider"></div>', unsafe_allow_html=True)
    st.markdown('<span class="feedback-label">Was this response helpful?</span>', unsafe_allow_html=True)

    # ── Thumbs buttons ─────────────────────────────────────────────────────
    col_up, col_down, col_spacer = st.columns([1.8, 2.2, 8])

    with col_up:
        up_label = ("👍 Helpful ✓" if fb_type == "positive" else "👍 Helpful")
        up_type  = "primary" if fb_type == "positive" else "secondary"
        if st.button(up_label, key=f"thumb_up_{msg_key}", help="This response was helpful",
                     use_container_width=True, type=up_type):
            if fb_type != "positive":
                with st.spinner("Recording feedback…"):
                    status, _ = submit_feedback("positive")
                if status:
                    st.session_state[_sk("type")]       = "positive"
                    st.session_state[_sk("submitted")]  = True
                    st.session_state[_sk("show_panel")] = True
                    st.session_state[_sk("extra_done")] = False
                    st.session_state[_sk("tags")]       = []
                else:
                    st.error("Could not submit feedback — please try again.")
                st.rerun()

    with col_down:
        down_label = ("👎 Not helpful ✓" if fb_type == "negative" else "👎 Not helpful")
        down_type  = "primary" if fb_type == "negative" else "secondary"
        if st.button(down_label, key=f"thumb_down_{msg_key}", help="This response wasn't helpful",
                     use_container_width=True, type=down_type):
            if fb_type != "negative":
                with st.spinner("Recording feedback…"):
                    status, _ = submit_feedback("negative")
                if status:
                    st.session_state[_sk("type")]       = "negative"
                    st.session_state[_sk("submitted")]  = True
                    st.session_state[_sk("show_panel")] = True
                    st.session_state[_sk("extra_done")] = False
                    st.session_state[_sk("tags")]       = []
                else:
                    st.error("Could not submit feedback — please try again.")
                st.rerun()

    # ── Toast after initial thumb (before detail panel) ────────────────────
    if fb_submitted and not show_panel and not extra_done:
        icon = "✅" if fb_type == "positive" else "🙏"
        msg  = ("Thanks for the positive feedback!" if fb_type == "positive"
                else "Thanks — your feedback helps us improve.")
        st.markdown(f'<div class="fb-toast success">{icon} {msg}</div>', unsafe_allow_html=True)

    # ── Additional details panel ───────────────────────────────────────────
    if show_panel and not extra_done:
        is_pos = fb_type == "positive"
        icon_p  = "💬" if is_pos else "🔍"
        title_p = "Tell us what you liked" if is_pos else "Help us improve"
        sub_p   = (
            "Your thumbs-up has been recorded ✅. Optionally share more detail below."
            if is_pos else
            "Your thumbs-down has been recorded ✅. Help us understand what went wrong."
        )
        tag_pool    = _POS_TAGS if is_pos else _NEG_TAGS
        placeholder = "Any additional comments…" if is_pos else "Describe the issue in more detail…"

        st.markdown(
            f'<div class="feedback-panel">'
            f'<div class="panel-title">{icon_p} {title_p}</div>'
            f'<div class="panel-sub">{sub_p}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("**Quick tags** *(optional — select all that apply)*")
        selected_tags = st.multiselect(
            label="Select tags",
            options=tag_pool,
            default=st.session_state[_sk("tags")],
            key=f"tags_ms_{msg_key}",
            label_visibility="collapsed",
        )
        st.session_state[_sk("tags")] = selected_tags

        extra_text = st.text_area(
            "Additional comments (optional)",
            key=f"extra_text_{msg_key}",
            placeholder=placeholder,
            height=100,
        )

        col_send, col_skip, col_spacer2 = st.columns([2, 1.5, 5])

        with col_send:
            if st.button("📤 Send Details", key=f"send_extra_{msg_key}",
                         use_container_width=True, type="primary"):
                tag_text = ", ".join(selected_tags) if selected_tags else ""
                combined = " | ".join(filter(None, [tag_text, extra_text.strip()]))
                if combined:
                    with st.spinner("Sending details…"):
                        # FIX: pass feedback_type so score is correctly logged
                        status, _ = submit_feedback(
                            feedback_type=fb_type,
                            feedback_text=combined,
                        )
                    if status:
                        st.session_state[_sk("show_panel")] = False
                        st.session_state[_sk("extra_done")] = True
                    else:
                        st.error("Failed to send details — please try again.")
                else:
                    st.warning("Select a tag or write a comment before sending.")
                st.rerun()

        with col_skip:
            if st.button("Skip", key=f"skip_extra_{msg_key}", use_container_width=True):
                st.session_state[_sk("show_panel")] = False
                st.session_state[_sk("extra_done")] = True
                st.rerun()

    # ── Final thank-you toast ──────────────────────────────────────────────
    if fb_submitted and extra_done:
        st.markdown(
            '<div class="fb-toast success">✅ Thank you! Your detailed feedback has been recorded.</div>',
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Ask me about a product and I'll show matching items and suggestions."}
    ]
if "suggestions"   not in st.session_state: st.session_state.suggestions   = []
if "used_context"  not in st.session_state: st.session_state.used_context  = []
if "session_id"    not in st.session_state: st.session_state.session_id    = str(uuid.uuid4())
if "thread_id"     not in st.session_state: st.session_state.thread_id     = st.session_state.session_id
if "trace_id"      not in st.session_state: st.session_state.trace_id      = None
# Stable unique keys per message — persists feedback state across re-renders
if "msg_ids" not in st.session_state:       st.session_state.msg_ids       = ["init_msg"]


# ─────────────────────────────────────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="hero">
      <h1>🛍️ Ecommerce Assistant</h1>
      <p>Search products, get concise answers, and browse matching product cards with images and quick suggestions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 💡 Suggestions")
    if st.session_state.suggestions:
        for suggestion in st.session_state.suggestions[:4]:
            suggestion = _ensure_dict(suggestion)
            st.info(suggestion.get("title", "Suggestion"))
    else:
        st.info("No suggestions yet. Ask a question to see quick follow-ups.")
    st.divider()
    _render_sidebar_products(_normalize_products({"used_context": st.session_state.used_context}))


# ─────────────────────────────────────────────────────────────────────────────
# CHAT HISTORY — render messages with per-message feedback widgets
# ─────────────────────────────────────────────────────────────────────────────

for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        is_assistant = message["role"] == "assistant"
        is_greeting  = (idx == 0)

        if is_assistant and not is_greeting:
            # Ensure stable key exists for this message index
            while len(st.session_state.msg_ids) <= idx:
                st.session_state.msg_ids.append(str(uuid.uuid4()))
            _render_feedback_widget(st.session_state.msg_ids[idx])


# ─────────────────────────────────────────────────────────────────────────────
# CHAT INPUT & STREAMING RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

prompt = st.chat_input("Ask about a laptop, price, size, brand, or similar products…")
if prompt:
    st.session_state.trace_id = None

    st.session_state.messages.append({"role": "user", "content": prompt})
    new_msg_key = str(uuid.uuid4())   # pre-allocated stable key for the incoming reply

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_placeholder  = st.empty()
        message_placeholder = st.empty()
        status_placeholder.markdown("**🔍 AI is thinking…**")

        for line in api_call_stream(
            "post",
            f"{config.API_URL}/rag",
            json={"query": prompt, "thread_id": get_session_id()},
            stream=True,
            headers={"Accept": "text/event-stream"},
        ):
            if isinstance(line, bytes):
                line_text = line.decode("utf-8", errors="ignore")
            else:
                line_text = str(line)

            if line_text.startswith("data: "):
                data = line_text[6:].strip()
                try:
                    output = json.loads(data)

                    if output.get("type") == "status":
                        status_placeholder.markdown(f"*{output.get('data', '')}*")
                        continue

                    if output.get("type") == "final_answer":
                        answer       = output["data"]["answer"]
                        used_context = output["data"].get("used_context", [])
                        trace_id     = output["data"].get("trace_id", "")

                        st.session_state.used_context = used_context
                        st.session_state.trace_id     = trace_id

                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        st.session_state.msg_ids.append(new_msg_key)

                        status_placeholder.empty()
                        message_placeholder.markdown(answer)

                        # Render feedback widget inline after the fresh reply
                        _render_feedback_widget(new_msg_key)
                        break

                    if output.get("type") == "error":
                        status_placeholder.empty()
                        message_placeholder.error(output.get("data", {}).get("message", "Unknown error"))
                        break

                except json.JSONDecodeError:
                    if data:
                        status_placeholder.markdown(f"*{data}*")
