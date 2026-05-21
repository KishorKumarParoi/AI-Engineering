import openai
from pydantic import BaseModel, Field
import instructor

import os
from dotenv import load_dotenv

# Load environment variables from .env file
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
    

class RagRequest(BaseModel):
    query: str = Field(..., description="The user's query to be used in the RAG pipeline")

class RAGUsedContext(BaseModel):
    id: str = Field(description="The ID of the retrieved review")
    review: str = Field(description="The text of the retrieved review")

class RagResponse(BaseModel):
    request_id: str = Field(..., description="The request ID")
    answer: str = Field(..., description="The answer to the query")
    used_context: list[RAGUsedContext] = Field([], description="The context that was used to generate the answer")

client = instructor.from_openai(openai.OpenAI())

class RagGenerationResponse(BaseModel):
    answer: str = Field(description="The answer to the question")
    reasoning: str = Field(description="The reasoning behind the answer")

class RagGenerationResponseReference(BaseModel):
    answer: str = Field(description="The answer to the question")
    reasoning: str = Field(description="The reasoning behind the answer")
    used_context: list[RAGUsedContext] = Field(description="The list of retrieved reviews used to generate the answer")
    references: list[RAGUsedContext] = Field(description="The list of references used to generate the answer")
