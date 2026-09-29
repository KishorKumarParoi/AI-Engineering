"""
Nexus-AI: Agent 5 — Voice & Notification Agent
================================================
Multi-channel notification dispatcher:
- Email notifications (SMTP / SendGrid)
- WhatsApp alerts (Twilio / n8n webhook)
- Slack messages
- Text-to-Speech audio generation
- n8n workflow integration

All channels work in simulation mode for demo,
with real integration points ready for production.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── n8n Workflow Templates ───────────────────────────────────────────────
N8N_WORKFLOWS = {
    "drift_alert": {
        "name": "Model Drift Alert",
        "trigger": "webhook",
        "webhook_path": "/webhook/nexus-drift-alert",
        "nodes": [
            {"type": "webhook", "name": "Receive Drift Alert"},
            {"type": "if", "name": "Check Severity", "condition": "severity >= CRITICAL"},
            {"type": "slack", "name": "Post to #mlops-alerts"},
            {"type": "email", "name": "Email ML Team"},
            {"type": "whatsapp", "name": "WhatsApp On-Call"},
        ],
    },
    "daily_brief": {
        "name": "Daily Executive Brief",
        "trigger": "cron",
        "schedule": "0 9 * * 1-5",
        "nodes": [
            {"type": "cron", "name": "Daily 9AM Trigger"},
            {"type": "http_request", "name": "Fetch KPIs from /api/agent/analyst"},
            {"type": "template", "name": "Format Executive Report"},
            {"type": "email", "name": "Send to Leadership"},
            {"type": "slack", "name": "Post to #daily-metrics"},
        ],
    },
    "security_incident": {
        "name": "Security Incident Response",
        "trigger": "webhook",
        "webhook_path": "/webhook/nexus-security-incident",
        "nodes": [
            {"type": "webhook", "name": "Receive Security Alert"},
            {"type": "slack", "name": "Post to #security-incidents (P0)"},
            {"type": "pagerduty", "name": "Page Security On-Call"},
            {"type": "email", "name": "Email CISO"},
            {"type": "jira", "name": "Create Incident Ticket"},
        ],
    },
}


def dispatch_notification(
    title: str,
    message: str,
    channel: str = "all",
    severity: str = "INFO",
    data: dict | None = None,
) -> dict[str, Any]:
    """
    Dispatch a notification across channels.

    Channels: email, whatsapp, slack, webhook, all
    Severity: INFO, WARNING, CRITICAL, EMERGENCY
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    notification_id = f"notif_{int(time.time()*1000)}"

    payload = {
        "notification_id": notification_id,
        "title": title,
        "message": message,
        "severity": severity,
        "timestamp": timestamp,
        "data": data or {},
    }

    dispatched_channels = []

    # ── Email ────────────────────────────────────────────────────────
    if channel in ("email", "all"):
        dispatched_channels.append({
            "channel": "email",
            "status": "QUEUED",
            "config": {
                "to": "team@nexus-ai.dev",
                "subject": f"[Nexus-AI {severity}] {title}",
                "provider": "SendGrid/SMTP",
            },
        })

    # ── WhatsApp ─────────────────────────────────────────────────────
    if channel in ("whatsapp", "all"):
        dispatched_channels.append({
            "channel": "whatsapp",
            "status": "QUEUED",
            "config": {
                "provider": "Twilio WhatsApp Business API",
                "to": "+91-XXXXXXXXXX",
                "template": "nexus_alert_template",
            },
        })

    # ── Slack ────────────────────────────────────────────────────────
    if channel in ("slack", "all"):
        slack_color = {
            "INFO": "#36a64f",
            "WARNING": "#f2c744",
            "CRITICAL": "#e01e5a",
            "EMERGENCY": "#ff0000",
        }.get(severity, "#36a64f")

        dispatched_channels.append({
            "channel": "slack",
            "status": "QUEUED",
            "config": {
                "channel": "#nexus-ai-alerts",
                "color": slack_color,
                "webhook_url": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
            },
        })

    # ── n8n Webhook ──────────────────────────────────────────────────
    if channel in ("webhook", "all"):
        dispatched_channels.append({
            "channel": "n8n_webhook",
            "status": "QUEUED",
            "config": {
                "url": "http://localhost:5678/webhook/nexus-alert",
                "method": "POST",
                "payload_size": len(json.dumps(payload)),
            },
        })

    # ── TTS Audio ────────────────────────────────────────────────────
    tts_text = f"Attention: {title}. {message}"

    return {
        "agent": "VoiceNotifyAgent",
        "type": "notification_dispatch",
        "notification_id": notification_id,
        "channels_dispatched": len(dispatched_channels),
        "channels": dispatched_channels,
        "tts_text": tts_text,
        "tts_status": "AUDIO_READY",
        "payload": payload,
        "demo_mode": True,
        "message": f"Notification dispatched to {len(dispatched_channels)} channels (demo mode)",
    }


def get_n8n_workflows() -> dict[str, Any]:
    """Return available n8n workflow configurations."""
    return {
        "agent": "VoiceNotifyAgent",
        "type": "n8n_workflows",
        "workflow_count": len(N8N_WORKFLOWS),
        "workflows": N8N_WORKFLOWS,
        "n8n_url": "http://localhost:5678",
        "status": "CONFIGURED",
    }


def analyze_query(query: str) -> dict[str, Any]:
    """Route notification agent queries."""
    q = query.lower()

    if any(kw in q for kw in ["alert", "notify", "send", "dispatch"]):
        severity = "CRITICAL" if "critical" in q else ("WARNING" if "warn" in q else "INFO")
        return dispatch_notification(
            title="Nexus-AI Alert",
            message=query,
            channel="all",
            severity=severity,
        )

    elif any(kw in q for kw in ["n8n", "workflow", "automation"]):
        return get_n8n_workflows()

    elif any(kw in q for kw in ["voice", "tts", "speak", "audio"]):
        return {
            "agent": "VoiceNotifyAgent",
            "type": "tts_generation",
            "text": query,
            "tts_status": "AUDIO_READY",
            "audio_format": "wav",
            "provider": "gTTS / Google Cloud TTS",
            "message": "Text-to-Speech audio generated (demo mode)",
        }

    else:
        return dispatch_notification(
            title="Nexus-AI Status Update",
            message=query,
            channel="slack",
            severity="INFO",
        )
