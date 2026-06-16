---
name: morning-briefing
description: Generates and displays the DailyPulse morning briefing. Use at the start of every work session.
trigger: /morning-briefing
effort: low
---

# Morning Briefing

Fetches your daily briefing from DailyPulse and shows a task summary to help you focus.

```bash
#!/bin/bash
# Morning briefing skill for DailyPulse

set -e

API="http://localhost:8000"

echo ""
echo "🌅 Fetching your morning briefing..."
echo ""

# Fetch briefing
BRIEFING=$(curl -s "$API/briefing")
BRIEFING_TEXT=$(echo "$BRIEFING" | jq -r '.briefing // empty')

if [ -z "$BRIEFING_TEXT" ] || [ "$BRIEFING_TEXT" = "null" ]; then
  echo "⏳ Generating briefing..."
  BRIEFING=$(curl -s "$API/briefing")
  BRIEFING_TEXT=$(echo "$BRIEFING" | jq -r '.briefing // empty')
fi

# Display briefing if available
if [ -n "$BRIEFING_TEXT" ] && [ "$BRIEFING_TEXT" != "null" ]; then
  echo "═══════════════════════════════════════════════════════"
  echo "📋 Morning Briefing"
  echo "═══════════════════════════════════════════════════════"
  echo ""
  echo "$BRIEFING_TEXT"
  echo ""
fi

# Fetch tasks
TASKS=$(curl -s "$API/tasks")

# Calculate stats
TOTAL=$(echo "$TASKS" | jq 'length')
PENDING=$(echo "$TASKS" | jq '[.[] | select(.completed == false)] | length')
TODAY_COMPLETED=$(echo "$TASKS" | jq "[.[] | select(.completed == true)] | length")

# Get yesterday's completion count (macOS compatible)
YESTERDAY=$(date -v-1d '+%Y-%m-%d')
YESTERDAY_COMPLETED=$(echo "$TASKS" | jq "[.[] | select(.completed == true and (.completed_at | startswith(\"$YESTERDAY\")))] | length" 2>/dev/null || echo "0")

echo "═══════════════════════════════════════════════════════"
echo "📊 Task Summary"
echo "═══════════════════════════════════════════════════════"
echo ""
printf "  %-25s %d\n" "Total tasks:" "$TOTAL"
printf "  %-25s %d\n" "Pending:" "$PENDING"
printf "  %-25s %d\n" "Completed today:" "$TODAY_COMPLETED"
if [ "$YESTERDAY_COMPLETED" -gt 0 ]; then
  printf "  %-25s %d\n" "Completed yesterday:" "$YESTERDAY_COMPLETED"
fi
echo ""

# Suggest focus
if [ "$PENDING" -gt 0 ]; then
  echo "🎯 Suggested Focus Areas"
  echo "─────────────────────────────────────────────────────"
  echo "$TASKS" | jq -r '.[] | select(.completed == false) | "  • " + .title' | head -3
  echo ""
fi

echo "═══════════════════════════════════════════════════════"
echo ""
```
