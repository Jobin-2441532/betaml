import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, List, MessageSquare,
  Users, TrendingUp, AlertCircle,
} from "lucide-react";

const NAV = [
  { path: "/",             icon: LayoutDashboard, label: "Dashboard" },
  { path: "/transactions", icon: List,            label: "Transactions" },
  { path: "/sms",          icon: MessageSquare,   label: "Add via SMS" },
  { path: "/splits",       icon: Users,           label: "Split Tracker" },
  { path: "/insights",     icon: TrendingUp,      label: "Insights" },
  { path: "/review",       icon: AlertCircle,     label: "Review Queue" },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <h1>💰 FinanceAI</h1>
        <p>Smart Money Tracker</p>
      </div>
      <nav className="sidebar-nav">
        {NAV.map(({ path, icon: Icon, label }) => (
          <div
            key={path}
            className={`nav-item ${location.pathname === path ? "active" : ""}`}
            onClick={() => navigate(path)}
          >
            <Icon size={16} />
            {label}
          </div>
        ))}
      </nav>

      {/* Existing footer */}
      <div style={{ padding: "16px 24px", borderTop: "1px solid #1e2235" }}>
        <div style={{ fontSize: 11, color: "#4a5080" }}>FinanceAI v1.0</div>
        <div style={{ fontSize: 11, color: "#3b4162", marginTop: 2 }}>
          Backend: localhost:8000
        </div>
      </div>

      {/* Added Logout Section */}
      <div style={{ padding: "16px 12px", borderTop: "1px solid #1e2235" }}>
        <div style={{ fontSize: 11, color: "#4a5080", marginBottom: 8 }}>
          FinanceAI v1.0 · localhost:8000
        </div>
        <button
          onClick={() => {
            if (confirm("Log out? Your data will be saved.")) {
              localStorage.removeItem("finance_ai_user_id");
              window.location.href = "/";
            }
          }}
          style={{
            width: "100%",
            background: "transparent",
            border: "1px solid #2d3354",
            borderRadius: 8,
            color: "#6b7280",
            fontSize: 12,
            padding: "7px",
            cursor: "pointer",
            fontFamily: "Inter, sans-serif",
          }}
        >
          🚪 Log Out
        </button>
      </div>
    </div>
  );
}