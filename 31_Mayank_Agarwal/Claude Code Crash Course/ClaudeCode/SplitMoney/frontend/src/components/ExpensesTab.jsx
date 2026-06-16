import { useState, useEffect } from "react";
import { fmtPaise, fmtDate } from "../utils";
import AddExpenseModal from "./AddExpenseModal";

export default function ExpensesTab({ group, API }) {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [confirmingDeleteId, setConfirmingDeleteId] = useState(null);

  const fetchExpenses = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/groups/${group.id}/expenses`);
      if (!res.ok) throw new Error("Failed to load expenses");
      setExpenses(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, [group.id]);

  const handleDeleteClick = (expId) => {
    if (confirmingDeleteId === expId) {
      performDelete(expId);
    } else {
      setConfirmingDeleteId(expId);
    }
  };

  const performDelete = async (expId) => {
    setDeletingId(expId);
    setConfirmingDeleteId(null);
    try {
      const res = await fetch(`${API}/groups/${group.id}/expenses/${expId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete expense");
      setExpenses((prev) => prev.filter((e) => e.id !== expId));
    } catch (e) {
      setError(e.message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleAdd = async (expenseData) => {
    const res = await fetch(`${API}/groups/${group.id}/expenses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(expenseData),
    });
    if (!res.ok) throw new Error("Failed to add expense");
    const expense = await res.json();
    setExpenses((prev) => [expense, ...prev]);
    setShowModal(false);
  };

  const memberName = (id) =>
    group.members.find((m) => m.id === id)?.name ?? "Unknown";

  const total = expenses.reduce((sum, e) => sum + e.amount, 0);

  return (
    <div className="animate-fadeIn">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-base font-black text-gray-700 uppercase tracking-wider">
          Expenses
        </h2>
        <button
          onClick={() => setShowModal(true)}
          disabled={group.members.length === 0}
          className="bg-emerald-700 text-white text-sm font-bold px-4 py-2 rounded-xl hover:bg-emerald-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
        >
          + Add Expense
        </button>
      </div>

      {group.members.length === 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-amber-700 text-sm font-medium mb-5">
          Add members to this group before recording expenses.
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white rounded-2xl p-5 animate-pulse border border-gray-100"
            >
              <div className="flex justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-100 rounded-lg w-2/5" />
                  <div className="h-3 bg-gray-100 rounded-lg w-1/4" />
                  <div className="h-5 bg-gray-100 rounded-full w-28 mt-3" />
                </div>
                <div className="h-7 bg-gray-100 rounded-lg w-20 shrink-0" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-center">
          <p className="text-red-600 font-semibold text-sm mb-1">
            Something went wrong
          </p>
          <p className="text-red-400 text-xs mb-3">{error}</p>
          <button
            onClick={fetchExpenses}
            className="text-red-600 text-sm font-bold hover:text-red-800 transition-colors"
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && expenses.length === 0 && (
        <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
          <div className="text-4xl mb-3">🧾</div>
          <p className="text-gray-500 font-semibold text-sm mb-1">
            No expenses yet
          </p>
          <p className="text-gray-400 text-xs">
            Tap "Add Expense" to record the first one.
          </p>
        </div>
      )}

      {/* Expense list */}
      {!loading && !error && expenses.length > 0 && (
        <>
          <div className="space-y-3">
            {expenses.map((expense) => {
              const paidByName = memberName(expense.paid_by);
              const splitCount = expense.splits?.length ?? 0;
              const isConfirming = confirmingDeleteId === expense.id;
              const isDeleting = deletingId === expense.id;

              return (
                <div
                  key={expense.id}
                  className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex items-start gap-4 animate-slideUp"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-gray-900 text-sm leading-snug">
                      {expense.description}
                    </p>
                    <p className="text-gray-400 text-xs mt-0.5 font-medium">
                      {fmtDate(expense.date)}
                    </p>
                    <div className="flex items-center gap-2 mt-2.5 flex-wrap">
                      <span className="bg-emerald-100 text-emerald-700 text-xs font-bold px-2.5 py-0.5 rounded-full">
                        {paidByName} paid
                      </span>
                      <span className="text-gray-400 text-xs font-medium">
                        split among {splitCount}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <span className="text-emerald-700 font-black text-lg leading-tight">
                      {fmtPaise(expense.amount)}
                    </span>

                    {isDeleting ? (
                      <span className="text-gray-300 text-xs font-medium">
                        Deleting…
                      </span>
                    ) : isConfirming ? (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setConfirmingDeleteId(null)}
                          className="text-gray-400 text-xs font-semibold hover:text-gray-600 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => performDelete(expense.id)}
                          className="text-red-500 text-xs font-bold hover:text-red-700 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleDeleteClick(expense.id)}
                        className="text-gray-200 hover:text-red-400 transition-colors text-xl leading-none font-light"
                        aria-label="Delete expense"
                      >
                        ×
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Total */}
          <div className="mt-5 bg-emerald-800 text-white rounded-2xl px-5 py-4 flex items-center justify-between shadow-sm">
            <span className="text-emerald-300 text-sm font-semibold">
              Total expenses
            </span>
            <span className="text-2xl font-black">{fmtPaise(total)}</span>
          </div>
        </>
      )}

      {showModal && (
        <AddExpenseModal
          group={group}
          onClose={() => setShowModal(false)}
          onAdd={handleAdd}
        />
      )}
    </div>
  );
}
