from __future__ import annotations

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

st.markdown(
    """
    <style>
    .app-shell {
        max-width: 1360px;
        margin: 0 auto;
    }
    .hero {
        padding: 1rem 1.2rem;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(30,41,59,0.94));
        color: white;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2rem;
        line-height: 1.15;
    }
    .hero p {
        margin: 0.45rem 0 0 0;
        color: rgba(255,255,255,0.82);
    }
    .answer-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 22px;
        padding: 1rem 1rem 0.9rem 1rem;
        background: #ffffff;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
        margin-bottom: 0.9rem;
    }
    .answer-heading {
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 0.5rem;
        color: #0f172a;
    }
    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.4rem;
    }
    .pill {
        border-radius: 999px;
        padding: 0.34rem 0.7rem;
        font-size: 0.8rem;
        background: rgba(37, 99, 235, 0.1);
        color: #0f172a;
        border: 1px solid rgba(37, 99, 235, 0.15);
    }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 0.9rem;
        margin-top: 0.8rem;
    }
    .card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 18px;
        overflow: hidden;
        background: white;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    }
    .card img {
        width: 100%;
        height: 180px;
        object-fit: cover;
        background: #f8fafc;
        display: block;
    }
    .card-body {
        padding: 0.85rem;
    }
    .card-title {
        font-weight: 800;
        font-size: 0.98rem;
        line-height: 1.3;
        margin-bottom: 0.35rem;
        color: #0f172a;
    }
    .card-meta {
        font-size: 0.8rem;
        opacity: 0.82;
        margin-bottom: 0.45rem;
        color: #334155;
    }
    .card-desc {
        font-size: 0.86rem;
        line-height: 1.4;
        color: #334155;
    }
    .sidebar-title {
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 0.1rem;
        color: #0f172a;
    }
    .sidebar-subtitle {
        font-size: 0.84rem;
        color: #64748b;
        margin-bottom: 0.75rem;
    }
    .sidebar-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 16px;
        overflow: hidden;
        background: white;
        margin-bottom: 0.8rem;
    }
    .sidebar-card img {
        width: 100%;
        height: 148px;
        object-fit: cover;
        display: block;
        background: #f8fafc;
    }
    .sidebar-card-body {
        padding: 0.75rem;
    }
    .sidebar-card-title {
        font-weight: 800;
        font-size: 0.92rem;
        line-height: 1.3;
        margin-bottom: 0.25rem;
    }
    .sidebar-card-meta {
        font-size: 0.78rem;
        opacity: 0.8;
        margin-bottom: 0.35rem;
    }
    .sidebar-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem;
        margin-top: 0.35rem;
    }
    .sidebar-badge {
        padding: 0.18rem 0.5rem;
        border-radius: 999px;
        font-size: 0.73rem;
        background: rgba(15, 23, 42, 0.06);
        color: #0f172a;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    if isinstance(value, dict):
        return value
    return {}


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
        ("price", "Price"),
        ("rating_number", "Ratings"),
        ("average_rating", "Avg rating"),
        ("brand", "Brand"),
        ("size", "Size"),
        ("color", "Color"),
        ("store", "Store"),
        ("main_category", "Category"),
    ]:
        value = item.get(key)
        if value not in (None, "", [], {}):
            bits.append(f"{label}: {value}")

    if isinstance(details, dict):
        for key in ["size", "color", "brand", "material", "style", "capacity", "storage"]:
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
                    "id": item[:40],
                    "title": item.strip(),
                    "text": item.strip(),
                    "images": [],
                    "features": [],
                    "price": None,
                    "rating_number": None,
                    "size": "",
                    "brand": "",
                    "color": "",
                    "details": {},
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



def submit_feedback(feedback_type=None, feedback_text=""):
    """Submit feedback to the APi Endpoint"""
    def _feedback_score(feedback_type):
        if feedback_type == "positive":
            return 1
        elif feedback_type == "negative":
            return 0
        else:
            return None 
    
    feedback_data = {
        "feedback_score": _feedback_score(feedback_type),
        "feedback_text": feedback_text,
        "trace_id": st.session_state.trace_id, 
        "thread_id": st.session_state.session_id,
        "feedback_source_type": "api"
    }

    logger.info("Feedback Data: {feedback_data}")

    status, response = api_call("post", f"{config.API_URL}/submit_feedback", json=feedback_data)
    return status, response

def _normalize_products(response_data: dict) -> list[dict]:
    return _normalize_suggestions(response_data)


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
            badges = [
                ("Price", product.get("price")),
                ("Size", product.get("size")),
                ("Brand", product.get("brand")),
                ("Rating", product.get("rating_number")),
            ]
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


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello. Ask me about a product and I will show matching items and suggestions."}]
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []
if "used_context" not in st.session_state:
    st.session_state.used_context = []
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "thread_id" not in st.session_state:
    st.session_state.thread_id = st.session_state.session_id

# initialize feedback states (simplified)
if "latest_feedback" not in st.session_state:
    st.session_state.latest_feedback = None

if "show_feedback_box" not in st.session_state:
    st.session_state.show_feedback_box = False

if "feedback_submission_status" not in st.session_state:
    st.session_state.feedback_submission_status = None

if "trace_id" not in st.session_state:
    st.session_state.trace_id = None


for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        feedback_result = None
        # Add feedback buttons only for the latest assistant message
        is_latest_assistant = (
            message["role"] == "assistant" and idx == len(st.session_state.messages) - 1 and idx > 0
        )

        if is_latest_assistant:
            # Use Streamlit's builtin feedback component
            feedback_key = f"feedback_{len(st.session_state.messages)}"
            feedback_result = st.feedback("thumbs", key=feedback_key)

            # Handle Feedback selection
            if feedback_result is not None:
                feedback_type = "positive" if feedback_result == 1 else "negative"

                # only submit if this is a new/different feedback
                if st.session_state.latest_feedback != feedback_type:
                    with st.spinner("Submitting Feedback..."):
                        st.session_state.feedback_submission_status = None
                        status, response = submit_feedback(feedback_type)
                        
                        if status:
                            st.session_state.latest_feedback = feedback_type
                            st.session_state.feedback_submission_status = "success"
                            st.session_state.show_feedback_box = True
                        else:
                            st.session_state.feedback_submission_status = "error"   
                            st.error("Failed to submit feedback. Please try again.")
                        
                    st.rerun()
            
            # show feedback status message
            if st.session_state.latest_feedback and st.session_state.feedback_submission_status == "success":
                if st.session_state.latest_feedback == "positive":
                    st.success("Thank you for positive feedback!")
                elif st.session_state.latest_feedback == "negative" and not st.session_state.show_feedback_box:
                    st.success("Thank you for your feedback!")
            elif st.session_state.feedback_submission_status == "error":
                st.error("Failed to submit feedback. Please try again.")
            
            # show feedback text box if thumbs down/up was pressed
            if st.session_state.show_feedback_box:
                st.markdown("**Want to tell us more? (Optional)**")
                if st.session_state.latest_feedback == "positive":
                    st.caption("Your positive feedback has already been recorded. You can optionally provide additional details or comments below.")
                    placeholder_text = "Please describe what you liked or any comments..."
                else:
                    st.caption("Your negative feedback has already been recorded. You can optionally provide additional details below.")
                    placeholder_text = "Please describe what was wrong with this response..."

                # Text area for detailed feedback
                feedback_text = st.text_area(
                    "Additional feedback (optional)",
                    key=f"feedback_text_{len(st.session_state.messages)}",
                    placeholder=placeholder_text,
                    height=100
                )

                # send additional feedback button
                col_send, col_spacer, col_close = st.columns([3, 5, 2])

                with col_send:
                    if st.button("Send Additional Details", key=f"send_additional_{len(st.session_state.messages)}"):
                        if feedback_text.strip():
                            with st.spinner("Submitting additional feedback..."):
                                status, response = submit_feedback(feedback_text=feedback_text)
                                if status:
                                    st.success("Thank you! Your additional feedback has been recorded.")
                                    st.session_state.show_feedback_box = False
                                else:
                                    st.error("Failed to record additional feedback. Please try again.")   
                        else:
                            st.warning("Please enter some feedback text before submitting!")         
                        st.rerun()

                with col_close:
                    if st.button("Close", key=f"cancel_feedback_{len(st.session_state.messages)}"):
                        st.session_state.show_feedback_box = False
                        st.session_state.latest_feedback = None
                        st.session_state.feedback_submission_status = None
                        st.rerun()

st.markdown(
    """
    <div class="hero">
      <h1>Ecommerce Assistant</h1>
      <p>Search products, get concise answers, and browse matching product cards with images and quick suggestions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Suggestions")
    if st.session_state.suggestions:
        for suggestion in st.session_state.suggestions[:4]:
            suggestion = _ensure_dict(suggestion)
            st.info(suggestion.get("title", "Suggestion"))
    else:
        st.info("No suggestions yet. Ask a question to see quick follow-ups.")

    st.divider()
    _render_sidebar_products(_normalize_products({"used_context": st.session_state.used_context}))


prompt = st.chat_input("Ask about a laptop, price, size, brand, or similar products...")
if prompt:
    st.session_state.latest_feedback = None
    st.session_state.show_feedback_box = False
    st.session_state.feedback_submission_status = None
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        success, response_data = api_call("post", f"{config.API_URL}/rag", json={"query": prompt, "thread_id": st.session_state.thread_id})

        if success and isinstance(response_data, dict):
            answer = response_data.get("answer") or response_data.get("message") or "No answer returned."
            st.session_state.used_context = response_data.get("used_context", []) or []
            st.session_state.suggestions = _normalize_suggestions(response_data)
            st.session_state.trace_id = response_data.get("trace_id")
        else:
            answer = response_data.get("message", "Sorry, I could not generate a response right now.")
            st.session_state.used_context = []
            st.session_state.suggestions = []

        st.markdown('<div class="answer-card">', unsafe_allow_html=True)
        st.markdown('<div class="answer-heading">Best answer</div>', unsafe_allow_html=True)
        st.write(answer)

        if st.session_state.suggestions:
            st.markdown('<div class="answer-heading">Suggestions</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="pill-row">' + ''.join(
                    f'<span class="pill">{_escape(item.get("title", ""))}</span>'
                    for item in st.session_state.suggestions[:4]
                ) + '</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.used_context:
            st.markdown('<div class="answer-heading">Products used</div>', unsafe_allow_html=True)
            cols = st.columns(min(3, len(st.session_state.used_context)))
            for index, item in enumerate(st.session_state.used_context[:3]):
                item = _ensure_dict(item)
                with cols[index]:
                    image_url = _image_url(item)
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    st.markdown(f"**{item.get('title', 'Product')}**")
                    meta = _meta_text(item)
                    if meta:
                        st.caption(meta)
                    description = item.get("description") or item.get("review") or ""
                    if isinstance(description, list):
                        description = " ".join(str(x) for x in description if x)
                    if description:
                        st.caption(str(description)[:220])

        st.markdown('</div>', unsafe_allow_html=True)

        st.caption("Open the sidebar for richer product cards, images, and follow-up suggestions.")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()