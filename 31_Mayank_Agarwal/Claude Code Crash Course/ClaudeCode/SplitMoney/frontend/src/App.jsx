import { useState } from "react";
import GroupsScreen from "./components/GroupsScreen";
import GroupDetail from "./components/GroupDetail";
import "./App.css";

// Dev: http://localhost:8000  |  Production (K8s): /api (nginx proxies to backend)
const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function App() {
  const [selectedGroupId, setSelectedGroupId] = useState(null);

  return (
    <div className="min-h-screen bg-green-50">
      {selectedGroupId ? (
        <GroupDetail
          groupId={selectedGroupId}
          onBack={() => setSelectedGroupId(null)}
          API={API}
        />
      ) : (
        <GroupsScreen onOpenGroup={setSelectedGroupId} API={API} />
      )}
    </div>
  );
}
