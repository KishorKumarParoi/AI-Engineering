import os
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("SecurityMCPClient")

MCP_SERVER_URL = os.getenv("MCP_SECURITY_URL", "http://localhost:8008")


class SecurityMCPClientManager:
    """
    Model Context Protocol (MCP) Client Manager.
    Connects agents to the FastMCP Security Microservice over HTTP JSON-RPC,
    with automatic failover to local execution if the microservice is cycling.
    """

    def __init__(self):
        self.server_url = MCP_SERVER_URL
        self._http_client = httpx.Client(timeout=8.0)

    def check_health(self) -> Dict[str, Any]:
        """Checks the real-time status of the MCP Security Server."""
        try:
            res = self._http_client.get(f"{self.server_url}/", timeout=2.0)
            return {
                "server_url": self.server_url,
                "status": "connected" if res.status_code in (200, 404, 405) else "unhealthy",
                "code": res.status_code
            }
        except Exception as e:
            return {
                "server_url": self.server_url,
                "status": "in_process_fallback_active",
                "error": str(e)
            }

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a tool call over the standard Model Context Protocol."""
        logger.info(f"🔌 [MCP Protocol] Dispatching '{tool_name}' with args {arguments}")
        try:
            res = self._http_client.post(
                f"{self.server_url}/tools/{tool_name}",
                json=arguments,
                headers={"Content-Type": "application/json"},
                timeout=6.0
            )
            if res.status_code == 200:
                data = res.json()
                return data.get("content", data)
        except Exception as err:
            logger.debug(f"Remote MCP server {self.server_url} unreachable ({err}); invoking in-process fallback.")

        # In-process graceful fallback
        from app.mcp.security_server import cve_lookup, threat_intel_feed, waf_metrics
        if tool_name == "cve_lookup":
            return cve_lookup(arguments.get("cve_id", ""))
        elif tool_name == "threat_intel_feed":
            return threat_intel_feed(arguments.get("indicator", ""))
        elif tool_name == "waf_metrics":
            return waf_metrics()
        else:
            return {"error": f"Unknown tool '{tool_name}'"}


security_mcp_client = SecurityMCPClientManager()
