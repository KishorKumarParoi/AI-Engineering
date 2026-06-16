# Project: Task Manager App

## What This Is
A web-based task management app for personal productivity.
Stack: HTML, CSS, vanilla JavaScript. No frameworks. No build tools.
The goal is simplicity — it should work by opening index.html directly.

## Project Structure
- index.html — main app shell
- style.css — all styling (no inline styles)  
- app.js — all JavaScript (no jQuery)
- data/ — JSON files for local storage backup

## Coding Standards
- Use camelCase for all JavaScript variables and functions
- CSS classes use kebab-case (e.g., task-item, priority-high)
- Every function must have a JSDoc comment
- No console.log in final code — use a debug flag instead
- Mobile-first CSS — base styles for mobile, media queries for desktop

## Behaviour Rules
- Never use alert() or confirm() — use custom modal components
- All DOM manipulation through utility functions in app.js, not inline
- Error states must be shown to the user, never silently swallowed

## Git Convention
- Commit messages: "[type]: description" — e.g., "feat: add priority labels"
- Never commit directly to main — always use feature branches 