import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient

from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse

from api.api.models import RagRequest, RagResponse, RAGUsedContext

import logging

# from api.agents.prod_retrieval_agents.retrieval_generation import rag_pipeline
# from api.agents.prod_retrieval_agents.structured_retrieval_generation import rag_pipeline_wrapper
# from api.agents.prod_retrieval_agents.hybrid_search_retrieval_generation import rag_pipeline_wrapper
# from api.agents.prod_retrieval_agents.hybrid_search_rerank_retrieval_generation import rag_pipeline_wrapper
from api.agents.prod_retrieval_agents.single_turn_in_retrieval_generation import rag_pipeline_wrapper

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

qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)

if qdrant_url and "qdrant:6333" in qdrant_url:
    # Docker service host is not resolvable from a local notebook kernel
    qdrant_url = qdrant_url.replace("qdrant:6333", "localhost:6333")

rag_router = APIRouter()


@rag_router.post("/")
def rag(
    request: Request,
    payload: RagRequest
) -> RagResponse:
    logger.info(f"Received request: {payload}")

    try:
        # raw_answer = rag_pipeline(payload.query, qdrant_client=qdrant_client, top_k=5)
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