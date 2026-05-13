import streamlit as st
from openai import OpenAI
from groq import Groq
from google import genai
from src.testing_ai_project.config.configuration import config


def run_llm(provider, model_name, messages, max_tokens=500):
    if provider == "OpenAI":
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            reasoning_effort="medium",
        )
        return response.choices[0].message.content

    if provider == "Groq":
        client = Groq(api_key=config.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    if provider == "Gemini":
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        contents = [message["content"] for message in messages if "content" in message]
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
        )
        return response.text

    raise ValueError("Unsupported provider")


with st.sidebar:
    st.title("Settings")

    provider = st.selectbox("Select LLM Provider", ["OpenAI", "Groq", "Gemini"])

    if provider == "OpenAI":
        model_name = st.selectbox("Select OpenAI Model", ["gpt-4o", "gpt-5-mini"])
    elif provider == "Groq":
        model_name = st.selectbox("Select Groq Model", ["llama-3.3-70b-versatile"])
    else:
        model_name = st.selectbox("Select Gemini Model", ["gemini-1.5-pro", "gemini-2.5-flash"])

    st.session_state.provider = provider
    st.session_state.model_name = model_name

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"**User:** {message['content']}")
    elif message["role"] == "assistant":
        st.markdown(f"**Assistant:** {message['content']}")

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Generating response..."):
        response = run_llm(
            st.session_state.provider,
            st.session_state.model_name,
            st.session_state.messages,
        )

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.markdown(f"**Assistant:** {response}")