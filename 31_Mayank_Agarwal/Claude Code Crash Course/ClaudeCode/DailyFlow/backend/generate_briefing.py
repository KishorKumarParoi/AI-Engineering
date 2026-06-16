#!/usr/bin/env python3
"""Generate and save daily briefing from the DailyPulse API."""

import json
import sys
from datetime import datetime

import requests


def generate_daily_briefing() -> None:
    """Fetch briefing from API and save to dated file."""
    try:
        # Call the briefing endpoint
        response = requests.get("http://localhost:8000/briefing", timeout=10)
        response.raise_for_status()

        briefing_data = response.json()

        # Create dated filename
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"data/briefing_{today}.json"

        # Save to file
        with open(filename, "w") as f:
            json.dump(briefing_data, f, indent=2)

        print(f"✓ Briefing saved to {filename}")

    except requests.exceptions.ConnectionError:
        print(
            "✗ Could not connect to backend. Make sure uvicorn is running on port 8000",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    generate_daily_briefing()
