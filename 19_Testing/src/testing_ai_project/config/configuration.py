from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    OPENAI_API_KEY: str
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    DEEPSEEK_API_KEY: str

    model_config = SettingsConfigDict(env_file="../../.env")


config = Config()