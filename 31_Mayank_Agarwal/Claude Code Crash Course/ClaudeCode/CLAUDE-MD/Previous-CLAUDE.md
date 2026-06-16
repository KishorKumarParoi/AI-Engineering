

<!-- 
HUMAN NOTE:
- Don't remove legacy auth yet
- Migration pending from v1 API
- Claude should NOT know this because it may break refactors
-->

# Project: Job Application Tracker
A Kanban-style web app for tracking job applications.
Stack: Next.js 14, TypeScript, Tailwind CSS, Supabase.
The app runs at localhost:3000 during development.

## Essential Commands
- Start dev server: `npm run dev`
- Run tests: `npm test`
- Type check: `npm run typecheck`
- Build: `npm run build`
- Lint: `npm run lint`

## Conventions
- Components: PascalCase (TaskCard, KanbanColumn)
- Functions/variables: camelCase
- CSS classes: kebab-case
- Files: kebab-case.tsx for components
- API routes: /api/resource-name (REST conventions)

## Structure
- /app — Next.js app directory
- /components — reusable UI components
- /lib — utilities and helpers  
- /types — TypeScript type definitions
- /supabase — database migrations and types
State management: React Context (no Redux)

## Testing
- Framework: Vitest + React Testing Library
- Run a single test: `npm test -- --grep "TestName"`
- Test files mirror source: /components/Button.tsx → /components/Button.test.tsx
- Always run tests after making changes

## Rules — Always Follow These
- Never commit directly to main
- Never hardcode credentials — always use environment variables
- Always handle errors explicitly — no silent failures
- Prefer explicit over clever — readable code beats compact code


## Verification
- After code changes: run `npm run typecheck && npm test`
- After UI changes: take a screenshot and compare to requirements
- After database changes: verify with a test query
- When uncertain: ask rather than assume



<!-- 
DON'T ADD:
- Entire API Documentation
- OUtdated Code snippets
- Task Specific Instructions
- Hooks related stuff/instructions.
-->