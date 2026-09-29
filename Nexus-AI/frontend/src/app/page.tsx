"use client";

import { useState, useEffect, useRef, useCallback } from "react";

/* ── Types ─────────────────────────────────────────────────── */
type Tab = "overview" | "agents" | "mlops" | "data" | "security";

interface KPI {
  label: string;
  value: string;
  change: string;
  positive: boolean;
  icon: string;
  accent: string;
}

interface AgentMessage {
  id: number;
  role: "user" | "agent";
  text: string;
  agent?: string;
  timestamp: string;
}

interface ModelHealth {
  rmse: number;
  mae: number;
  r2: number;
  psi: number;
  status: string;
  predictions: number;
  within5min: number;
}

/* ── Mock Data ─────────────────────────────────────────────── */
const MODEL_HEALTH: ModelHealth = {
  rmse: 3.431,
  mae: 2.623,
  r2: 0.9542,
  psi: 0.0123,
  status: "HEALTHY",
  predictions: 145_892,
  within5min: 86.5,
};

const KPIS: KPI[] = [
  { label: "Total Revenue", value: "₹66.2L", change: "+12.3%", positive: true, icon: "💰", accent: "indigo" },
  { label: "Active Orders", value: "10,000", change: "+8.7%", positive: true, icon: "📦", accent: "emerald" },
  { label: "Model R² Score", value: "0.9542", change: "+0.012", positive: true, icon: "🤖", accent: "amber" },
  { label: "Drift PSI", value: "0.0123", change: "−0.002", positive: true, icon: "📊", accent: "rose" },
];

const CITY_DATA = [
  { city: "Mumbai", orders: 2840, revenue: "₹18.9L", fulfillment: 94.2 },
  { city: "Delhi", orders: 2210, revenue: "₹14.5L", fulfillment: 91.8 },
  { city: "Bangalore", orders: 1960, revenue: "₹13.1L", fulfillment: 95.1 },
  { city: "Hyderabad", orders: 1450, revenue: "₹9.2L", fulfillment: 92.5 },
  { city: "Chennai", orders: 1540, revenue: "₹10.5L", fulfillment: 90.3 },
];

const AGENTS = [
  { name: "Data Agent", icon: "📊", status: "active", queries: 1247, latency: "23ms" },
  { name: "Analyst Agent", icon: "💡", status: "active", queries: 856, latency: "45ms" },
  { name: "MLOps Agent", icon: "🤖", status: "active", queries: 432, latency: "12ms" },
  { name: "Security Agent", icon: "🛡️", status: "active", queries: 3891, latency: "5ms" },
  { name: "Voice Agent", icon: "🔔", status: "active", queries: 128, latency: "8ms" },
];

const SECURITY_EVENTS = [
  { time: "09:14:32", type: "PROMPT_INJECTION", action: "BLOCKED", risk: 0.95, query: "ignore previous instructions..." },
  { time: "09:12:01", type: "PII_DETECTED", action: "REDACTED", risk: 0.3, query: "Show data for user@email.com" },
  { time: "09:08:45", type: "SQL_INJECTION", action: "BLOCKED", risk: 0.97, query: "'; DROP TABLE users--" },
  { time: "08:55:12", type: "SAFE", action: "ALLOWED", risk: 0.02, query: "Show top restaurants in Mumbai" },
  { time: "08:41:33", type: "SAFE", action: "ALLOWED", risk: 0.01, query: "Generate executive revenue summary" },
];

/* ── Components ────────────────────────────────────────────── */

function Sidebar({ activeTab, onTabChange }: { activeTab: Tab; onTabChange: (t: Tab) => void }) {
  const navItems: { id: Tab; label: string; icon: string }[] = [
    { id: "overview", label: "Dashboard", icon: "📈" },
    { id: "agents", label: "AI Agents", icon: "🤖" },
    { id: "mlops", label: "MLOps", icon: "⚙️" },
    { id: "data", label: "Data Explorer", icon: "💾" },
    { id: "security", label: "Security", icon: "🛡️" },
  ];

  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-icon">⚡</div>
        <span className="logo-text">Nexus-AI</span>
        <span className="logo-badge">v1.0</span>
      </div>

      <nav className="nav-section">
        <div className="nav-section-label">Platform</div>
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => onTabChange(item.id)}
            style={{ position: "relative", width: "100%", textAlign: "left" }}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div style={{ marginTop: "auto", padding: "12px" }}>
        <div className="glass-card" style={{ padding: "12px", textAlign: "center" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>
            System Status
          </div>
          <span className="status-pill healthy">
            <span className="status-dot healthy" />
            All Systems Operational
          </span>
        </div>
      </div>
    </aside>
  );
}

function KPIGrid() {
  return (
    <div className="kpi-grid">
      {KPIS.map((kpi) => (
        <div key={kpi.label} className={`glass-card kpi-card ${kpi.accent}`}>
          <div className="kpi-header">
            <span className="kpi-label">{kpi.label}</span>
            <span className={`kpi-icon ${kpi.accent}`}>{kpi.icon}</span>
          </div>
          <div className="kpi-value">{kpi.value}</div>
          <span className={`kpi-change ${kpi.positive ? "positive" : "negative"}`}>
            {kpi.change} vs last period
          </span>
        </div>
      ))}
    </div>
  );
}

function ModelHealthPanel() {
  const m = MODEL_HEALTH;
  const gauges = [
    { label: "RMSE", value: m.rmse, max: 15, unit: "min", color: m.rmse < 5 ? "emerald" : "amber" },
    { label: "MAE", value: m.mae, max: 10, unit: "min", color: m.mae < 5 ? "emerald" : "amber" },
    { label: "R² Score", value: m.r2, max: 1, unit: "", color: m.r2 > 0.9 ? "emerald" : "amber" },
    { label: "Drift PSI", value: m.psi, max: 0.5, unit: "", color: m.psi < 0.1 ? "emerald" : "rose" },
  ];

  return (
    <div className="glass-card chart-card">
      <div className="chart-title">
        🧠 Model Health — Delivery ETA
        <span className="status-pill healthy" style={{ marginLeft: "auto" }}>
          <span className="status-dot healthy" />
          {m.status}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {gauges.map((g) => (
          <div key={g.label}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
              <span style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: 600 }}>{g.label}</span>
              <span style={{ fontSize: "14px", fontWeight: 700 }}>
                {g.value}{g.unit}
              </span>
            </div>
            <div className="progress-bar">
              <div
                className={`progress-fill ${g.color}`}
                style={{ width: `${Math.min((g.value / g.max) * 100, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: "20px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "24px", fontWeight: 800, color: "var(--accent-indigo)" }}>
            {m.predictions.toLocaleString()}
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Total Predictions</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "24px", fontWeight: 800, color: "var(--accent-emerald)" }}>
            {m.within5min}%
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Within 5 min</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "24px", fontWeight: 800, color: "var(--accent-cyan)" }}>
            11.5s
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Training Time</div>
        </div>
      </div>
    </div>
  );
}

function CityPerformance() {
  return (
    <div className="glass-card chart-card">
      <div className="chart-title">🏙️ City Performance</div>
      <table className="data-table">
        <thead>
          <tr>
            <th>City</th>
            <th>Orders</th>
            <th>Revenue</th>
            <th>Fulfillment</th>
          </tr>
        </thead>
        <tbody>
          {CITY_DATA.map((city) => (
            <tr key={city.city}>
              <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{city.city}</td>
              <td>{city.orders.toLocaleString()}</td>
              <td style={{ color: "var(--accent-emerald)" }}>{city.revenue}</td>
              <td>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div className="progress-bar" style={{ flex: 1 }}>
                    <div
                      className={`progress-fill ${city.fulfillment > 93 ? "emerald" : "amber"}`}
                      style={{ width: `${city.fulfillment}%` }}
                    />
                  </div>
                  <span style={{ fontSize: "12px", fontWeight: 600, minWidth: "40px" }}>
                    {city.fulfillment}%
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AgentMeshPanel() {
  const [messages, setMessages] = useState<AgentMessage[]>([
    { id: 1, role: "agent", text: "Welcome to the Nexus-AI Agent Mesh. I can query data, analyze trends, check model health, or run security audits. How can I help?", agent: "Orchestrator", timestamp: "09:15:00" },
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [messages, scrollToBottom]);

  const sendMessage = () => {
    if (!input.trim()) return;

    const userMsg: AgentMessage = {
      id: messages.length + 1,
      role: "user",
      text: input,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    // Simulate agent response
    setTimeout(() => {
      const q = input.toLowerCase();
      let agent = "DataAgent";
      let response = "";

      if (q.includes("revenue") || q.includes("kpi") || q.includes("summary")) {
        agent = "AnalystAgent";
        response = "📊 Executive Brief: Total GMV ₹66.2L across 10,000 orders. Top market: Mumbai (₹18.9L). Avg fulfillment: 93.2%. Recommendation: Scale rider incentives during peak dinner hours (7-10 PM).";
      } else if (q.includes("model") || q.includes("drift") || q.includes("health")) {
        agent = "MLOpsAgent";
        response = "✅ Model Status: HEALTHY\n• R²: 0.9542\n• MAE: 2.623 min\n• RMSE: 3.431 min\n• Drift PSI: 0.0123 (well below 0.10 threshold)\n• Action: MAINTAIN — no retraining needed.";
      } else if (q.includes("security") || q.includes("owasp")) {
        agent = "SecurityAgent";
        response = "🛡️ Security Status: Active\n• 12 injection signatures loaded\n• 8 PII types monitored\n• OWASP LLM Top 10 coverage\n• Today: 2 threats blocked, 3 PII redactions";
      } else if (q.includes("alert") || q.includes("notify")) {
        agent = "VoiceAgent";
        response = "🔔 Notification dispatched to 4 channels:\n• Email → team@nexus-ai.dev\n• Slack → #nexus-ai-alerts\n• WhatsApp → On-call\n• n8n → Workflow triggered";
      } else {
        response = `📊 Query routed to DataAgent.\nSQL: SELECT name, rating, cuisine FROM gold_dim_restaurants ORDER BY rating DESC LIMIT 10\nReturned 10 rows in 23ms.`;
      }

      setMessages((prev) => [
        ...prev,
        {
          id: prev.length + 1,
          role: "agent",
          text: response,
          agent,
          timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        },
      ]);
    }, 800);
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">🤖 AI Agent Mesh</h1>
          <p className="page-subtitle">5-Agent Autonomous System — Security-First Architecture</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "20px" }}>
        {AGENTS.map((agent) => (
          <div key={agent.name} className="glass-card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "24px" }}>{agent.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: "14px" }}>{agent.name}</div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  {agent.queries.toLocaleString()} queries • {agent.latency} avg
                </div>
              </div>
              <span className="status-pill healthy">
                <span className="status-dot healthy" />
                Active
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card chat-container">
        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-message ${msg.role}`}>
              {msg.agent && <div className="agent-badge">{msg.agent}</div>}
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "4px" }}>
                {msg.timestamp}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <input
            className="chat-input"
            placeholder="Ask the agent mesh... (e.g., 'Show top restaurants' or 'Check model health')"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button className="btn btn-primary" onClick={sendMessage}>
            Send ↗
          </button>
        </div>
      </div>
    </>
  );
}

function SecurityPanel() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">🛡️ AI Security Center</h1>
          <p className="page-subtitle">OWASP LLM Top 10 — Real-time Threat Detection</p>
        </div>
        <div className="header-actions">
          <span className="status-pill healthy">
            <span className="status-dot healthy" />
            All Clear
          </span>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="glass-card kpi-card indigo">
          <div className="kpi-header">
            <span className="kpi-label">Threats Blocked</span>
            <span className="kpi-icon rose">🚫</span>
          </div>
          <div className="kpi-value">2</div>
          <span className="kpi-change positive">Today</span>
        </div>
        <div className="glass-card kpi-card emerald">
          <div className="kpi-header">
            <span className="kpi-label">PII Redacted</span>
            <span className="kpi-icon amber">🔒</span>
          </div>
          <div className="kpi-value">3</div>
          <span className="kpi-change positive">GDPR Compliant</span>
        </div>
        <div className="glass-card kpi-card amber">
          <div className="kpi-header">
            <span className="kpi-label">Injection Sigs</span>
            <span className="kpi-icon indigo">🔍</span>
          </div>
          <div className="kpi-value">12</div>
          <span className="kpi-change positive">Active patterns</span>
        </div>
        <div className="glass-card kpi-card rose">
          <div className="kpi-header">
            <span className="kpi-label">OWASP Coverage</span>
            <span className="kpi-icon emerald">✅</span>
          </div>
          <div className="kpi-value">8/10</div>
          <span className="kpi-change positive">LLM Top 10</span>
        </div>
      </div>

      <div className="glass-card" style={{ marginTop: "20px" }}>
        <div className="chart-title">🔍 Recent Security Events</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Threat Type</th>
              <th>Action</th>
              <th>Risk</th>
              <th>Query</th>
            </tr>
          </thead>
          <tbody>
            {SECURITY_EVENTS.map((evt, i) => (
              <tr key={i}>
                <td style={{ fontFamily: "monospace", fontSize: "12px" }}>{evt.time}</td>
                <td>
                  <span
                    className={`status-pill ${evt.type === "SAFE" ? "healthy" : evt.type === "PII_DETECTED" ? "warning" : "critical"}`}
                    style={{ fontSize: "11px", padding: "3px 8px" }}
                  >
                    {evt.type}
                  </span>
                </td>
                <td style={{ fontWeight: 600, color: evt.action === "BLOCKED" ? "var(--accent-rose)" : evt.action === "REDACTED" ? "var(--accent-amber)" : "var(--accent-emerald)" }}>
                  {evt.action}
                </td>
                <td>
                  <div className="progress-bar" style={{ width: "60px" }}>
                    <div
                      className={`progress-fill ${evt.risk > 0.8 ? "rose" : evt.risk > 0.2 ? "amber" : "emerald"}`}
                      style={{ width: `${evt.risk * 100}%` }}
                    />
                  </div>
                </td>
                <td style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {evt.query}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function DataExplorer() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">💾 Data Explorer</h1>
          <p className="page-subtitle">Medallion Lakehouse — Bronze → Silver → Gold</p>
        </div>
      </div>

      <div className="kpi-grid">
        {[
          { label: "Bronze (Raw)", value: "5", change: "CSV files", icon: "🥉", accent: "amber" },
          { label: "Silver (Clean)", value: "5", change: "31/32 checks pass", icon: "🥈", accent: "indigo" },
          { label: "Gold (Analytics)", value: "8", change: "Parquet tables", icon: "🥇", accent: "emerald" },
          { label: "Feature Store", value: "8,221", change: "ML samples", icon: "🧪", accent: "rose" },
        ].map((item) => (
          <div key={item.label} className={`glass-card kpi-card ${item.accent}`}>
            <div className="kpi-header">
              <span className="kpi-label">{item.label}</span>
              <span className={`kpi-icon ${item.accent}`}>{item.icon}</span>
            </div>
            <div className="kpi-value">{item.value}</div>
            <span className="kpi-change positive">{item.change}</span>
          </div>
        ))}
      </div>

      <div className="glass-card" style={{ marginTop: "20px" }}>
        <div className="chart-title">📋 Gold Layer Tables</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Table</th>
              <th>Type</th>
              <th>Rows</th>
              <th>Size</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: "dim_restaurants", type: "Dimension", rows: "100", size: "36 KB" },
              { name: "dim_cuisines", type: "Dimension", rows: "15", size: "5 KB" },
              { name: "dim_delivery_partners", type: "Dimension", rows: "200", size: "32 KB" },
              { name: "fact_orders", type: "Fact", rows: "10,000", size: "430 KB" },
              { name: "fact_daily_delivery_performance", type: "Fact", rows: "365", size: "20 KB" },
              { name: "mart_city_revenue", type: "Mart", rows: "10", size: "7 KB" },
              { name: "mart_hourly_demand", type: "Mart", rows: "48", size: "4 KB" },
              { name: "features_delivery_eta_v1", type: "Feature Store", rows: "8,221", size: "314 KB" },
            ].map((t) => (
              <tr key={t.name}>
                <td style={{ fontFamily: "monospace", fontWeight: 600, color: "var(--accent-indigo)" }}>
                  {t.name}
                </td>
                <td>{t.type}</td>
                <td>{t.rows}</td>
                <td>{t.size}</td>
                <td>
                  <span className="status-pill healthy" style={{ fontSize: "11px", padding: "3px 8px" }}>
                    ✓ Active
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

/* ── Main Page ─────────────────────────────────────────────── */
export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  return (
    <div className="layout">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="main-content">
        {activeTab === "overview" && (
          <>
            <div className="page-header">
              <div>
                <h1 className="page-title">Dashboard Overview</h1>
                <p className="page-subtitle">Real-time platform health and business metrics</p>
              </div>
              <div className="header-actions">
                <span className="status-pill healthy">
                  <span className="status-dot healthy" />
                  All Healthy
                </span>
                <button className="btn btn-ghost">Last 24h ▾</button>
              </div>
            </div>

            <KPIGrid />

            <div className="chart-grid">
              <ModelHealthPanel />
              <CityPerformance />
            </div>

            <div className="glass-card">
              <div className="chart-title">🤖 Agent Mesh Status</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "12px" }}>
                {AGENTS.map((a) => (
                  <div key={a.name} style={{ textAlign: "center", padding: "12px" }}>
                    <div style={{ fontSize: "28px", marginBottom: "8px" }}>{a.icon}</div>
                    <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "4px" }}>{a.name}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                      {a.queries.toLocaleString()} queries
                    </div>
                    <span className="status-pill healthy" style={{ fontSize: "10px", padding: "2px 8px", marginTop: "6px", display: "inline-flex" }}>
                      <span className="status-dot healthy" />
                      {a.latency}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {activeTab === "agents" && <AgentMeshPanel />}
        {activeTab === "mlops" && (
          <>
            <div className="page-header">
              <div>
                <h1 className="page-title">⚙️ MLOps Engine</h1>
                <p className="page-subtitle">Model Training, Registry, Drift Detection & Monitoring</p>
              </div>
            </div>
            <KPIGrid />
            <div className="chart-grid">
              <ModelHealthPanel />
              <div className="glass-card chart-card">
                <div className="chart-title">📦 Model Registry</div>
                <table className="data-table">
                  <thead>
                    <tr><th>Property</th><th>Value</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>Model Type</td><td style={{ fontWeight: 600 }}>GradientBoostingRegressor</td></tr>
                    <tr><td>Stage</td><td><span className="status-pill healthy" style={{ fontSize: "11px", padding: "3px 8px" }}>Production</span></td></tr>
                    <tr><td>RMSE</td><td>3.431 min</td></tr>
                    <tr><td>MAE</td><td>2.623 min</td></tr>
                    <tr><td>R² Score</td><td style={{ color: "var(--accent-emerald)", fontWeight: 700 }}>0.9542</td></tr>
                    <tr><td>Drift PSI</td><td style={{ color: "var(--accent-emerald)" }}>0.0123 (Healthy)</td></tr>
                    <tr><td>Within 5 min</td><td>86.5%</td></tr>
                    <tr><td>Within 10 min</td><td>99.4%</td></tr>
                    <tr><td>Prometheus</td><td style={{ fontFamily: "monospace", fontSize: "12px" }}>12 metrics exported</td></tr>
                    <tr><td>Grafana</td><td>9-panel dashboard configured</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {activeTab === "data" && <DataExplorer />}
        {activeTab === "security" && <SecurityPanel />}
      </main>
    </div>
  );
}
