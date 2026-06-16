# Prisma Database Configuration Report

**Generated:** 2026-04-27  
**Report Type:** Database Schema Analysis

---

## Overview

This project uses **Prisma ORM** with **SQLite** as the local database provider. The database is file-based (`prisma/dev.db`), making it ideal for a single-user, local-first application.

---

## Configuration

### Data Source
- **Provider:** SQLite
- **Database File:** `./dev.db` (12 KB)
- **Location:** `prisma/` directory

### Client Generator
- **Provider:** `prisma-client-js`
- Generates TypeScript-safe database client for use in API routes and server components

---

## Database Schema

### Model: JobApplication

The database contains a single model `JobApplication` with 16 fields:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | String | Primary Key, CUID | Auto-generated unique identifier |
| `companyName` | String | Required | Name of the company |
| `roleTitle` | String | Required | Job title/position name |
| `status` | String | Required | Application status (e.g., 'wishlist', 'applied', 'offer') |
| `jobUrl` | String | Optional | URL to job posting |
| `location` | String | Optional | Job location |
| `salaryRange` | String | Optional | Salary information |
| `appliedDate` | String | Optional | Date application was submitted |
| `notes` | String | Optional | User notes about the application |
| `contactName` | String | Optional | Name of contact person at company |
| `contactEmail` | String | Optional | Email of contact person |
| `priority` | Int | Default: 0 | Priority ranking (higher = more important) |
| `createdAt` | DateTime | Auto | Timestamp when record was created |
| `updatedAt` | DateTime | Auto | Timestamp when record was last updated |

---

## Key Design Decisions

1. **String-based Status**: Status is stored as a plain string (not an enum), allowing flexibility for status values without schema migrations.

2. **Optional Fields**: Most fields are optional (`jobUrl`, `location`, `salaryRange`, `appliedDate`, `notes`, `contactName`, `contactEmail`) to support minimal data entry.

3. **Priority System**: Integer-based priority (default 0) allows ranking applications within the Kanban board.

4. **Auto-Generated IDs**: Uses CUID (Collision-resistant IDs) for globally unique, database-friendly identifiers.

5. **Timestamps**: `createdAt` and `updatedAt` automatically track record lifecycle.

---

## Database File

- **Size:** 12 KB
- **Format:** Binary SQLite database file
- **Location:** `prisma/dev.db`
- **Auto-generated:** Yes (created by Prisma on first `db push`)

---

## Development Workflow

**Commands:**
- `npx prisma db push` — Apply schema changes to SQLite database
- `npx prisma studio` — Open GUI to inspect/edit data at http://localhost:5555

**Migrations:**
- SQLite migrations are handled automatically by Prisma
- No explicit migration files needed for local development
- Changes tracked in `prisma_migrations` table within `dev.db`

---

## Usage in Application

- **API Routes:** `/app/api/applications/route.ts` and `/app/api/applications/[id]/route.ts` use Prisma client for CRUD operations
- **Context:** Data is fetched via API and cached in React Context (`useJobApplications`)
- **Client:** All database access is server-side; client receives JSON via API routes

---

## Notes

- This is a **single-user, local-first** setup — no cloud database or authentication
- Database is persisted locally and can be backed up by copying `prisma/dev.db`
- No performance concerns at current scale (single user)
