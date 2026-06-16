import { useState, useEffect } from "react";
import { fmtPaise } from "../utils";
import AddGroupModal from "./AddGroupModal";

export default function GroupsScreen({ onOpenGroup, API }) {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expenseTotals, setExpenseTotals] = useState({});
  const [showModal, setShowModal] = useState(false);

  const fetchGroups = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/groups`);
      if (!res.ok) throw new Error("Failed to load groups");
      const data = await res.json();
      setGroups(data);
      fetchTotals(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchTotals = async (groupsList) => {
    const results = await Promise.all(
      groupsList.map(async (g) => {
        try {
          const res = await fetch(`${API}/groups/${g.id}/expenses`);
          if (!res.ok) return [g.id, 0];
          const expenses = await res.json();
          return [g.id, expenses.reduce((sum, e) => sum + e.amount, 0)];
        } catch {
          return [g.id, 0];
        }
      })
    );
    setExpenseTotals(Object.fromEntries(results));
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  const handleCreate = async (name) => {
    const res = await fetch(`${API}/groups`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error("Failed to create group");
    const group = await res.json();
    setShowModal(false);
    onOpenGroup(group.id);
  };

  return (
    <div className="min-h-screen bg-green-50">
      {/* Header */}
      <header className="bg-emerald-800 text-white">
        <div className="max-w-5xl mx-auto px-5 py-10 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-black text-sm shrink-0">
                ₹
              </div>
              <span className="text-2xl font-black tracking-tight">
                SplitEasy
              </span>
            </div>
            <p className="text-emerald-300 text-sm font-medium">
              No more bill confusion
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="bg-white text-emerald-800 font-bold px-5 py-2.5 rounded-xl text-sm hover:bg-emerald-50 transition-colors shadow-sm shrink-0 mt-1"
          >
            + New Group
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-5 py-8">
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white rounded-2xl p-6 animate-pulse border border-gray-100"
              >
                <div className="h-5 bg-gray-100 rounded-lg w-3/4 mb-2" />
                <div className="h-3.5 bg-gray-100 rounded-lg w-1/3 mb-6" />
                <div className="h-px bg-gray-100 mb-4" />
                <div className="flex justify-between items-end">
                  <div>
                    <div className="h-5 bg-gray-100 rounded-lg w-24 mb-1" />
                    <div className="h-3 bg-gray-100 rounded-lg w-16" />
                  </div>
                  <div className="h-9 bg-gray-100 rounded-xl w-20" />
                </div>
              </div>
            ))}
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center animate-fadeIn">
            <p className="text-red-600 font-semibold mb-1">
              Couldn't load groups
            </p>
            <p className="text-red-400 text-sm mb-4">{error}</p>
            <button
              onClick={fetchGroups}
              className="bg-red-600 text-white px-5 py-2 rounded-xl text-sm font-bold hover:bg-red-700 transition-colors"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && groups.length === 0 && (
          <div className="text-center py-24 animate-fadeIn">
            <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-5 text-3xl">
              🌿
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">
              No groups yet
            </h2>
            <p className="text-gray-400 text-sm mb-7 max-w-xs mx-auto">
              Create your first group to start tracking shared expenses with
              friends.
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="bg-emerald-700 text-white px-7 py-3 rounded-xl font-bold hover:bg-emerald-800 transition-colors shadow-sm"
            >
              Create a Group
            </button>
          </div>
        )}

        {!loading && !error && groups.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-fadeIn">
            {groups.map((g) => (
              <GroupCard
                key={g.id}
                group={g}
                total={
                  g.id in expenseTotals ? expenseTotals[g.id] : null
                }
                onOpen={() => onOpenGroup(g.id)}
              />
            ))}
          </div>
        )}
      </main>

      {showModal && (
        <AddGroupModal onClose={() => setShowModal(false)} onCreate={handleCreate} />
      )}
    </div>
  );
}

function GroupCard({ group, total, onOpen }) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow duration-200 border border-gray-100 flex flex-col animate-slideUp">
      <div className="flex-1">
        <h3 className="text-lg font-black text-gray-900 mb-1 leading-tight">
          {group.name}
        </h3>
        <p className="text-gray-400 text-sm">
          {group.members.length}{" "}
          {group.members.length === 1 ? "person" : "people"}
        </p>
      </div>

      <div className="mt-5 pt-4 border-t border-gray-100 flex items-end justify-between gap-3">
        <div>
          {total === null ? (
            <div className="h-6 w-24 bg-gray-100 rounded-lg animate-pulse mb-1" />
          ) : (
            <p className="text-emerald-700 font-black text-xl leading-tight">
              {fmtPaise(total)}
            </p>
          )}
          <p className="text-gray-400 text-xs mt-0.5">total expenses</p>
        </div>
        <button
          onClick={onOpen}
          className="bg-emerald-700 text-white text-sm font-bold px-4 py-2 rounded-xl hover:bg-emerald-800 transition-colors shrink-0"
        >
          Open →
        </button>
      </div>
    </div>
  );
}
