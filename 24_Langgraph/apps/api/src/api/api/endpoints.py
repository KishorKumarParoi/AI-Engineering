import os
import logging
import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse  # Moved up here to avoid NameError

from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse

from api.api.models import RagRequest, RagResponse, RAGUsedContext
from api.agents.prod_retrieval_agents.single_turn_in_retrieval_generation import rag_pipeline_wrapper
from api.api.populate_data import populate_qdrant, retrieve_data

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

DATA_PATH = "data/Data_With_Images.jsonl" 

# 1. RUN DATA POPULATION AT APP BOOT LIFECYCLE (PROVISIONED WITH WHITE-SPACE STRIPPER)
try:
    COLLECTION_NAME = os.environ.get("collection_name") or "Amazon_Electronics_Products"
        
    try:
        qdrant_data = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        logger.info("Qdrant collection metadata retrieved successfully: %s", qdrant_data)
    except UnexpectedResponse as e:
        if e.status_code == 404:
            logger.warning(f"Collection '{COLLECTION_NAME}' does not exist. Initializing populate routine...")
            
            try:
                if not os.path.exists(DATA_PATH):
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    print(f"Current directory for data path resolution: {current_dir}")
                    # Climbs up 5 levels dynamically to project root and joins 'data/Data_With_Images.jsonl'
                    DATA_PATH = os.path.abspath(os.path.join(
                        current_dir, 
                        "../../../../../data/Data_With_Images.jsonl"
                    ))
                
                # Check file baseline
                if os.path.exists(DATA_PATH) and os.path.getsize(DATA_PATH) > 0:
                    # Clean trailing whitespaces/newlines out of stream to prevent ValueError
                    with open(DATA_PATH, 'r', encoding='utf-8') as f:
                        valid_lines = [line.strip() for line in f if line.strip()]
                    
                    if not valid_lines:
                        raise ValueError("Data file is empty or contains only whitespace lines.")
                    
                    from io import StringIO
                    clean_json_stream = StringIO("\n".join(valid_lines))
                    
                    df = pd.read_json(clean_json_stream, lines=True)
                    logger.info(f"Successfully loaded dataset of shape: {df.shape}")
                    
                    # Recreates and populates vector space schemas dynamically!
                    populate_qdrant(df, qdrant_client, collection_name=COLLECTION_NAME)
                else:
                    raise FileNotFoundError()
                
                # 2. Testing with sample query to see if retrieval works now
                try:
                    sample_answer = retrieve_data(qdrant_client, query="What kind of Laptop do you offer?", collection_name=COLLECTION_NAME, k=10)
                    print("Sample retrieval answer:", sample_answer)
                except Exception as look_err:
                    logger.error(f"Error during sample retrieval after population: {look_err}")
                    
            except FileNotFoundError:
                raise ValueError(
                    f"Could not automatically populate because data file wasn't found at {DATA_PATH}. "
                    f"Please verify your Docker compose volume mount paths."
                )
        else:
            raise e
except Exception as init_err:
    logger.exception(f"Initialization failed: {init_err}")


rag_router = APIRouter()

@rag_router.post("/")
def rag(
    request: Request,
    payload: RagRequest
) -> RagResponse:
    logger.info(f"Received request: {payload}")

    try:  # <-- FIXED: Restored missing parent try-block here
        # 3. Execute your core multi-agent LangGraph workflow
        answer = rag_pipeline_wrapper(payload.query, qdrant_client=qdrant_client, top_k=5)
        logger.info("Raw answer from RAG pipeline: %s", answer)
        
        if answer is None:
            answer_text = "Please try again later."
            used_context = []
        elif isinstance(answer, dict):
            answer_text = str(answer.get("answer", ""))
            used_context = [RAGUsedContext(**ctx) for ctx in answer.get("used_context", [])]
        else:
            answer_text = str(answer) if answer else ""
            used_context = []
        
        return RagResponse(request_id=request.state.request_id, answer=answer_text, used_context=used_context)
        
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