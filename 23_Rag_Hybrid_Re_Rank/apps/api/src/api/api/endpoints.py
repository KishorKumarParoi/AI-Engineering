import os

from qdrant_client import QdrantClient

from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse

from api.api.models import RagRequest, RagResponse, RAGUsedContext

import logging

# from api.agents.retrieval_generation import rag_pipeline
# from api.agents.structured_retrieval_generation import rag_pipeline_wrapper
# from api.agents.hybrid_search_retrieval_generation import rag_pipeline_wrapper

from api.agents.hybrid_search_rerank_retrieval_generation import rag_pipeline_wrapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))  

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
        print("Raw answer from RAG pipeline:", answer)
        
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