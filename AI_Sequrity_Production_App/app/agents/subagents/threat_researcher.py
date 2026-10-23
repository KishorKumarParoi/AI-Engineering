import re
import logging
from typing import Dict, Any
from app.agents.state import SupervisorState
from app.services.search import search_service
from app.mcp.security_client import security_mcp_client

logger = logging.getLogger("ThreatResearcherAgent")


def threat_researcher_node(state: SupervisorState) -> Dict[str, Any]:
    """
    Agent 1: Live Threat Intelligence & Web Reconnaissance.
    - Uses Tavily & Serper for live vulnerability and threat actor data.
    - Interrogates FastMCP tools for official CVE definitions and indicator reputations.
    """
    query = state.get("current_query", "")
    logger.info(f"🕵️ [Agent 1: ThreatResearcher] Executing intelligence recon for: '{query[:60]}'")

    # 1. LIVE WEB RECONNAISSANCE VIA TAVILY + SERPER
    web_findings = search_service.hybrid_search(query, max_results=5)

    # 2. EXTRACT CVE IDENTIFIERS & QUERY MCP CVE SERVICE
    cve_pattern = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
    matched_cves = cve_pattern.findall(query)
    cve_details = []
    for cve in set(matched_cves):
        mcp_res = security_mcp_client.call_tool("cve_lookup", {"cve_id": cve})
        cve_details.append(mcp_res)

    # 3. EXTRACT IP / HOST INDICATORS & QUERY MCP THREAT FEED
    ip_pattern = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
    matched_ips = ip_pattern.findall(query)
    ip_reputations = []
    for ip in set(matched_ips):
        rep = security_mcp_client.call_tool("threat_intel_feed", {"indicator": ip})
        ip_reputations.append(rep)

    summary_bullets = []
    for res in web_findings[:3]:
        summary_bullets.append(f"• [{res.get('source', 'web')}] {res.get('title')}: {res.get('snippet')[:160]}...")
    for cve in cve_details:
        d = cve.get("details", {})
        summary_bullets.append(f"• [MCP NVD] {cve.get('cve_id')}: CVSS {d.get('cvss')} ({d.get('severity')}) - {d.get('description')}")

    intel_result = {
        "agent": "threat_researcher",
        "web_results": web_findings,
        "cve_records": cve_details,
        "indicator_reputations": ip_reputations,
        "intelligence_summary": "\n".join(summary_bullets) if summary_bullets else "No critical live zero-days surfaced.",
        "status": "completed"
    }

    # Update completed steps
    completed = list(state.get("completed_steps", []))
    completed.append("threat_research")

    return {
        "threat_intel": intel_result,
        "completed_steps": completed,
        "status": "Threat research completed."
    }
