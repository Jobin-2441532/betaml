import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  LayoutDashboard, List, MessageSquare,
  Users, TrendingUp, AlertCircle,
} from "lucide-react";

const NAV = [
  { path: "/",             icon: LayoutDashboard, label: "Dashboard" },
  { path: "/transactions", icon: List,            label: "Transactions" },
  { path: "/sms",          icon: MessageSquare,   label: "Add via SMS" },
  { path: "/insights",     icon: TrendingUp,      label: "Insights" },
  { path: "/review",       icon: AlertCircle,     label: "Review Queue", badge: true },
];

export default function Sidebar() {
  const location  = useLocation();
  const navigate  = useNavigate();
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    const uid = localStorage.getItem("finance_ai_user_id");
    if (!uid) return;
    axios.get(`http://127.0.0.1:8000/api/review/queue?user_id=${uid}`)
      .then(r => setReviewCount(r.data.pending_count || 0))
      .catch(() => {});

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      axios.get(`http://127.0.0.1:8000/api/review/queue?user_id=${uid}`)
        .then(r => setReviewCount(r.data.pending_count || 0))
        .catch(() => {});
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <h1>💰 FinanceAI</h1>
        <p>Smart Money Tracker</p>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ path, icon: Icon, label, badge }) => (
          <div
            key={path}
            className={`nav-item ${location.pathname === path ? "active" : ""}`}
            onClick={() => navigate(path)}
            style={{ justifyContent: "space-between" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <Icon size={16} />
              {label}
            </div>
            {badge && reviewCount > 0 && (
              <span style={{
                background: "#f87171",
                color: "#fff",
                borderRadius: "10px",
                padding: "1px 7px",
                fontSize: 10,
                fontWeight: 700,
                minWidth: 18,
                textAlign: "center",
              }}>
                {reviewCount}
              </span>
            )}
          </div>
        ))}
      </nav>

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