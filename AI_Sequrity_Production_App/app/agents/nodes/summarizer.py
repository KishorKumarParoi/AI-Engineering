"""Conversation history summarizer to prevent exceeding context window limits."""

from app.gateway import portkey_client
from app.config import settings
import logfire


def summarize_conversation_if_needed(messages: list[dict], max_turns: int = 10) -> list[dict]:
    """Compress older conversation turns into a unified context summary."""
    if len(messages) <= max_turns:
        return messages

    with logfire.span("Compressing conversation history"):
        older = messages[:-4]
        recent = messages[-4:]
        summary_prompt = "Summarize the key facts from this chat history concisely:\n"
        for m in older:
            summary_prompt += f"{m.get('role')}: {m.get('content')}\n"

        resp = portkey_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0,
        )
        summary_text = resp.choices[0].message.content
        return [{"role": "assistant", "content": f"[Previous Conversation Summary: {summary_text}]"}] + recent
