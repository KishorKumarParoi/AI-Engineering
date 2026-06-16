# SplitEasy — Product Requirements Document

**Version:** 1.0  
**Date:** 2026-05-03  
**Status:** Draft

---

## 1. What the App Does

SplitEasy is a web app that helps groups of people track shared expenses and settle up fairly.

When friends go on a trip or colleagues share a meal, one person often ends up paying for everyone. Over multiple such payments across the group, it becomes difficult to track who owes whom. SplitEasy solves this by letting users record every payment, split it among the relevant people, and then automatically calculate the minimum number of transactions needed for everyone to settle up.

**The core loop:**
1. Create a group (e.g. "Goa Trip 2026")
2. Add the members of that group
3. Record each expense — who paid, how much, what for, and who it's split between
4. View a settlement summary showing exactly who needs to pay whom and how much

---

## 2. Core Features

### Feature 1 — Group Management
Users can create named groups. Each group is a self-contained space for tracking a shared experience (a trip, a dinner, a flatshare, etc.). Groups can be created, renamed, and deleted. Each group has a unique shareable link so others can join without needing an account.

### Feature 2 — Member Management
Within a group, users can add members by name. Members do not need to have accounts — they can be added as names only (e.g. "Priya", "Rohan"). A real user who visits the group link can claim their name. Members can be removed as long as they have no recorded expenses.

### Feature 3 — Expense Recording
Users can add an expense to a group by specifying:
- A description (e.g. "Hotel stay", "Petrol", "Dinner at Toit")
- The amount in ₹
- Who paid (one person from the group)
- Which members the expense is split among (defaults to all members, but can be a subset)
- The date of the expense

Splits are equal by default. Custom split amounts per person are supported (as long as they add up to the total). Expenses can be edited or deleted.

### Feature 4 — Settlement Calculation
The app calculates, at any moment, the minimum set of transactions to settle all debts within the group. It shows a clear list like:

> Rohan pays Priya ₹850  
> Karan pays Ananya ₹1,200

The algorithm minimises the number of transactions (not just a naive pairwise calculation). The settlement screen updates in real time as expenses are added or removed.

### Feature 5 — Expense Summary & History
Users can view a full list of all expenses in a group, sorted by date (newest first). Each expense shows who paid, the amount, the description, the split breakdown, and when it was added. The group also shows a running balance per member — how much each person has paid vs. how much they owe overall.

---

## 3. Screens

### Screen 1 — Home / Groups List
- Shows all groups the current user is a member of
- Each group card shows: group name, number of members, number of expenses, and the user's current net balance in that group (e.g. "You are owed ₹1,200" or "You owe ₹450")
- A prominent "Create New Group" button at the top
- Empty state: friendly message prompting the user to create their first group

### Screen 2 — Create Group
- Single-field form: Group Name (required)
- "Add members" section: type a name, press enter to add. Shows added names as removable chips.
- "Create Group" button — creates the group and redirects to the Group Detail screen

### Screen 3 — Group Detail
- Header: group name, member count, and a "Share Group" button (copies invite link to clipboard)
- **Balances tab (default):** Shows each member's net balance — positive means they are owed money, negative means they owe money
- **Expenses tab:** Chronological list of all expenses. Each row shows description, amount, paid-by, and date. Tapping an expense expands it to show the per-person split.
- **Settle Up tab:** Shows the minimum list of transactions to zero out all balances. Each item is a clear "X pays Y ₹Z" line. A "Mark as Settled" button on each item records that the payment was made (removes it from the list without adding it as an expense).
- Floating "Add Expense" button always visible

### Screen 4 — Add / Edit Expense
- Fields:
  - Description (text, required)
  - Amount in ₹ (number, required)
  - Paid by (dropdown of group members, required)
  - Date (date picker, defaults to today)
  - Split among (multi-select of group members, defaults to all)
  - Split type toggle: "Equal" (default) or "Custom"
  - If Custom: an input field per selected member showing their share (must sum to total)
- "Save Expense" button — validates and saves, returns to Group Detail
- On edit: pre-fills all fields, shows "Delete Expense" option at the bottom

### Screen 5 — Member Detail (within a group)
- Shows the selected member's name
- Their total paid across all group expenses
- Their total share (what they owe across all group expenses)
- Their net balance
- A filtered list of expenses they are involved in

---

## 4. Data Model

### Group
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | String | Display name (e.g. "Goa Trip 2026") |
| invite_code | String | Unique short code for the shareable link |
| created_at | Timestamp | |
| created_by | User ID | The user who created the group |

### Member
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| group_id | UUID | The group this member belongs to |
| name | String | Display name |
| user_id | UUID or null | Linked to a real user account, if claimed |
| added_at | Timestamp | |

### Expense
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| group_id | UUID | The group this expense belongs to |
| description | String | What the expense was for |
| amount | Integer | Amount in paise (₹1 = 100 paise) — avoids float precision issues |
| paid_by | Member ID | Who paid |
| date | Date | Date of the expense |
| created_at | Timestamp | |
| created_by | User ID | Who entered it into the app |

### ExpenseSplit
One row per member per expense. Defines how the expense is divided.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| expense_id | UUID | The expense |
| member_id | UUID | The member who owes this share |
| amount | Integer | Share amount in paise |

### Settlement
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| group_id | UUID | The group |
| from_member | Member ID | Who is paying |
| to_member | Member ID | Who is receiving |
| amount | Integer | Amount in paise |
| settled_at | Timestamp | When "Mark as Settled" was pressed |
| created_by | User ID | |

### User
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | String | Unique |
| display_name | String | |
| created_at | Timestamp | |

---

## 5. What the API Does (Non-Technical)

These are the operations the app's backend must support:

### Groups
- **Create a group** — takes a name, returns the new group with its shareable invite link
- **Get a group** — returns the group details, its members, and computed balances per member
- **Update a group name** — renames the group
- **Delete a group** — removes the group and all its data (requires confirmation)
- **Join a group via invite code** — adds the requesting user as a member using the invite link

### Members
- **Add a member** — adds a named person to a group (no account required)
- **Remove a member** — removes a member if they have no expenses attached
- **Claim a member** — links a real user account to an existing named member slot

### Expenses
- **Add an expense** — records who paid, how much, what for, and how it's split
- **Get all expenses for a group** — returns the full list, sorted by date
- **Get a single expense** — returns full detail including per-person split
- **Edit an expense** — updates any field; recalculates splits if amounts change
- **Delete an expense** — removes the expense and its splits

### Settlements
- **Get settlement plan** — calculates and returns the minimum set of transactions to settle the group (this is computed, not stored, until marked settled)
- **Mark a settlement as paid** — records that a specific payment was made, removes it from the active settlement list

### Users
- **Sign up** — creates an account with email and password
- **Log in** — returns an auth token
- **Get current user** — returns the logged-in user's profile

---

## 6. Definition of Done

The app is complete when all of the following are true:

### Functional Completeness
- [ ] A user can sign up, log in, and log out
- [ ] A user can create a group and add named members
- [ ] A user can share a group invite link; others can join via the link
- [ ] A user can add an expense with equal or custom splits
- [ ] A user can edit and delete expenses
- [ ] Balances update correctly after every add/edit/delete
- [ ] The settlement screen shows the correct minimum-transaction plan
- [ ] A user can mark individual settlements as paid
- [ ] All amounts display in ₹ (e.g. ₹1,250.00)

### Edge Cases Handled
- [ ] Adding an expense for a subset of members (not the whole group) calculates correctly
- [ ] Deleting an expense recalculates all balances immediately
- [ ] If all balances are zero, the settlement screen shows "All settled up! 🎉"
- [ ] A member with no expenses can be removed; one with expenses cannot
- [ ] Trying to delete a group prompts a confirmation and warns that all data will be lost

### Quality
- [ ] Works on mobile (Chrome, Safari) and desktop (Chrome, Firefox, Safari)
- [ ] No page takes more than 2 seconds to load on a standard connection
- [ ] All forms show clear validation errors (e.g. "Amount must be greater than ₹0")
- [ ] No broken states — refreshing the page never loses data
- [ ] An unauthenticated user who visits a group invite link is prompted to log in first, then redirected to the group

---

## 7. Out of Scope (v1)

The following are explicitly not part of v1 and should not be built:

- In-app payments or UPI integration
- Push notifications or email reminders
- Currency conversion (₹ only)
- Recurring expenses
- Photos/receipts attached to expenses
- Group chat or comments on expenses
- Percentage-based splits (equal and custom fixed amounts only)
