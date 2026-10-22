import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # --- GEMINI EMBEDDINGS ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # --- VECTOR DB (QDRANT) ---
    QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = "enterprise_rag"

    # --- REASONING ENGINE (GROQ) ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")



    # --- LLM GATEWAY (PORTKEY) ---
    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
    GROQ_SLUG =  "groq2"     # primary: @rag/llama-3.3-70b-versatile
    GROQ_SLUG_2 = "groq1"  # fallback: @brag/llama-3.1-8b-instant
    PORTKEY_CONFIG_ID = os.getenv("PORTKEY_CONFIG_ID")

    
    # --- OBSERVABILITY ---
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    # --- GCP CONFIGURATION ---
    PROJECT_ID = os.getenv("PROJECT_ID", "project-53d8ce01-b0e0-4f8b-94c")
    LOCATION = os.getenv("LOCATION", "us-central1")
    GCP_DOC_AI_LOCATION = os.getenv("GCP_DOC_AI_LOCATION", "us")
    GCP_DOC_AI_PROCESSOR_ID = os.getenv("GCP_DOC_AI_PROCESSOR_ID", "b306803e35baef71")
    GCP_RAW_BUCKET = os.getenv("GCP_RAW_BUCKET", "enterprise-rag-raw-kkp-53d8ce01")
    GCP_PROCESSED_BUCKET = os.getenv("GCP_PROCESSED_BUCKET", "enterprise-rag-processed-kkp-53d8ce01")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")

    # --- BOT & SECURITY DEFENSE ---
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    BURST_LIMIT_PER_SECOND = int(os.getenv("BURST_LIMIT_PER_SECOND", "5"))
    MAX_PAYLOAD_BYTES = int(os.getenv("MAX_PAYLOAD_BYTES", "65536"))  # 64KB max query body

# Resolve Google Application Credentials if path exists
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.path.isabs(cred_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(base_dir, cred_path)
    if os.path.exists(cred_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

# Apply LangChain environment variables for automatic tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

settings = Settings()

