from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class RAGUsedContext(BaseModel):
    id: str | int = Field(description="The ID of the retrieved context/product")
    description: Optional[Union[str, List[str]]] = Field(default=None, description="The product description")
    title: Optional[str] = Field(default=None, description="Product title")
    price: Optional[float] = Field(default=None, description="Product price")
    rating: Optional[float] = Field(default=None, description="Product rating")
    images: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Product images")


class RagRequest(BaseModel):
    query: str = Field(..., description="The user's query to be processed by the RAG pipeline")
    thread_id: Optional[str] = Field(default=None, description="Unique session thread ID for LangGraph state persistence")


class RagResponse(BaseModel):
    request_id: str = Field(..., description="The request ID")
    answer: str = Field(..., description="The generated response to the query")
    used_context: List[RAGUsedContext] = Field(default_factory=list, description="Context chunks utilized")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    trace_id: Optional[str] = Field(default=None, description="Distributed tracing identifier")


class FeedbackRequest(BaseModel):
    feedback_score: Optional[int] = Field(..., description="1 for positive thumbs up, -1 or 0 for negative")
    feedback_text: str = Field(..., description="Qualitative feedback string")
    trace_id: str = Field(..., description="Distributed trace ID")
    thread_id: str = Field(..., description="Thread session identifier")
    feedback_source_type: str = Field(..., description="UI feedback source")


class FeedbackResponse(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Status of the feedback submission")


class HITLApprovalRequest(BaseModel):
    thread_id: str = Field(..., description="Thread ID of the interrupted session awaiting approval")
    decision: str = Field(..., description="'approved' to authorize the sensitive action, 'rejected' to decline")
    supervisor_notes: Optional[str] = Field(default="", description="Optional supervisor rationale")


class HITLApprovalResponse(BaseModel):
    request_id: str = Field(..., description="Request identifier")
    status: str = Field(..., description="'success' or 'error'")
    action_id: Optional[str] = Field(default=None, description="Unique action ID")
    decision: str = Field(..., description="Resolution decision recorded")
    message: str = Field(..., description="Human-readable resolution message")
    resolution_summary: Optional[str] = Field(default=None, description="Detailed action summary")
