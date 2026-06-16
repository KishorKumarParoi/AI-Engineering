import { useState } from "react";
import { today } from "../utils";

export default function AddExpenseModal({ group, onClose, onAdd }) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [paidBy, setPaidBy] = useState(group.members[0]?.id ?? "");
  const [splitAmong, setSplitAmong] = useState(group.members.map((m) => m.id));
  const [date, setDate] = useState(today());
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const errs = {};
    if (!description.trim()) errs.description = "Description is required";
    const amt = parseFloat(amount);
    if (!amount || isNaN(amt) || amt <= 0)
      errs.amount = "Amount must be greater than ₹0";
    if (!paidBy) errs.paidBy = "Select who paid";
    if (splitAmong.length === 0)
      errs.splitAmong = "Select at least one person to split with";
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setSaving(true);
    try {
      await onAdd({
        description: description.trim(),
        amount: parseFloat(amount),
        paid_by: paidBy,
        split_among: splitAmong,
        date,
      });
    } catch (e) {
      setErrors({ submit: e.message });
    } finally {
      setSaving(false);
    }
  };

  const toggleMember = (id) => {
    setSplitAmong((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const inputClass = (field) =>
    `w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-shadow ${
      errors[field]
        ? "border-red-300 bg-red-50 focus:ring-red-400"
        : "border-gray-200 bg-white"
    }`;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl max-h-[92vh] overflow-y-auto animate-slideUp">
        <div className="p-6">
          {/* Modal header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-black text-gray-900">Add Expense</h2>
            <button
              onClick={onClose}
              className="text-gray-300 hover:text-gray-500 text-2xl leading-none transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100"
              aria-label="Close"
            >
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Description */}
            <div>
              <label className="block text-xs font-black text-gray-500 uppercase tracking-widest mb-1.5">
                Description
              </label>
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Hotel stay, Dinner, Petrol"
                className={inputClass("description")}
              />
              {errors.description && (
                <p className="text-red-500 text-xs mt-1 font-medium">
                  {errors.description}
                </p>
              )}
            </div>

            {/* Amount */}
            <div>
              <label className="block text-xs font-black text-gray-500 uppercase tracking-widest mb-1.5">
                Amount
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 font-bold text-sm pointer-events-none">
                  ₹
                </span>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className={`${inputClass("amount")} pl-7`}
                />
              </div>
              {errors.amount && (
                <p className="text-red-500 text-xs mt-1 font-medium">
                  {errors.amount}
                </p>
              )}
            </div>

            {/* Paid by */}
            <div>
              <label className="block text-xs font-black text-gray-500 uppercase tracking-widest mb-1.5">
                Paid by
              </label>
              <select
                value={paidBy}
                onChange={(e) => setPaidBy(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white transition-shadow"
              >
                {group.members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Date */}
            <div>
              <label className="block text-xs font-black text-gray-500 uppercase tracking-widest mb-1.5">
                Date
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-shadow"
              />
            </div>

            {/* Split among */}
            <div>
              <label className="block text-xs font-black text-gray-500 uppercase tracking-widest mb-1.5">
                Split among
              </label>
              {errors.splitAmong && (
                <p className="text-red-500 text-xs mb-2 font-medium">
                  {errors.splitAmong}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                {group.members.map((m) => {
                  const selected = splitAmong.includes(m.id);
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => toggleMember(m.id)}
                      className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-colors ${
                        selected
                          ? "bg-emerald-700 text-white"
                          : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                      }`}
                    >
                      {selected ? "✓ " : ""}
                      {m.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Submit error */}
            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-2.5">
                <p className="text-red-600 text-sm font-medium">
                  {errors.submit}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-sm font-bold text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-4 py-3 rounded-xl bg-emerald-700 text-white text-sm font-bold hover:bg-emerald-800 transition-colors disabled:opacity-50 shadow-sm"
              >
                {saving ? "Saving…" : "Save Expense"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
