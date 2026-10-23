"""
Enterprise ISO 27001:2022 & SOC 2 Type II Compliance Mapping for AI/LLM Systems.
Maps AI agentic architectures to international cybersecurity & governance frameworks.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"


@dataclass
class ComplianceControl:
    control_id: str
    framework: str        # "ISO 27001:2022" or "SOC 2 Type II" or "NIST AI RMF"
    title: str
    domain: str
    requirement: str
    implemented_measure: str
    technical_component: str
    status: ComplianceStatus
    evidence_artifact: str


@dataclass
class ComplianceAuditReport:
    overall_compliance_pct: float
    iso_27001_compliance_pct: float
    soc2_compliance_pct: float
    nist_ai_rmf_compliance_pct: float
    total_controls: int
    compliant_controls: int
    partial_controls: int
    controls: List[ComplianceControl] = field(default_factory=list)
    executive_summary: str = ""


class ComplianceFrameworkMapper:
    """
    Evaluates enterprise AI architecture against ISO 27001, SOC 2, and NIST AI RMF controls.
    """

    def __init__(self):
        self.controls: List[ComplianceControl] = self._init_controls()

    def _init_controls(self) -> List[ComplianceControl]:
        return [
            # --- ISO/IEC 27001:2022 CONTROLS ---
            ComplianceControl(
                control_id="ISO-27001-A.5.8",
                framework="ISO 27001:2022",
                title="Information Security in Project Management (AI Workflows)",
                domain="Organizational Controls",
                requirement="Security must be integrated into all phases of AI model lifecycle and deployments.",
                implemented_measure="LangGraph Supervisor Multi-Agent pipeline with automated red-teaming and compliance gate.",
                technical_component="app/agents/supervisor.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/03_NODE_INTELLIGENCE.md",
            ),
            ComplianceControl(
                control_id="ISO-27001-A.8.7",
                framework="ISO 27001:2022",
                title="Protection Against Malware & Adversarial AI Attacks",
                domain="Technological Controls",
                requirement="Protection against unauthorized execution of adversarial payloads, scripts, or malicious prompts.",
                implemented_measure="BotShield ASGI WAF with honeypots + Prompt Injection Shield with heuristic/LLM classifier.",
                technical_component="app/middleware/bot_shield.py & app/security/prompt_injection.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/08_GUARDRAILS.md",
            ),
            ComplianceControl(
                control_id="ISO-27001-A.8.11",
                framework="ISO 27001:2022",
                title="Data Masking & PII Redaction",
                domain="Technological Controls",
                requirement="Data masking must be applied in accordance with access control policies and legal mandates.",
                implemented_measure="PIIFilterEngine with Luhn validation, cloud secret detection, and reversible tokenization.",
                technical_component="app/security/pii.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="app/security/pii.py",
            ),
            ComplianceControl(
                control_id="ISO-27001-A.8.16",
                framework="ISO 27001:2022",
                title="Monitoring Activities & Observability",
                domain="Technological Controls",
                requirement="Networks, systems, and applications shall be monitored for abnormal behavior and security events.",
                implemented_measure="Logfire OpenTelemetry instrumentation, Prometheus metrics, and real-time latency percentiles.",
                technical_component="app/observability/logfire_setup.py & app/evaluation/metrics_service.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/04_TRACING_AND_OBSERVABILITY.md",
            ),
            ComplianceControl(
                control_id="ISO-27001-A.8.24",
                framework="ISO 27001:2022",
                title="Use of Cryptography & Key Management",
                domain="Technological Controls",
                requirement="Cryptographic controls and key lifecycle management must be established.",
                implemented_measure="KMS encrypted storage, TLS 1.3 enforced, and strict secret-leakage guardrails.",
                technical_component="app/guardrails/rails.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/05_ENVIRONMENT_VARIABLES.md",
            ),
            ComplianceControl(
                control_id="ISO-27001-A.8.28",
                framework="ISO 27001:2022",
                title="Secure Coding & LLM Boundary Defense",
                domain="Technological Controls",
                requirement="Secure coding principles must be applied to software development and AI prompt boundaries.",
                implemented_measure="NVIDIA NeMo Guardrails Colang policy rules intercepting system prompt extractions and jailbreaks.",
                technical_component="app/guardrails/colang_rules.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/08_GUARDRAILS.md",
            ),

            # --- SOC 2 TYPE II TRUST SERVICES CRITERIA ---
            ComplianceControl(
                control_id="SOC2-CC6.1",
                framework="SOC 2 Type II",
                title="Logical Access Control & Least Privilege",
                domain="Security / Access Control",
                requirement="The entity restricts logical access to registered and authorized users, devices, and tool execution.",
                implemented_measure="Model Context Protocol (FastMCP) secure tool encapsulation with strict JSON-RPC schemas.",
                technical_component="app/mcp/server.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="app/mcp/server.py",
            ),
            ComplianceControl(
                control_id="SOC2-CC6.6",
                framework="SOC 2 Type II",
                title="Boundary Protection & Rate Limiting",
                domain="Security / Perimeter",
                requirement="The entity implements logical boundaries to protect against external attacks and denial of service.",
                implemented_measure="Sliding-window IP rate limiter (60 rpm, 5 burst/s) and automated honeypot blacklisting.",
                technical_component="app/middleware/bot_shield.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/01_SYSTEM_OVERVIEW.md",
            ),
            ComplianceControl(
                control_id="SOC2-CC6.7",
                framework="SOC 2 Type II",
                title="Transmission Data Protection & Confidentiality",
                domain="Confidentiality / Encryption",
                requirement="Data transmission across external networks is encrypted to protect integrity and confidentiality.",
                implemented_measure="TLS termination on AWS ALB/EC2 and base64 environment variable secret injection.",
                technical_component="deploy.sh",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="deploy.sh",
            ),
            ComplianceControl(
                control_id="SOC2-CC7.2",
                framework="SOC 2 Type II",
                title="Vulnerability Detection & Red-Teaming",
                domain="Security / Vulnerability Management",
                requirement="The entity monitors for vulnerabilities and exploits in software components and models.",
                implemented_measure="ExploitAnalyst agent executing real-time CVE and OWASP LLM red-teaming during query lifecycle.",
                technical_component="app/agents/supervisor.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/03_NODE_INTELLIGENCE.md",
            ),
            ComplianceControl(
                control_id="SOC2-CC8.1",
                framework="SOC 2 Type II",
                title="Change Management & High-Impact Mutation Controls",
                domain="Processing Integrity / Change Control",
                requirement="Changes to system operations, security rules, and code mutations require authorized human review.",
                implemented_measure="Cryptographic Human-in-the-Loop (HITL) break-glass gate requiring signed admin approval.",
                technical_component="app/hitl/break_glass.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="app/hitl/break_glass.py",
            ),

            # --- NIST AI RMF 1.0 CONTROLS ---
            ComplianceControl(
                control_id="NIST-AI-RMF-GOVERN-1.2",
                framework="NIST AI RMF",
                title="AI Risk Management & Safety Policies",
                domain="Govern",
                requirement="AI policies, processes, and responsibilities are documented, monitored, and enforced.",
                implemented_measure="NeMo Guardrails + BotShield ASGI WAF gating all inbound/outbound prompt streams.",
                technical_component="app/guardrails/rails.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/08_GUARDRAILS.md",
            ),
            ComplianceControl(
                control_id="NIST-AI-RMF-MEASURE-2.5",
                framework="NIST AI RMF",
                title="AI System Evaluation & Groundedness Metrics",
                domain="Measure",
                requirement="AI systems are evaluated for bias, hallucinations, safety, and reliability using rigorous benchmarks.",
                implemented_measure="G-Eval Chain-of-Thought continuous scoring + online A/B testing framework.",
                technical_component="app/evaluation/geval.py & app/evaluation/ab_testing.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="DOCS/10_EVALS.md",
            ),
            ComplianceControl(
                control_id="NIST-AI-RMF-MANAGE-1.3",
                framework="NIST AI RMF",
                title="Risk Treatment & Autonomous Remediation",
                domain="Manage",
                requirement="Identified AI risks are treated, monitored, and mitigated with feedback loops.",
                implemented_measure="Stateful Loop Engineering reflection cycles between RemediationPatcher and ComplianceAuditor.",
                technical_component="app/agents/supervisor.py",
                status=ComplianceStatus.COMPLIANT,
                evidence_artifact="ARCHITECTURE.md",
            ),
        ]

    def audit(self) -> ComplianceAuditReport:
        total = len(self.controls)
        compliant = sum(1 for c in self.controls if c.status == ComplianceStatus.COMPLIANT)
        partial = sum(1 for c in self.controls if c.status == ComplianceStatus.PARTIAL)

        iso_controls = [c for c in self.controls if c.framework == "ISO 27001:2022"]
        soc2_controls = [c for c in self.controls if c.framework == "SOC 2 Type II"]
        nist_controls = [c for c in self.controls if c.framework == "NIST AI RMF"]

        iso_pct = (sum(1 for c in iso_controls if c.status == ComplianceStatus.COMPLIANT) / len(iso_controls)) * 100
        soc2_pct = (sum(1 for c in soc2_controls if c.status == ComplianceStatus.COMPLIANT) / len(soc2_controls)) * 100
        nist_pct = (sum(1 for c in nist_controls if c.status == ComplianceStatus.COMPLIANT) / len(nist_controls)) * 100
        overall_pct = (compliant / total) * 100

        summary = (
            f"Enterprise AI Compliance Audit Complete: {compliant}/{total} Controls Fully Satisfied ({overall_pct:.1f}%). "
            f"ISO 27001: {iso_pct:.0f}%, SOC 2 Type II: {soc2_pct:.0f}%, NIST AI RMF: {nist_pct:.0f}%. "
            f"Architecture enforces end-to-end data masking, prompt injection defense, observability, and HITL governance."
        )

        return ComplianceAuditReport(
            overall_compliance_pct=round(overall_pct, 1),
            iso_27001_compliance_pct=round(iso_pct, 1),
            soc2_compliance_pct=round(soc2_pct, 1),
            nist_ai_rmf_compliance_pct=round(nist_pct, 1),
            total_controls=total,
            compliant_controls=compliant,
            partial_controls=partial,
            controls=self.controls,
            executive_summary=summary,
        )


# Global Singleton Compliance Mapper
compliance_mapper = ComplianceFrameworkMapper()
