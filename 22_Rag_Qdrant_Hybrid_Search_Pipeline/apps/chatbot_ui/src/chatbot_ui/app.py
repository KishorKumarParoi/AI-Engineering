import streamlit as st
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


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if "used_context" not in st.session_state:
    st.session_state.used_context = []


with st.sidebar:
    suggestions_tab, about_tab = st.tabs(["Suggestions", "About"])

    with suggestions_tab:
        if st.session_state.used_context:
            st.write("### Suggestions based on retrieved context:")
            for idx, context in enumerate(st.session_state.used_context, 1):
                st.markdown(f"**Context {idx}:** {context}")
        else:
            st.write("No suggestions available since no relevant context was retrieved.")


if prompt := st.chat_input("Hello! How can I assist you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        success, response_data = api_call("post", f"{config.API_URL}/rag", json={"query": prompt})
        if success and "answer" in response_data:
            answer = response_data["answer"]
            used_context = response_data.get("used_context", [])
            st.session_state.used_context = used_context
        else:
            answer = response_data.get("message", "Sorry, I could not generate a response right now.")
            st.session_state.used_context = []  
        st.write(answer)
        st.write("### Used Context:")
        if st.session_state.used_context:
            for idx, context in enumerate(st.session_state.used_context, 1):
                st.markdown(f"**Context {idx}:** {context}")
        else:
            st.markdown("No relevant context was retrieved.")
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()