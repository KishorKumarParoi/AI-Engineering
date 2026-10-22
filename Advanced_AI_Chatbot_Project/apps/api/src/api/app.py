from fastapi import FastAPI, Request
from pydantic import BaseModel
import logging

from api.core.config import config
from api.api.endpoints import api_router
from api.api.middleware import RequestIDMiddleware
from api.security.bot_shield import BotShieldMiddleware, bot_shield_stats
from api.mcp.client import mcp_client_manager
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise AI Production Chatbot API",
    description="Multi-Agent RAG Orchestrator with LangGraph, Model Context Protocol (MCP), HITL Governance, and BotShield Security.",
    version="2.0.0"
)

# Enterprise WAF & BotShield Guardrail
app.add_middleware(BotShieldMiddleware)
app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health", tags=["system"])
def health():
    return {
        "status": "healthy",
        "service": "enterprise_ai_chatbot_api",
        "version": "2.0.0",
        "security": bot_shield_stats.to_dict(),
        "mcp_cluster": mcp_client_manager.check_server_health(),
    }

app.include_router(api_router)