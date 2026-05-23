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

if "used_context" not in st.session_state:
    st.session_state.used_context = []


def _first_image_url(images):
    if not isinstance(images, list) or not images:
        return None

    first_image = images[0]
    if isinstance(first_image, dict):
        return first_image.get("hi_res") or first_image.get("large") or first_image.get("thumb")

    if isinstance(first_image, str):
        return first_image

    return None


def _escape_html(value):
    if value is None:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _format_product_meta(item):
    meta_parts = []
    if item.get("price") is not None:
        meta_parts.append(f"Price: {item.get('price')}")
    if item.get("store"):
        meta_parts.append(item.get("store"))
    if item.get("main_category"):
        meta_parts.append(item.get("main_category"))
    categories = item.get("categories") or []
    if isinstance(categories, list) and categories:
        meta_parts.append(", ".join(categories[:3]))
    return " • ".join([part for part in meta_parts if part])


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
        details = retrieved_context.get("retrieve_context_details") or []
        features = retrieved_context.get("retrieve_context_features") or []
        images = retrieved_context.get("retrieve_context_images") or []
        videos = retrieved_context.get("retrieve_context_videos") or []
        main_categories = retrieved_context.get("retrieve_context_main_categories") or []
        rating_numbers = retrieved_context.get("retrieved_context_rating_numbers") or []

        item_count = max(
            len(ids),
            len(titles),
            len(texts),
            len(scores),
            len(prices),
            len(stores),
            len(categories),
            len(descriptions),
            len(details),
            len(features),
            len(images),
            len(videos),
            len(main_categories),
            len(rating_numbers),
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
                "details": details[index] if index < len(details) else {},
                "features": features[index] if index < len(features) else [],
                "images": images[index] if index < len(images) else [],
                "videos": videos[index] if index < len(videos) else [],
                "main_category": main_categories[index] if index < len(main_categories) else "",
                "rating_number": rating_numbers[index] if index < len(rating_numbers) else None,
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
                "details": item.get("details", {}),
                "features": item.get("features", []),
                "images": item.get("images", []),
                "videos": item.get("videos", []),
                "main_category": item.get("main_category", ""),
                "rating_number": item.get("rating_number"),
            })

    return suggestions


def render_suggestions_panel(suggestions):
    st.markdown("### Suggestions")
    if not suggestions:
        st.info("No suggestions available.")
        return

    st.markdown(
        """
        <style>
        .sidebar-suggestions-scroll {
            max-height: 72vh;
            overflow-y: auto;
            padding-right: 0.25rem;
        }
        .sidebar-suggestion-card {
            border: 1px solid rgba(49, 51, 63, 0.18);
            border-radius: 16px;
            padding: 0.8rem;
            margin-bottom: 0.75rem;
            background: rgba(255, 255, 255, 0.92);
        }
        .sidebar-suggestion-title {
            font-weight: 700;
            font-size: 0.95rem;
            line-height: 1.25;
            margin: 0.2rem 0 0.4rem 0;
        }
        .sidebar-suggestion-meta {
            font-size: 0.8rem;
            opacity: 0.78;
            margin-bottom: 0.45rem;
        }
        .sidebar-suggestion-image {
            width: 100%;
            border-radius: 12px;
            margin-bottom: 0.55rem;
            object-fit: cover;
            display: block;
        }
        .sidebar-suggestion-body {
            font-size: 0.87rem;
            line-height: 1.35;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    html_cards = []
    for suggestion in suggestions:
        score = suggestion.get("score")
        score_text = f"Score: {score:.3f}" if isinstance(score, (int, float)) else ""
        image_url = _first_image_url(suggestion.get("images"))
        meta_text = _format_product_meta(suggestion)

        features = suggestion.get("features") or []
        feature_html = ""
        if isinstance(features, list) and features:
            feature_html = "<ul>" + "".join(
                f"<li>{_escape_html(feature)}</li>" for feature in features[:4]
            ) + "</ul>"

        html_cards.append(
            f"""
            <div class="sidebar-suggestion-card">
                {f'<img class="sidebar-suggestion-image" src="{_escape_html(image_url)}" alt="{_escape_html(suggestion.get("title", "Suggestion"))}" />' if image_url else ''}
                <div class="sidebar-suggestion-title">{_escape_html(suggestion.get('title', 'Suggestion'))}</div>
                <div class="sidebar-suggestion-meta">
                    {f'ID: {_escape_html(suggestion.get("id", ""))}' if suggestion.get('id') else ''}
                    {(' • ' + _escape_html(score_text)) if score_text else ''}
                </div>
                {f'<div class="sidebar-suggestion-body">{_escape_html(suggestion.get("text", ""))}</div>' if suggestion.get('text') else ''}
                {f'<div class="sidebar-suggestion-meta">{_escape_html(meta_text)}</div>' if meta_text else ''}
                {f'<div class="sidebar-suggestion-body"><strong>Description:</strong> {_escape_html(suggestion.get("description", ""))}</div>' if suggestion.get('description') else ''}
                {f'<div class="sidebar-suggestion-body"><strong>Features:</strong>{feature_html}</div>' if feature_html else ''}
            </div>
            """
        )

    st.markdown('<div class="sidebar-suggestions-scroll">' + ''.join(html_cards) + '</div>', unsafe_allow_html=True)


def render_used_context_panel(used_context):
    st.markdown("### Products Suggestion")

    for item in used_context:
        image_url = _first_image_url(item.get("images"))
        meta_text = _format_product_meta(item)

        with st.container(border=True):
            if image_url:
                st.image(image_url, use_container_width=True)

            st.markdown(f"**{item.get('title', 'Used Context')}**")
            if item.get('id'):
                st.caption(f"ID: {item.get('id')}")

            if item.get('review'):
                st.write(item.get('review'))

            if meta_text:
                st.caption(meta_text)

            if item.get("description"):
                st.caption(f"Description: {item.get('description')}")

            features = item.get("features") or []
            if isinstance(features, list) and features:
                st.write("Details:")
                for feature in features[:5]:
                    st.write(f"- {feature}")


def render_about_panel():
    pass


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
    tabs = st.tabs(["Suggestions"])
    with tabs[0]:
        # Prefer explicit suggestions; otherwise derive suggestions from used_context
        suggestions_to_render = st.session_state.suggestions or normalize_suggestions({"used_context": st.session_state.used_context})
        if suggestions_to_render:
            render_suggestions_panel(suggestions_to_render)

        st.divider()
        render_used_context_panel(st.session_state.used_context)


if prompt := st.chat_input("Hello! How can I assist you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        st.markdown('<div id="assistant-response-anchor"></div>', unsafe_allow_html=True)
        success, response_data = api_call("post", f"{config.API_URL}/rag", json={"query": prompt})
        if success and "answer" in response_data:
            answer = response_data["answer"]
            # store used_context from the API and derive suggestions from it
            st.session_state.used_context = response_data.get("used_context", []) or []
            st.session_state.suggestions = normalize_suggestions(response_data)
        else:
            answer = response_data.get("message", "Sorry, I could not generate a response right now.")
            st.session_state.suggestions = []
            st.session_state.used_context = []

        st.markdown("#### Best suggestion")
        st.write(answer)
        st.caption("Open the sidebar to browse the images, product details, and used context.")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    scroll_to_response_anchor()
    st.rerun()