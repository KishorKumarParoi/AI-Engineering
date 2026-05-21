import streamlit as st
import streamlit.components.v1 as components
import requests
from chatbot_ui.core.config import config

st.set_page_config(page_title="Ecommerce Assistant",layout="wide", initial_sidebar_state="expanded", page_icon="🤖")

def api_call(method, url, **kwargs):

    def _show_error_popup(message):
        """Show error message as a popup in the top-right corner."""
        st.session_state["error_popup"] = {
            "visible": True,
            "message": message,
        }

    try:
        response = getattr(requests, method)(url, **kwargs)

        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            response_data = {"message": "Invalid response format from server"}

        if response.ok:
            return True, response_data

        return False, response_data

    except requests.exceptions.ConnectionError:
        _show_error_popup("Connection error. Please check your network connection.")
        return False, {"message": "Connection error"}
    except requests.exceptions.Timeout:
        _show_error_popup("The request timed out. Please try again later.")
        return False, {"message": "Request timeout"}
    except Exception as e:
        _show_error_popup(f"An unexpected error occurred: {str(e)}")
        return False, {"message": str(e)}


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you today?"}]

if "suggestions" not in st.session_state:
    st.session_state.suggestions = []


def normalize_suggestions(response_data):
    suggestions = []

    if not isinstance(response_data, dict):
        return suggestions

    retrieved_context = response_data.get("retrieved_context", {})

    if isinstance(retrieved_context, dict):
        ids = retrieved_context.get("retrieved_context_ids") or []
        titles = retrieved_context.get("retrieve_context_titles") or []
        texts = retrieved_context.get("retrieve_context") or []
        scores = retrieved_context.get("similarity_scores") or []
        prices = retrieved_context.get("retrieve_context_prices") or []
        stores = retrieved_context.get("retrieve_context_stores") or []
        categories = retrieved_context.get("retrieve_context_categories") or []
        descriptions = retrieved_context.get("retrieve_context_descriptions") or []

        item_count = max(
            len(ids),
            len(titles),
            len(texts),
            len(scores),
            len(prices),
            len(stores),
            len(categories),
            len(descriptions),
        )

        for index in range(item_count):
            title = titles[index] if index < len(titles) else ""
            text = texts[index] if index < len(texts) else ""
            suggestions.append({
                "id": ids[index] if index < len(ids) else "",
                "title": title or text[:80],
                "text": text,
                "score": scores[index] if index < len(scores) else None,
                "price": prices[index] if index < len(prices) else None,
                "store": stores[index] if index < len(stores) else "",
                "categories": categories[index] if index < len(categories) else [],
                "description": descriptions[index] if index < len(descriptions) else "",
            })

    elif isinstance(response_data.get("used_context"), list):
        for item in response_data.get("used_context", []):
            if not isinstance(item, dict):
                continue
            suggestions.append({
                "id": item.get("id", ""),
                "title": item.get("title") or item.get("review", "")[:80],
                "text": item.get("review", ""),
                "score": item.get("score"),
                "price": item.get("price"),
                "store": item.get("store", ""),
                "categories": item.get("categories", []),
                "description": item.get("description", ""),
            })

    return suggestions


def render_suggestions_panel(suggestions):
    st.markdown(
        """
        <style>
        .suggestions-panel {
            max-height: 540px;
            overflow-y: auto;
            padding-right: 0.5rem;
        }
        .suggestion-card {
            border: 1px solid rgba(49, 51, 63, 0.18);
            border-radius: 14px;
            padding: 0.85rem 0.9rem;
            margin-bottom: 0.75rem;
            background: rgba(250, 250, 250, 0.85);
        }
        .suggestion-title {
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .suggestion-meta {
            font-size: 0.85rem;
            opacity: 0.75;
            margin-bottom: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Suggestions")
    if not suggestions:
        st.info("No suggestions available.")
        return

    st.markdown('<div class="suggestions-panel">', unsafe_allow_html=True)
    for suggestion in suggestions:
        score = suggestion.get("score")
        score_text = f"Score: {score:.3f}" if isinstance(score, (int, float)) else ""
        categories = suggestion.get("categories") or []
        category_text = ", ".join(categories[:3]) if isinstance(categories, list) else str(categories)

        st.markdown(
            f"""
            <div class="suggestion-card">
                <div class="suggestion-title">{suggestion.get('title', 'Suggestion')}</div>
                <div class="suggestion-meta">
                    {suggestion.get('id', '')} {('• ' + score_text) if score_text else ''}
                </div>
                <div>{suggestion.get('text', '')}</div>
                <div class="suggestion-meta">
                    {f'Price: {suggestion.get("price")}' if suggestion.get('price') is not None else ''}
                    {(' • ' + suggestion.get('store', '')) if suggestion.get('store') else ''}
                    {(' • ' + category_text) if category_text else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def scroll_to_response_anchor():
    components.html(
        """
        <script>
        const anchor = window.parent.document.getElementById('assistant-response-anchor');
        if (anchor) {
            anchor.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
        </script>
        """,
        height=0,
    )


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if "used_context" not in st.session_state:
    st.session_state.used_context = []


with st.sidebar:
    suggestions_tab, about_tab = st.tabs(["Suggestions", "About"])

    with suggestions_tab:
        if st.session_state.suggestions:
            st.write("Suggestions from the latest response are shown in the main chat area.")
            st.caption("Use the scrollable panel next to the answer to inspect them.")
        else:
            st.write("No suggestions available yet.")


if prompt := st.chat_input("Hello! How can I assist you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        st.markdown('<div id="assistant-response-anchor"></div>', unsafe_allow_html=True)
        success, response_data = api_call("post", f"{config.API_URL}/rag", json={"query": prompt})
        if success and "answer" in response_data:
            answer = response_data["answer"]
            st.session_state.suggestions = normalize_suggestions(response_data)
        else:
            answer = response_data.get("message", "Sorry, I could not generate a response right now.")
            st.session_state.suggestions = []

        answer_col, suggestions_col = st.columns([0.62, 0.38], gap="large")

        with answer_col:
            st.markdown("#### Response")
            st.markdown(answer)

        with suggestions_col:
            render_suggestions_panel(st.session_state.suggestions)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    scroll_to_response_anchor()
    st.rerun()