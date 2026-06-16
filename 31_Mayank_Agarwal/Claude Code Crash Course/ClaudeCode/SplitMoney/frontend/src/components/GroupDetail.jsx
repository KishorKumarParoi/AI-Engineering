import { useState, useEffect } from "react";
import ExpensesTab from "./ExpensesTab";
import SettleUpTab from "./SettleUpTab";

export default function GroupDetail({ groupId, onBack, API }) {
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("expenses");
  const [addingMember, setAddingMember] = useState(false);
  const [memberName, setMemberName] = useState("");
  const [memberSaving, setMemberSaving] = useState(false);
  const [memberError, setMemberError] = useState(null);

  const fetchGroup = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/groups/${groupId}`);
      if (!res.ok) throw new Error("Group not found");
      setGroup(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroup();
  }, [groupId]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!memberName.trim()) return;
    setMemberSaving(true);
    setMemberError(null);
    try {
      const res = await fetch(`${API}/groups/${groupId}/members`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: memberName.trim() }),
      });
      if (!res.ok) throw new Error("Failed to add member");
      setMemberName("");
      setAddingMember(false);
      await fetchGroup();
    } catch (e) {
      setMemberError(e.message);
    } finally {
      setMemberSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-emerald-700 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-sm font-medium">Loading group…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center p-5">
        <div className="bg-white rounded-2xl p-8 text-center shadow-sm border border-gray-100 max-w-sm w-full animate-fadeIn">
          <p className="text-red-600 font-semibold mb-1">Couldn't load group</p>
          <p className="text-gray-400 text-sm mb-5">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={onBack}
              className="px-4 py-2 text-sm text-gray-500 font-semibold hover:text-gray-700 transition-colors"
            >
              ← Go back
            </button>
            <button
              onClick={fetchGroup}
              className="bg-emerald-700 text-white px-5 py-2 rounded-xl text-sm font-bold hover:bg-emerald-800 transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-green-50">
      {/* Sticky header */}
      <header className="bg-emerald-800 text-white sticky top-0 z-20 shadow-lg">
        <div className="max-w-4xl mx-auto px-5 pt-4 pb-0">
          {/* Top row */}
          <div className="flex items-center gap-3 mb-3">
            <button
              onClick={onBack}
              className="text-emerald-300 hover:text-white transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-emerald-700 text-lg shrink-0"
              aria-label="Back to groups"
            >
              ←
            </button>
            <h1 className="text-xl font-black truncate flex-1">{group.name}</h1>
          </div>

          {/* Members row */}
          <div className="flex items-center gap-2 flex-wrap pb-3">
            {group.members.map((m) => (
              <span
                key={m.id}
                className="bg-emerald-700 text-emerald-100 text-xs font-semibold px-2.5 py-1 rounded-full"
              >
                {m.name}
              </span>
            ))}

            {addingMember ? (
              <form
                onSubmit={handleAddMember}
                className="flex items-center gap-1.5"
              >
                <input
                  autoFocus
                  value={memberName}
                  onChange={(e) => setMemberName(e.target.value)}
                  placeholder="Name…"
                  className="bg-emerald-900 text-white placeholder-emerald-500 text-xs px-3 py-1 rounded-full border border-emerald-600 focus:outline-none focus:border-emerald-300 w-28 transition-colors"
                />
                <button
                  type="submit"
                  disabled={memberSaving}
                  className="bg-white text-emerald-800 text-xs font-bold px-2.5 py-1 rounded-full hover:bg-emerald-50 transition-colors disabled:opacity-50"
                >
                  {memberSaving ? "…" : "Add"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAddingMember(false);
                    setMemberName("");
                    setMemberError(null);
                  }}
                  className="text-emerald-400 hover:text-emerald-200 text-sm leading-none transition-colors"
                  aria-label="Cancel"
                >
                  ✕
                </button>
              </form>
            ) : (
              <button
                onClick={() => setAddingMember(true)}
                className="text-emerald-300 text-xs border border-emerald-600 px-2.5 py-1 rounded-full hover:bg-emerald-700 hover:text-white transition-colors"
              >
                + Add Member
              </button>
            )}

            {memberError && (
              <span className="text-red-300 text-xs font-medium">
                {memberError}
              </span>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-0">
            {[
              { id: "expenses", label: "Expenses" },
              { id: "settle", label: "Settle Up" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-5 py-3 text-sm font-bold transition-all border-b-2 ${
                  activeTab === tab.id
                    ? "border-white text-white"
                    : "border-transparent text-emerald-400 hover:text-emerald-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Tab content */}
      <main className="max-w-4xl mx-auto px-5 py-7">
        {activeTab === "expenses" && (
          <ExpensesTab group={group} API={API} />
        )}
        {activeTab === "settle" && (
          <SettleUpTab group={group} API={API} />
        )}
      </main>
    </div>
  );
}
