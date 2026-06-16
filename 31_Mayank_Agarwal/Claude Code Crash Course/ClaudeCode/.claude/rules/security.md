---
description: Security rules - never violate these
---
- Never hardcode credentials, API keys, or passwords
- Always use environment variables for secrets
- Sanitise all user inputs before using them
- Never use eval() in JavaScript
- Always parameterise database queries (no string concatenation)