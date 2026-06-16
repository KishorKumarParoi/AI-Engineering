import { useState, useEffect, useCallback } from "react";
import { fmtRupees } from "../utils";

export default function SettleUpTab({ group, API }) {
  const [settlements, setSettlements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSettlements = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/groups/${group.id}/settlement`);
      if (!res.ok) throw new Error("Failed to calculate settlement");
      setSettlements(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [group.id, API]);

  useEffect(() => {
    fetchSettlements();
  }, [fetchSettlements]);

  return (
    <div className="animate-fadeIn">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-base font-black text-gray-700 uppercase tracking-wider">
          Settle Up
        </h2>
        <button
          onClick={fetchSettlements}
          disabled={loading}
          className="text-emerald-600 text-sm font-bold hover:text-emerald-800 transition-colors disabled:opacity-40 flex items-center gap-1.5"
        >
          <span className={loading ? "animate-spin inline-block" : ""}>↻</span>
          Recalculate
        </button>
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="bg-white rounded-2xl p-6 animate-pulse border border-gray-100"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 flex-1">
                  <div className="h-4 bg-gray-100 rounded-lg w-24" />
                  <div className="h-px bg-gray-100 w-12" />
                  <div className="h-4 bg-gray-100 rounded-lg w-24" />
                </div>
                <div className="h-6 bg-gray-100 rounded-lg w-20 shrink-0" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
          <p className="text-red-600 font-semibold text-sm mb-1">
            Couldn't calculate settlement
          </p>
          <p className="text-red-400 text-xs mb-3">{error}</p>
          <button
            onClick={fetchSettlements}
            className="text-red-600 text-sm font-bold hover:text-red-800 transition-colors"
          >
            Try again
          </button>
        </div>
      )}

      {/* All settled up */}
      {!loading && !error && settlements.length === 0 && (
        <div className="bg-white rounded-2xl p-12 text-center border border-emerald-100 shadow-sm animate-fadeIn">
          <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4 text-3xl">
            ✓
          </div>
          <h3 className="text-xl font-black text-emerald-700 mb-1">
            All settled up!
          </h3>
          <p className="text-gray-400 text-sm font-medium">
            Everyone's even — no payments needed.
          </p>
        </div>
      )}

      {/* Settlement list */}
      {!loading && !error && settlements.length > 0 && (
        <div className="space-y-3 animate-slideUp">
          {settlements.map((s, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl px-6 py-5 shadow-sm border border-gray-100"
            >
              <div className="flex items-center gap-3">
                {/* From */}
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-0.5">
                    From
                  </p>
                  <p className="font-black text-gray-900 text-base truncate">
                    {s.from}
                  </p>
                </div>

                {/* Arrow */}
                <div className="flex flex-col items-center shrink-0 px-2">
                  <div className="flex items-center gap-1 text-emerald-500">
                    <div className="w-5 h-px bg-emerald-300" />
                    <div className="w-5 h-px bg-emerald-400" />
                    <span className="text-emerald-600 text-lg leading-none">
                      →
                    </span>
                  </div>
                  <span className="text-emerald-500 text-xs font-semibold mt-0.5">
                    pays
                  </span>
                </div>

                {/* To */}
                <div className="flex-1 min-w-0 text-right">
                  <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-0.5">
                    To
                  </p>
                  <p className="font-black text-gray-900 text-base truncate">
                    {s.to}
                  </p>
                </div>
              </div>

              {/* Amount */}
              <div className="mt-4 pt-4 border-t border-gray-100 flex justify-center">
                <span className="text-emerald-700 font-black text-2xl">
                  {fmtRupees(s.amount)}
                </span>
              </div>
            </div>
          ))}

          <p className="text-center text-gray-400 text-xs font-medium mt-4">
            Minimum {settlements.length}{" "}
            {settlements.length === 1 ? "transaction" : "transactions"} to
            clear all debts
          </p>
        </div>
      )}
    </div>
  );
}
