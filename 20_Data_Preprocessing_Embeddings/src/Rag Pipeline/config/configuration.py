try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:
    # Fallback for environments with older pydantic or different packaging
    try:
        from pydantic import BaseSettings
        # SettingsConfigDict is a simple dict subclass used by pydantic v2; if unavailable, use a plain dict
        SettingsConfigDict = dict
    except Exception:
        raise


class Config(BaseSettings):
    OPENAI_API_KEY: str
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    DEEPSEEK_API_KEY: str

    model_config = SettingsConfigDict(env_file="../../.env")


config = Config()