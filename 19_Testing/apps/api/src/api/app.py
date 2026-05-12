from fastapi import FastAPI, Request
from pydantic import BaseModel

from openai import OpenAI
from groq import Groq
from google import genai

from api.config.configuration import config

import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_llm(provider, model_name, messages, max_tokens=500):

    if provider == "OpenAI":
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            reasoning_effort="minimal"
        )
        return response.choices[0].message.content
    elif provider == "Groq":
        client = Groq(api_key=config.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=max_tokens
        )
        return response.choices[0].message.content
    elif provider == "Gemini":
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model_name,
            contents=[message["content"] for message in messages if "content" in message],
        )
        return response.text
    else:
        raise ValueError(f"Unsupported provider: {provider}")


class ChatRequest(BaseModel):
    provider: str
    model_name: str
    messages: list[dict]

class ChatResponse(BaseModel):
    message: str


app = FastAPI(title="LLM Chat API")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/config")
def show_config() -> dict[str, bool]:
    return {
        "openai_api_key": bool(config.OPENAI_API_KEY),
        "groq_api_key": bool(config.GROQ_API_KEY),
        "gemini_api_key": bool(config.GEMINI_API_KEY),
        "deepseek_api_key": bool(config.DEEPSEEK_API_KEY),
    }


@app.post("/chat")
def chat(payload: ChatRequest) -> ChatResponse:
    logger.info(f"Chat request - provider: {payload.provider}, model: {payload.model_name}")
    result = run_llm(payload.provider, payload.model_name, payload.messages)
    return ChatResponse(message=result)
