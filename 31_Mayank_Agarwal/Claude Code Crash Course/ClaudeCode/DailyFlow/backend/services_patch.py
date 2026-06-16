# Patch to add fallback briefing when Gemini API fails

original_get_briefing = get_briefing

def get_briefing_with_fallback() -> dict:
    """Return today's briefing, with fallback if AI is unavailable."""
    try:
        return original_get_briefing()
    except RuntimeError:
        # Fallback when Gemini API fails
        today = today_str()
        return {
            "date": today,
            "quote": "Every day is a chance to improve.",
            "focus_tip": "Start your day by identifying your top 3 priorities.",
            "message": "Focus on what matters most. You've got this!"
        }

# Replace the function
get_briefing = get_briefing_with_fallback
