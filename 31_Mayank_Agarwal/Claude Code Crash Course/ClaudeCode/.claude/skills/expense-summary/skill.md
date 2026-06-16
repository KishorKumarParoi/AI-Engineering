---
name: expense-summary
description: Shows a summary of all SplitEasy groups and expenses. Use to get a quick overview of all active groups, total spending, and per-member contributions.
trigger: /expense-summary
effort: low
---

Read `backend/data/groups.json` and `backend/data/expenses.json` directly using the Read tool. Do not make any HTTP calls.

Then print a human-readable summary using this exact format:

```
================================================
           SPLITEASY — EXPENSE SUMMARY
================================================

Found <N> group(s)  |  <total expenses across all groups> expense(s) total

------------------------------------------------
GROUP: <Group Name>
------------------------------------------------
Members  : <count>  (<comma-separated member names>)
Expenses : <count>
Total Spent : ₹<total formatted with commas and 2 decimal places>

Per-member breakdown:
  <Member Name>  →  paid ₹<amount>  (<percentage>% of total)
  ...

  Most paid  : <Member Name>  (₹<amount>)
  Least paid : <Member Name>  (₹<amount>)

(repeat block for each group)

------------------------------------------------
OVERALL TOTALS
------------------------------------------------
Total groups   : <N>
Total expenses : <N>
Total spent    : ₹<amount>
================================================
```

## Calculation rules

- All amounts in `expenses.json` are stored in **paise** (integers). Convert to rupees for display by dividing by 100.
- Display all ₹ amounts with 2 decimal places and comma separators, e.g. `₹1,250.00`.
- "Paid by member" is determined by the `paid_by` field on each expense, which is a `member_id`. Look up the member's name from the group's `members` array.
- For each group, total each member's payments: sum all expenses in that group where `paid_by == member.id`.
- If a group has no expenses, show `Total Spent : ₹0.00` and skip the per-member breakdown, printing `  (no expenses recorded)` instead.
- If `groups.json` is empty, print: `No groups found. Create a group first.`
- Percentages: round to 1 decimal place. If total is 0, show `0.0%` for everyone.
- Sort the per-member list from highest paid to lowest paid.

## Example output (with data)

```
================================================
           SPLITEASY — EXPENSE SUMMARY
================================================

Found 2 group(s)  |  5 expense(s) total

------------------------------------------------
GROUP: Goa Trip 2026
------------------------------------------------
Members  : 3  (Priya, Rahul, Sneha)
Expenses : 3
Total Spent : ₹4,500.00

Per-member breakdown:
  Priya   →  paid ₹2,500.00  (55.6% of total)
  Rahul   →  paid ₹1,500.00  (33.3% of total)
  Sneha   →  paid ₹500.00    (11.1% of total)

  Most paid  : Priya  (₹2,500.00)
  Least paid : Sneha  (₹500.00)

------------------------------------------------
GROUP: Office Lunch Pool
------------------------------------------------
Members  : 2  (Arjun, Meera)
Expenses : 2
Total Spent : ₹800.00

Per-member breakdown:
  Meera  →  paid ₹500.00  (62.5% of total)
  Arjun  →  paid ₹300.00  (37.5% of total)

  Most paid  : Meera  (₹500.00)
  Least paid : Arjun  (₹300.00)

------------------------------------------------
OVERALL TOTALS
------------------------------------------------
Total groups   : 2
Total expenses : 5
Total spent    : ₹5,300.00
================================================
```

Output the summary as plain text (no markdown code fences around the output itself). Do not explain what you are doing — just print the summary.
