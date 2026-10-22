"""
Model Context Protocol (MCP) Client Package for Advanced AI Production Chatbot.
Provides centralized discovery, capability negotiation, and remote tool execution
over the Anthropic Model Context Protocol standard.
"""

from api.mcp.client import MCPClientManager, mcp_client_manager

__all__ = ["MCPClientManager", "mcp_client_manager"]
