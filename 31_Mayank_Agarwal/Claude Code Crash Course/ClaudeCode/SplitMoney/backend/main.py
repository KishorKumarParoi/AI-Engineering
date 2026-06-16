import heapq
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATA_DIR = Path(__file__).parent / "data"
GROUPS_FILE = DATA_DIR / "groups.json"
EXPENSES_FILE = DATA_DIR / "expenses.json"


def _read(path: Path) -> list:
    with open(path) as f:
        return json.load(f)


def _write(path: Path, data: list) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


@asynccontextmanager
async def lifespan(_app: FastAPI):  # pyright: ignore[reportUnusedParameter]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not GROUPS_FILE.exists():
        _write(GROUPS_FILE, [])
    if not EXPENSES_FILE.exists():
        _write(EXPENSES_FILE, [])
    yield


app = FastAPI(title="SplitEasy API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class CreateGroupBody(BaseModel):
    name: str


class AddMemberBody(BaseModel):
    name: str


class AddExpenseBody(BaseModel):
    description: str
    amount: float  # ₹, stored internally as paise
    paid_by: str  # member id
    split_among: list[str]  # member ids — equal split
    date: str  # ISO date, e.g. "2026-05-03"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_group(groups: list, group_id: str) -> dict:
    for g in groups:
        if g["id"] == group_id:
            return g
    raise HTTPException(status_code=404, detail=f"Group {group_id!r} not found")


def _get_expense(expenses: list, exp_id: str) -> dict:
    for e in expenses:
        if e["id"] == exp_id:
            return e
    raise HTTPException(status_code=404, detail=f"Expense {exp_id!r} not found")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------


@app.post("/groups", status_code=201)
def create_group(body: CreateGroupBody) -> dict:
    """Create a new group with no members."""
    groups = _read(GROUPS_FILE)
    group: dict = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "members": [],
        "created_at": _now_iso(),
    }
    groups.append(group)
    _write(GROUPS_FILE, groups)
    return group


@app.get("/groups")
def list_groups() -> list:
    """Return all groups."""
    return _read(GROUPS_FILE)


@app.get("/groups/{group_id}")
def get_group(group_id: str) -> dict:
    """Return a single group with its members."""
    groups = _read(GROUPS_FILE)
    return _get_group(groups, group_id)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@app.post("/groups/{group_id}/members", status_code=201)
def add_member(group_id: str, body: AddMemberBody) -> dict:
    """Add a named member to an existing group."""
    groups = _read(GROUPS_FILE)
    group = _get_group(groups, group_id)
    member: dict = {
        "id": str(uuid.uuid4()),
        "name": body.name,
    }
    group["members"].append(member)
    _write(GROUPS_FILE, groups)
    return member


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------


@app.post("/groups/{group_id}/expenses", status_code=201)
def add_expense(group_id: str, body: AddExpenseBody) -> dict:
    """Record an expense, split equally among the listed members."""
    groups = _read(GROUPS_FILE)
    group = _get_group(groups, group_id)

    member_ids = {m["id"] for m in group["members"]}

    if body.paid_by not in member_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Member {body.paid_by!r} does not belong to this group",
        )

    if not body.split_among:
        raise HTTPException(status_code=400, detail="split_among must not be empty")

    for mid in body.split_among:
        if mid not in member_ids:
            raise HTTPException(
                status_code=400, detail=f"Member {mid!r} does not belong to this group"
            )

    # Store amount in paise; distribute remainder across first N members so splits sum exactly
    amount_paise = round(body.amount * 100)
    n = len(body.split_among)
    base = amount_paise // n
    remainder = amount_paise % n

    splits = [
        {"member_id": mid, "amount": base + (1 if i < remainder else 0)}
        for i, mid in enumerate(body.split_among)
    ]

    expenses = _read(EXPENSES_FILE)
    expense: dict = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "description": body.description,
        "amount": amount_paise,
        "paid_by": body.paid_by,
        "date": body.date,
        "created_at": _now_iso(),
        "splits": splits,
    }
    expenses.append(expense)
    _write(EXPENSES_FILE, expenses)
    return expense


@app.get("/groups/{group_id}/expenses")
def list_expenses(group_id: str) -> list:
    """Return all expenses for a group, newest first."""
    groups = _read(GROUPS_FILE)
    _get_group(groups, group_id)  # 404 guard

    expenses = _read(EXPENSES_FILE)
    group_expenses = [e for e in expenses if e["group_id"] == group_id]
    return sorted(group_expenses, key=lambda e: e["date"], reverse=True)


@app.delete("/groups/{group_id}/expenses/{exp_id}")
def delete_expense(group_id: str, exp_id: str) -> dict:
    """Remove an expense from a group."""
    groups = _read(GROUPS_FILE)
    _get_group(groups, group_id)  # 404 guard

    expenses = _read(EXPENSES_FILE)
    expense = _get_expense(expenses, exp_id)

    if expense["group_id"] != group_id:
        raise HTTPException(
            status_code=404,
            detail=f"Expense {exp_id!r} not found in group {group_id!r}",
        )

    _write(EXPENSES_FILE, [e for e in expenses if e["id"] != exp_id])
    return {"deleted": exp_id}


# ---------------------------------------------------------------------------
# Settlement
# ---------------------------------------------------------------------------


@app.get("/groups/{group_id}/settlement")
def get_settlement(group_id: str) -> list:
    """
    Calculate the minimum set of transactions to settle all debts.

    Returns a list of {"from": name, "to": name, "amount": float_in_rupees}.
    """
    groups = _read(GROUPS_FILE)
    group = _get_group(groups, group_id)
    expenses = _read(EXPENSES_FILE)
    group_expenses = [e for e in expenses if e["group_id"] == group_id]

    member_names: dict[str, str] = {m["id"]: m["name"] for m in group["members"]}
    # Net balance in paise: positive → owed money, negative → owes money
    balances: dict[str, int] = {m["id"]: 0 for m in group["members"]}

    for expense in group_expenses:
        paid_by = expense["paid_by"]
        if paid_by in balances:
            balances[paid_by] += expense["amount"]
        for split in expense["splits"]:
            mid = split["member_id"]
            if mid in balances:
                balances[mid] -= split["amount"]

    # Greedy minimisation: repeatedly pair the largest creditor with the largest debtor
    # creditors heap: (-balance_paise, member_id) — max-heap via negation
    # debtors heap:   (-abs_debt_paise, member_id) — max-heap via negation
    creditors: list = []
    debtors: list = []

    for mid, bal in balances.items():
        if bal > 0:
            heapq.heappush(creditors, (-bal, mid))
        elif bal < 0:
            heapq.heappush(
                debtors, (bal, mid)
            )  # most-negative = largest debt → pops first

    transactions: list[dict] = []

    while creditors and debtors:
        cred_neg, cred_id = heapq.heappop(creditors)
        cred_bal = -cred_neg  # positive: amount this person is owed

        debt_val, debt_id = heapq.heappop(debtors)
        debt_bal = -debt_val  # positive: amount this person owes

        settle = min(cred_bal, debt_bal)
        transactions.append(
            {
                "from": member_names.get(debt_id, debt_id),
                "to": member_names.get(cred_id, cred_id),
                "amount": round(settle / 100, 2),
            }
        )

        remaining_cred = cred_bal - settle
        remaining_debt = debt_bal - settle

        if remaining_cred > 0:
            heapq.heappush(creditors, (-remaining_cred, cred_id))
        if remaining_debt > 0:
            heapq.heappush(debtors, (-remaining_debt, debt_id))

    return transactions
