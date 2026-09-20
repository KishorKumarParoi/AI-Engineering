from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

def pick_llm(level: str) -> ChatOpenAI:
    """
    Picks and initializes the ChatOpenAI model based on the level.

    Args:
        level (str): The level of the LLM to pick ("low", "medium", "high").

    Returns:
        ChatOpenAI: Initialized ChatOpenAI instance.
    """
    models = {
        "low": "gpt-4o-mini",
        "medium": "gpt-4o",
        "high": "gpt-4-turbo",
    }

    normalized_level = level.lower().strip()
    if normalized_level not in models:
        raise ValueError(
            f"Invalid level '{level}'. Supported levels: {list(models.keys())}"
        )

    return ChatOpenAI(
        model=models[normalized_level],
        temperature=0.0,
        max_tokens=500,
    )

if __name__ == "__main__":
    llm_obj = pick_llm("low")
    print(llm_obj.invoke("What is the capital of France?"))