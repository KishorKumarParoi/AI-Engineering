# Mayank's Job Tracker

A local-first, single-user Kanban board for tracking job applications.

## CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

**Development & Building:**
- `npm run dev` — Start Next.js dev server (http://localhost:3000)
- `npm run build` — Build for production
- `npm start` — Run production server
- `npm run typecheck` — Type-check without emitting code (catch TS errors early)
- `npm run lint` — Run ESLint

**Testing:**
- `npm test` — Run all tests once
- `npm run test:watch` — Run tests in watch mode
- `npm test -- --grep "TestName"` — Run single test by name

**Database:**
- `npx prisma db push` — Apply Prisma schema changes to SQLite (creates `prisma/dev.db` if missing)
- `npx prisma studio` — Open Prisma Studio GUI at http://localhost:5555 to inspect/edit data

## Architecture Overview

This is a **local-first, single-user Kanban board** for tracking job applications. Key design decisions:

### No Cloud Services
- Database is local SQLite file (`prisma/dev.db`), not Supabase or external DB
- No authentication layer (single-user app intended for personal use)
- All state is either in React Context or persisted in local database

### State Management
- **React Context** (`lib/context/job-applications-context.tsx`) owns all application data
- Optimistic updates: UI updates immediately on user action, API call fires in background
- If API fails, UI reverts to previous state
- No Redux or other state library (Context is sufficient for this scope)

### Data Layer
- **Prisma ORM** with SQLite datasource
- Single model: `JobApplication` with fields for company, role, status, dates, notes, contact info, priority
- Status is stored as string (not enum) to allow flexibility: `'wishlist' | 'applied' | 'phone_screen' | 'interviewing' | 'offer' | 'rejected' | 'withdrawn'`
- API routes (`/app/api/applications/`) handle CRUD operations
- All routes return consistent `ApiResponse<T>` format with `{ data, error }`

### UI Architecture
- **Drag-and-Drop**: Uses `@hello-pangea/dnd` (maintained fork of react-beautiful-dnd)
- Cards become semi-transparent while dragging, columns highlight on hover
- Drag end updates status and recalculates priorities within the target column
- **Modals**: Portal-based (ReactDOM.createPortal) with Escape key + backdrop close
- **Form Validation**: Client-side via `validateJobApplicationForm()` before submission
- Columns configured in `lib/constants.ts` — single source of truth for colors and order

## Code Organization

```
app/
  api/
    applications/route.ts      # GET all, POST create
    applications/[id]/route.ts # GET one, PATCH update, DELETE
  layout.tsx                   # Root layout, providers
  page.tsx                     # Main board page (client component)
  error.tsx, not-found.tsx     # Error boundaries

components/
  ui/                          # Reusable atoms: button, input, modal, badge, spinner, etc.
  kanban-board.tsx            # DragDropContext wrapper, handles drag logic
  kanban-column.tsx           # Droppable column with list of cards
  job-card.tsx                # Draggable card item
  job-application-form.tsx    # Form for add/edit modals
  add-application-modal.tsx   # Wrapper for add flow
  edit-application-modal.tsx  # Wrapper for edit/delete flow
  navbar.tsx                  # Top navigation

lib/
  prisma.ts                   # Prisma client singleton
  constants.ts                # KANBAN_COLUMNS, STATUS_BADGE_COLORS
  format-date.ts              # Date formatting utilities
  validations.ts              # Form validation logic
  kanban-helpers.ts           # groupApplicationsByStatus(), moveApplicationBetweenColumns(), etc.
  context/
    job-applications-context.tsx  # React Context provider & hook
    index.ts                      # Barrel export

types/
  database.ts                 # JobApplication types from Prisma
  kanban.ts                   # KanbanColumn, KanbanBoardData
  forms.ts                    # JobApplicationFormData
  api.ts                      # ApiResponse<T>, PaginatedResponse<T>
  index.ts                    # Barrel export

prisma/
  schema.prisma               # Database schema
  dev.db                      # SQLite database (auto-generated)

app/globals.css               # Tailwind directives, global resets
```

## Key Patterns & Conventions

**TypeScript & Types:**
- Strict mode enabled in `tsconfig.json`
- `@/*` alias resolves to project root (defined in tsconfig and vitest config)
- Import types from `types/index.ts` barrel export for consistency

**React Patterns:**
- Functional components with hooks only (no class components)
- Use `React.memo()` on expensive components (KanbanColumn, JobCard)
- Client components marked with `"use client"` at top of file
- Context hook: `const { data, actions } = useJobApplications()`

**API Routes & Error Handling:**
All handlers follow this pattern:
```typescript
try {
  const data = await prisma.jobApplication.findMany(...)
  return NextResponse.json({ data, error: null })
} catch (err) {
  return NextResponse.json({ data: null, error: 'Message' }, { status: 500 })
}
```

**CSS & Styling:**
- Tailwind CSS only (no CSS-in-JS or inline styles)
- Mobile-first approach: base styles for mobile, media queries for larger screens
- Color system defined in `tailwind.config.ts` extends theme with kanban status colors
- Kebab-case class names, but since using Tailwind utility classes, rarely need custom classes

**Naming Conventions:**
- Components: PascalCase (`JobCard.tsx`, `KanbanBoard.tsx`)
- Files: kebab-case for utilities/pages (`job-card.tsx`, `format-date.ts`)
- Functions/variables: camelCase
- CSS classes (custom): kebab-case

**Testing Setup** (not yet implemented, but configured):
- Framework: Vitest with jsdom environment
- Library: React Testing Library
- Test files mirror source: `components/JobCard.tsx` → `components/JobCard.test.tsx`
- Run via `npm test` or `npm run test:watch`

## Database Notes

**Schema Evolution:**
- Database schema is in `prisma/schema.prisma`
- Changes: update schema, run `npx prisma db push` (creates migrations automatically for SQLite)
- No explicit migration files needed for local development
- Always verify with `npx prisma studio` after changes

**Singleton Pattern:**
- `lib/prisma.ts` prevents multiple Prisma client instances during hot-reload
- Global prisma declaration in dev mode reuses instance across module reloads
- Import with: `import prisma from '@/lib/prisma'`

## Debugging Tips

**Type Errors:**
- Run `npm run typecheck` frequently during development
- Most errors caught by TypeScript before runtime

**Runtime Issues:**
- Check browser console (client-side errors)
- Check terminal logs (server-side errors, API responses)
- Open `npx prisma studio` to inspect database state

**Drag-and-Drop Issues:**
- Verify `draggableId` is unique and matches app IDs
- Check `index` prop in Draggable components (must match array position)
- Ensure Droppable and DragDropContext wrap correctly

## Performance Notes

- Components using `React.memo()`: KanbanColumn, JobCard (prevent re-renders on parent updates)
- Date formatting (`getRelativeDays()`) runs on every render — consider memoization if performance becomes issue
- Optimistic updates in Context reduce perceived latency

## Known Limitations & Future Improvements

- No multi-user support (single-user local app)
- No authentication layer
- Status enum is string, not TypeScript enum (allows flexibility but less type safety)
- Phase 9 (comprehensive unit tests) not yet implemented
- No search/filter functionality
- No keyboard navigation or accessibility shortcuts beyond basic ARIA labels



## Working Memory

After completing any significant action, update CHANGELOG.md with a single line:
- Format: `[YYYY-MM-DD] type: brief description`
- Types: feat (feature), fix (bug fix), docs (documentation), refactor, test
- Keep it concise — one line per change. Read CHANGELOG.md at session start to understand project state.