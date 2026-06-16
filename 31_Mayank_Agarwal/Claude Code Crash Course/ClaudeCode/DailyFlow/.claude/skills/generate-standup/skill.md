---
name: generate-standup
description: Generates a professional standup from today's DailyPulse tasks. Use before your daily standup meeting.
trigger: /generate-standup
effort: low
---

# Generate Standup

Fetches your completed and pending tasks from DailyPulse and formats them as a professional standup report.

```bash
#!/bin/bash
# Generate standup skill for DailyPulse

set -e

API="http://localhost:8000"

echo ""
echo "📝 Generating your standup..."
echo ""

# Fetch standup data
RESPONSE=$(curl -s "$API/standup")
STANDUP_TEXT=$(echo "$RESPONSE" | jq -r '.standup')

# Format the standup
FORMATTED=""
FORMATTED+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
FORMATTED+="STANDUP REPORT — $(date '+%B %d, %Y')\n"
FORMATTED+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
FORMATTED+="\n"

# Parse the standup text and format it nicely
FORMATTED+="$(echo -e "$STANDUP_TEXT" | sed 's/\*\*//g')\n"
FORMATTED+="\n"

# Blockers section header
FORMATTED+="🚧 ADDITIONAL BLOCKERS\n"
FORMATTED+="─────────────────────────────────────────────────────\n"

# Print the formatted standup
echo -e "$FORMATTED"

# Ask about blockers
echo "Do you have any additional blockers? (Press Enter to skip)"
read -r BLOCKER

if [ -n "$BLOCKER" ]; then
  FORMATTED+="  • $BLOCKER\n"
  echo -e "  • $BLOCKER\n"
else
  FORMATTED+="  None.\n"
  echo -e "  None.\n"
fi

FORMATTED+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ask to copy to clipboard
echo "Copy to clipboard? (y/n)"
read -r COPY_CHOICE

if [[ "$COPY_CHOICE" =~ ^[Yy]$ ]]; then
  # Clean up the formatted string for clipboard
  CLEAN_STANDUP=$(echo -e "$FORMATTED" | sed 's/\\n/\n/g')
  
  # Detect OS and use appropriate clipboard command
  if command -v pbcopy &> /dev/null; then
    echo -e "$CLEAN_STANDUP" | pbcopy
    echo "✨ Copied to clipboard!"
  elif command -v xclip &> /dev/null; then
    echo -e "$CLEAN_STANDUP" | xclip -selection clipboard
    echo "✨ Copied to clipboard!"
  elif command -v clip &> /dev/null; then
    echo -e "$CLEAN_STANDUP" | clip
    echo "✨ Copied to clipboard!"
  else
    echo "❌ Clipboard command not found on this system."
  fi
else
  echo "Standup ready to share!"
fi

echo ""
```
