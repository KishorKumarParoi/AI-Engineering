"""
Model Context Protocol (MCP) Integration for Enterprise AI Security Platform.
Exposes security microservice tools via the FastMCP standard.
"""

from app.mcp.security_client import security_mcp_client

__all__ = ["security_mcp_client"]
