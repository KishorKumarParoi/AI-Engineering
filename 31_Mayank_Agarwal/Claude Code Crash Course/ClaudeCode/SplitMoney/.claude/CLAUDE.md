# SplitEasy

Group expense tracker — record who paid what, split costs among friends, settle up with the minimum number of transactions.

Full requirements in [PRD.md](PRD.md) — read it before making any decisions.

---

## Tech Stack

### Backend
- **Framework:** Python FastAPI
- **Port:** 8000
- **Storage:** JSON files in `backend/data/`
  - `groups.json` — all groups and their members
  - `expenses.json` — all expenses across all groups

### Frontend
- **Framework:** React with Vite
- **Styling:** Tailwind CSS
- **Port:** 5173
- **API base:** `http://localhost:8000`
- **State:** `useState` and `useEffect` only — no external state management libraries

---

## Key Commands

```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

---

## Code Standards

### Python
- Type hints on every function parameter and return value
- `black` formatting — applied automatically via hooks on every save
- No bare `except` — always catch a specific exception type

### React
- Functional components only
- Every fetch must handle both a loading state and an error state — never leave either unhandled
- No inline styles — Tailwind classes only

### Currency
- Always display amounts as ₹ with 2 decimal places: `₹1,250.00`
- Store amounts as integers in paise (₹1 = 100 paise) to avoid float precision issues

---

## Data Schemas

See [PRD.md § 4 — Data Model](PRD.md) for full field definitions.

**Quick reference:**

`groups.json`
```json
[
  {
    "id": "uuid",
    "name": "Goa Trip 2026",
    "invite_code": "abc123",
    "created_at": "2026-05-03T10:00:00Z",
    "created_by": "user-uuid",
    "members": [
      { "id": "uuid", "name": "Priya", "user_id": null }
    ]
  }
]
```

`expenses.json`
```json
[
  {
    "id": "uuid",
    "group_id": "uuid",
    "description": "Hotel stay",
    "amount": 450000,
    "paid_by": "member-uuid",
    "date": "2026-05-03",
    "created_at": "2026-05-03T10:00:00Z",
    "splits": [
      { "member_id": "uuid", "amount": 150000 }
    ]
  }
]
```
