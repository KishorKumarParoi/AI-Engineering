import os
import logging
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse  # Moved up here to avoid NameError
import threading

from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse

from api.api.models import RagRequest, RagResponse, RAGUsedContext
from api.agents.prod_retrieval_agents.single_turn_in_retrieval_generation import rag_pipeline_wrapper
from api.api.populate_data import populate_qdrant, retrieve_data, ensure_collection_exists

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

# Retrieve API keys from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GEMINI_API_KEY')
qdrant_url = os.getenv('QDRANT_URL')
qdrant_api_key = os.getenv('QDRANT_API_KEY')
langsmith_api_key = os.getenv('LANGSMITH_API_KEY')

if qdrant_url and "qdrant:6333" in qdrant_url:
    # Docker service host is not resolvable from a local notebook kernel
    qdrant_url = qdrant_url.replace("qdrant:6333", "localhost:6333")
    
# Verify keys are loaded
print(f"OpenAI API Key present: {bool(openai_api_key)}")
print(f"Google API Key present: {bool(google_api_key)}")
print(f"Qdrant URL present: {bool(qdrant_url)}")
print(f"Qdrant API Key present: {bool(qdrant_api_key)}")
print(f"Langsmith API Key present: {bool(langsmith_api_key)}")

# Keep your robust Docker bridge routing url
ACTIVE_CONTAINER_URL = "http://qdrant:6333" if os.path.exists('/.dockerenv') else os.getenv('QDRANT_URL', 'http://localhost:6333')

print(f"--> [DOCKER-NETWORK] Instantiating Qdrant Target: {ACTIVE_CONTAINER_URL}")

qdrant_client = QdrantClient(
    url=ACTIVE_CONTAINER_URL,
    api_key=os.getenv('QDRANT_API_KEY'),
    check_compatibility=False,  # Stops the client from crashing when checking version on boot
)

# Simple lock to avoid concurrent population from multiple requests
_population_lock = threading.Lock()

DATA_PATH = "data/Data_With_Images.jsonl" 
COLLECTION_NAME = os.environ.get("collection_name") or "Amazon_Electronics_Products"

def _collection_count_value(collection_count):
    if collection_count is None:
        return None
    if isinstance(collection_count, int):
        return collection_count
    return getattr(collection_count, "count", None)

# 1. RUN DATA POPULATION AT APP BOOT LIFECYCLE (PROVISIONED WITH WHITE-SPACE STRIPPER)
def run_db_initialization():
    global DATA_PATH
    try:
        # Ensure collection exists (creates with retries if Qdrant isn't ready yet)
        try:
            ensure_collection_exists(qdrant_client, collection_name=COLLECTION_NAME, retries=12, delay=2)

            # If collection exists but is empty, attempt to populate from local data file
            try:
                collection_count = qdrant_client.count(collection_name=COLLECTION_NAME)
            except Exception:
                collection_count = None
            collection_count_value = _collection_count_value(collection_count)

            if collection_count_value in (0, None):
                logger.info(f"Collection '{COLLECTION_NAME}' is empty or unknown size ({collection_count_value}). Attempting population if data exists...")
                try:
                    if not os.path.exists(DATA_PATH):
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        print(f"Current directory for data path resolution: {current_dir}")
                        DATA_PATH = os.path.abspath(os.path.join(current_dir, "../../../../../data/Data_With_Images.jsonl"))

                    if os.path.exists(DATA_PATH) and os.path.getsize(DATA_PATH) > 0:
                        with open(DATA_PATH, 'r', encoding='utf-8') as f:
                            valid_lines = [line.strip() for line in f if line.strip()]

                        if valid_lines:
                            from io import StringIO
                            clean_json_stream = StringIO("\n".join(valid_lines))
                            df = pd.read_json(clean_json_stream, lines=True)
                            logger.info(f"Successfully loaded dataset of shape: {df.shape}")
                            populate_qdrant(df, qdrant_client, collection_name=COLLECTION_NAME)
                        else:
                            logger.warning("Data file exists but contains no valid lines; skipping population.")
                    else:
                        logger.info(f"No data file found at {DATA_PATH}; skipping auto-population.")

                except Exception as pop_err:
                    logger.error(f"Population routine failed: {pop_err}")

            # 2. Testing with sample query to see if retrieval works now
            try:
                sample_answer = retrieve_data(qdrant_client, query="What kind of Laptop do you offer?", collection_name=COLLECTION_NAME, k=10)
                print("Sample retrieval answer:", sample_answer)
            except Exception as look_err:
                logger.error(f"Error during sample retrieval after population: {look_err}")

        except Exception as e:
            logger.exception(f"Failed to ensure collection exists: {e}")
    except Exception as init_err:
        logger.exception(f"Initialization failed: {init_err}")

threading.Thread(target=run_db_initialization, daemon=True).start()


rag_router = APIRouter()

@rag_router.post("/")
def rag(
    request: Request,
    payload: RagRequest
) -> RagResponse:
    logger.info(f"Received request: {payload}")

    try:  # <-- FIXED: Restored missing parent try-block here
        # Ensure collection exists and populate on-demand if empty
        try:
            ensure_collection_exists(qdrant_client, collection_name=COLLECTION_NAME)
        except Exception as e:
            logger.warning(f"Could not ensure collection exists before request: {e}")

        try:
            collection_count = qdrant_client.count(collection_name=COLLECTION_NAME)
        except Exception:
            collection_count = None
        collection_count_value = _collection_count_value(collection_count)

        if collection_count_value in (0, None):
            # Acquire lock so only one request populates at a time
            if _population_lock.acquire(blocking=False):
                try:
                    # Re-check inside lock
                    try:
                        collection_count = qdrant_client.count(collection_name=COLLECTION_NAME)
                    except Exception:
                        collection_count = None
                    collection_count_value = _collection_count_value(collection_count)

                    if collection_count_value in (0, None):
                        logger.info("On-demand population: collection empty, attempting to upsert data before answering request")
                        try:
                            # Resolve DATA_PATH similar to startup logic
                            if not os.path.exists(DATA_PATH):
                                current_dir = os.path.dirname(os.path.abspath(__file__))
                                DATA_FILE = os.path.abspath(os.path.join(current_dir, "../../../../../data/Data_With_Images.jsonl"))
                            else:
                                DATA_FILE = DATA_PATH

                            if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
                                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                                    valid_lines = [line.strip() for line in f if line.strip()]

                                if valid_lines:
                                    from io import StringIO
                                    clean_json_stream = StringIO("\n".join(valid_lines))
                                    df = pd.read_json(clean_json_stream, lines=True)
                                    populate_qdrant(df, qdrant_client, collection_name=COLLECTION_NAME)
                                else:
                                    logger.warning("On-demand population skipped: data file contains no valid lines")
                            else:
                                logger.warning(f"On-demand population skipped: data file not found at {DATA_FILE}")
                        except Exception as pop_err:
                            logger.exception(f"On-demand population failed: {pop_err}")
                finally:
                    _population_lock.release()

        # 3. Execute your core multi-agent LangGraph workflow
        thread_id = getattr(request.state, "request_id", None)
        answer = rag_pipeline_wrapper(payload.query, qdrant_client=qdrant_client, top_k=5, thread_id=payload.thread_id)
        logger.info("Raw answer from RAG pipeline: %s", answer)
        
        if answer is None:
            answer_text = "Please try again later."
            used_context = []
            suggestions = [
                "Try again later or refine your query.",
            ]
        elif isinstance(answer, dict):
            answer_text = str(answer.get("answer", ""))
            used_context = [RAGUsedContext(**ctx) for ctx in answer.get("used_context", [])]
            suggestions = [
                "Refine your query (e.g., ask about price or features)",
                "Request similar products",
                "Ask for product images or details",
            ]
        else:
            answer_text = str(answer) if answer else ""
            used_context = []
            suggestions = ["Refine your query for better matches."]
        
        return RagResponse(request_id=request.state.request_id, answer=answer_text, used_context=used_context, suggestions=suggestions)
        
    except Exception as e:
        logger.exception("RAG pipeline failed")
        return JSONResponse(
            status_code=500,
            content={
                "request_id": request.state.request_id,
                "answer": "",
                "message": f"Failed to generate response: {str(e)}",
            },
        )

api_router = APIRouter()
api_router.include_router(rag_router, prefix="/rag", tags=["RAG"])