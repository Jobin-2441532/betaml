import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";

import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import SMSInput from "./pages/SMSInput";
import Insights from "./pages/Insights";
import ReviewQueue from "./pages/ReviewQueue";
import Onboarding from "./pages/Onboarding";

// ✅ FIXED: correct import
import { p2pReview, subscriptionReview } from "./api";

const PAGES = {
  "/": { title: "Dashboard", sub: "Overview of your finances" },
  "/transactions": { title: "Transactions", sub: "All your transactions" },
  "/sms": { title: "Add via SMS", sub: "Paste SMS to classify" },
  "/insights": { title: "Monthly Insights", sub: "Spending patterns & trends" },
  "/review": { title: "Review Queue", sub: "Transactions needing attention" },
};

export default function App() {
  const [userId, setUserId] = useState(localStorage.getItem("finance_ai_user_id"));
  const [toast, setToast] = useState(null);
  const [p2pPopup, setP2pPopup] = useState(null);
  const [subPopup, setSubPopup] = useState(null);

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const handleOnboardingComplete = (id) => {
    localStorage.setItem("finance_ai_user_id", id);
    setUserId(String(id));
  };

  const triggerP2PPopup = (txResult) => {
    if (txResult?.needs_p2p_review) setP2pPopup(txResult);
  };

  const triggerSubPopup = (txResult) => {
    if (txResult?.needs_subscription_review) setSubPopup(txResult);
  };

  if (!userId) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />

        <div className="main-content">
          <Routes>
            {Object.entries(PAGES).map(([path, info]) => (
              <Route
                key={path}
                path={path}
                element={
                  <>
                    <TopBar title={info.title} sub={info.sub} />
                    <RouteContent
                      path={path}
                      showToast={showToast}
                      triggerP2PPopup={triggerP2PPopup}
                      triggerSubPopup={triggerSubPopup}
                    />
                  </>
                }
              />
            ))}

            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </div>

      {/* P2P Popup */}
      {p2pPopup && (
        <P2PPopup
          tx={p2pPopup}
          onClose={() => setP2pPopup(null)}
          showToast={showToast}
        />
      )}

      {/* Subscription Popup */}
      {subPopup && (
        <SubscriptionPopup
          tx={subPopup}
          onClose={() => setSubPopup(null)}
          showToast={showToast}
        />
      )}

      {/* Toast */}
      {toast && (
        <div className="toast">
          <span>{toast.type === "success" ? "✅" : "❌"}</span>
          {toast.msg}
        </div>
      )}
    </BrowserRouter>
  );
}

function RouteContent({ path, showToast, triggerP2PPopup, triggerSubPopup }) {
  const props = { showToast, triggerP2PPopup, triggerSubPopup };

  if (path === "/") return <Dashboard {...props} />;
  if (path === "/transactions") return <Transactions {...props} />;
  if (path === "/sms") return <SMSInput {...props} />;
  if (path === "/insights") return <Insights {...props} />;
  if (path === "/review") return <ReviewQueue {...props} />;

  return null;
}

// ── P2P Popup ─────────────────────────────
function P2PPopup({ tx, onClose, showToast }) {
  const OPTIONS = [
    { value: "food", label: "🍕 Food", color: "#fb923c" },
    { value: "travel", label: "🚗 Travel", color: "#38bdf8" },
    { value: "entertainment", label: "🎬 Entertainment", color: "#f472b6" },
    { value: "gift", label: "🎁 Gift", color: "#4ade80" },
    { value: "reimbursement", label: "↩️ Reimbursement", color: "#a78bfa" },
    { value: "others", label: "📦 Others", color: "#6b7280" },
  ];

  const handleSelect = async (context) => {
    try {
      await p2pReview(tx.id, context);
      showToast(`Tagged as ${context}`);
    } catch (e) {
      showToast("Failed to save", "error");
    }
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ width: 360 }}>
        <div style={{ fontSize: 13, color: "#6b7280", marginBottom: 4 }}>
          💬 Quick question
        </div>

        <div className="modal-title" style={{ fontSize: 15 }}>
          ₹{(tx.amount || 0).toLocaleString("en-IN")} to {tx.merchant || tx.vpa}
        </div>

        <div style={{ fontSize: 13, color: "#9ca3af", marginBottom: 20 }}>
          What was this payment for?
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {OPTIONS.map((o) => (
            <button
              key={o.value}
              onClick={() => handleSelect(o.value)}
              style={{
                padding: "10px",
                borderRadius: 8,
                background: "#1a1d27",
                border: "1px solid #2d3354",
                color: o.color,
                fontWeight: 600,
                fontSize: 13,
              }}
            >
              {o.label}
            </button>
          ))}
        </div>

        <button className="btn btn-secondary" style={{ width: "100%", marginTop: 12 }} onClick={onClose}>
          Skip — I'll review later
        </button>
      </div>
    </div>
  );
}

// ── Subscription Popup ─────────────────────
function SubscriptionPopup({ tx, onClose, showToast }) {
  const [type, setType] = useState("personal");
  const [members, setMembers] = useState(2);

  const handleSave = async () => {
    try {
      await subscriptionReview(
        tx.id,
        type,
        type === "group" ? members : 1
      );

      showToast(
        type === "group"
          ? `Split across ${members} people. Your share: ₹${(tx.amount / members).toFixed(0)}`
          : "Marked as personal subscription"
      );
    } catch (e) {
      showToast("Failed to save", "error");
    }

    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ width: 380 }}>
        <div className="modal-title">📺 Subscription Detected</div>

        <div style={{ fontSize: 13, color: "#9ca3af", marginBottom: 20 }}>
          ₹{(tx.amount || 0).toLocaleString("en-IN")} for {tx.merchant}
        </div>

        <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
          {["personal", "group"].map((t) => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={`btn ${type === t ? "btn-primary" : "btn-secondary"}`}
              style={{ flex: 1 }}
            >
              {t === "personal" ? "👤 Just me" : "👥 Shared"}
            </button>
          ))}
        </div>

        {type === "group" && (
          <div className="form-group">
            <label>How many people share this?</label>
            <input
              type="number"
              min={2}
              max={10}
              value={members}
              onChange={(e) => setMembers(parseInt(e.target.value))}
            />
          </div>
        )}

        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSave}>
            Save
          </button>
          <button className="btn btn-secondary" onClick={onClose}>
            Skip
          </button>
        </div>
      </div>
    </div>
  );
}