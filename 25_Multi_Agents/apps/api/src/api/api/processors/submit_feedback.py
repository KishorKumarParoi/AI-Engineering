import uuid
import logging
from langsmith import Client

logger = logging.getLogger(__name__)
client = Client()

def submit_feedback(trace_id: str, feedback_score: int | None = None, feedback_text: str = "", feedback_source_type: str = "api"):
    try:
        uuid.UUID(str(trace_id))
    except (ValueError, TypeError):
        logger.warning(f"Skipping feedback submission: invalid or empty trace_id: {trace_id}")
        return

    try:
        if feedback_score is not None:
            client.create_feedback(
                run_id=trace_id,
                key="thumbs",
                score=feedback_score,
                feedback_source_type=feedback_source_type
            )
        if len(feedback_text) > 0:
            client.create_feedback(
                run_id=trace_id,
                key="comment",
                comment=feedback_text,
                feedback_source_type=feedback_source_type
            )
    except Exception as e:
        logger.exception(f"Failed to submit feedback to LangSmith: {e}")
        