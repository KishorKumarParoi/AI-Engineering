import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def pick_llm(
    level: str = "low",
    temperature: float = 0.0,
    max_tokens: int = 2048,
    model_override: Optional[str] = None,
) -> ChatOpenAI:
    """
    Picks and initializes a ChatOpenAI model based on the complexity level.

    Args:
        level (str): "low", "medium", or "high".
        temperature (float): Sampling temperature (default 0.0 for deterministic output).
        max_tokens (int): Maximum output tokens (default 2048).
        model_override (str, optional): Explicit model name to use.

    Returns:
        ChatOpenAI: Initialized LangChain ChatOpenAI instance.
    """
    models = {
        "low": os.getenv("MODEL_LOW", "gpt-4o-mini"),
        "medium": os.getenv("MODEL_MEDIUM", "gpt-4o"),
        "high": os.getenv("MODEL_HIGH", "gpt-4o"),
    }

    normalized_level = level.lower().strip()
    selected_model = model_override or models.get(normalized_level, "gpt-4o-mini")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please check your .env file.")

    return ChatOpenAI(
        model=selected_model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )


if __name__ == "__main__":
    llm_obj = pick_llm("low")
    response = llm_obj.invoke("Hello, respond with 'LLM is working!'")
    print(response.content)