from pydantic import BaseModel, Field

class RagRequest(BaseModel):
    query: str = Field(..., description="The user's query to be used in the RAG pipeline")

class RagResponse(BaseModel):
    request_id: str = Field(..., description="The request ID")
    answer: str = Field(..., description="The answer to the query")