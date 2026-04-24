import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";
import axios from "axios";
import { getMonthlySummary, getRecurring, getTopMerchants, getUserId } from "../api";
import CategoryBadge from "../components/CategoryBadge";

export default function Insights() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const [summary, setSummary] = useState(null);
  const [recurring, setRecurring] = useState([]);
  const [topMerchants, setTopMerchants] = useState([]);
  const [learningStats, setLearningStats] = useState(null);

  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);

    Promise.all([
      getMonthlySummary(year, month),
      getRecurring(90),
      getTopMerchants(30),
      axios.get(`http://127.0.0.1:8000/api/feedback/learning-stats?user_id=${getUserId()}`)
    ])
      .then(([s, r, t, l]) => {
        setSummary(s.data);
        setRecurring(r.data.recurring_expenses || []);
        setTopMerchants(t.data.top_merchants || []);
        setLearningStats(l.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [year, month]);

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  return (
    <div className="page">

      {/* Month Picker */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
          <div>
            <label>Year</label>
            <select value={year} onChange={e => setYear(Number(e.target.value))}>
              {[2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
            </select>
          </div>

          <div>
            <label>Month</label>
            <select value={month} onChange={e => setMonth(Number(e.target.value))}>
              {MONTHS.map((m, i) => <option key={i+1} value={i+1}>{m}</option>)}
            </select>
          </div>

          <button className="btn btn-primary" onClick={load}>Load</button>
        </div>
      </div>

      {loading ? (
        <div className="loading">⏳ Loading insights...</div>
      ) : (
        <>

          {/* Summary Cards */}
          <div className="grid-4" style={{ marginBottom: 24 }}>
            {[
              { t: "Total Income",  v: summary?.total_income  || 0, c: "#4ade80" },
              { t: "Total Expense", v: summary?.total_expense || 0, c: "#f87171" },
              { t: "Net Savings",   v: summary?.net_savings   || 0, c: "#7c6af7" },
              { t: "Savings Rate",  v: `${summary?.savings_rate_pct || 0}%`, c: "#facc15", raw: true },
            ].map(({ t, v, c, raw }) => (
              <div className="card" key={t}>
                <div className="card-title">{t}</div>
                <div className="card-value" style={{ color: c }}>
                  {raw ? v : `₹${Number(v).toLocaleString("en-IN")}`}
                </div>
              </div>
            ))}
          </div>

          {/* Charts + Merchants */}
          <div className="grid-2" style={{ marginBottom: 24 }}>

            {/* Category Breakdown */}
            <div className="card">
              <div className="section-title">Category Breakdown</div>

              {(summary?.category_breakdown?.length || 0) > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={summary.category_breakdown.slice(0, 8)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e2235" />
                    <XAxis dataKey="category" angle={-30} textAnchor="end" height={50} />
                    <YAxis tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                    <Tooltip formatter={v => `₹${v.toLocaleString("en-IN")}`} />
                    <Bar dataKey="amount" fill="#7c6af7" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div>No data</div>
              )}
            </div>

            {/* Top Merchants */}
            <div className="card">
              <div className="section-title">Top Merchants</div>

              {topMerchants.map((m, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{i + 1}. {m.merchant}</span>
                  <span>₹{(m.total_spend || 0).toLocaleString("en-IN")}</span>
                </div>
              ))}
            </div>

          </div>

          {/* Recurring */}
          <div className="card">
            <div className="section-title">Recurring Expenses</div>

            {recurring.map((r, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between" }}>
                <span>{r.merchant}</span>
                <CategoryBadge category={r.category} />
                <span>{r.frequency}</span>
                <span>₹{(r.amount || 0).toLocaleString("en-IN")}</span>
              </div>
            ))}
          </div>

          {/* ================= AI LEARNING STATS ================= */}
          {learningStats && (
            <div className="card" style={{ marginTop: 24 }}>
              <div className="section-title">🧠 AI Learning Progress</div>

              {/* Stats row */}
              <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
                {[
                  { label: "Merchants Learned", value: learningStats.merchant_mappings_learned, color: "#7c6af7", icon: "🏪" },
                  { label: "Corrections Made", value: learningStats.total_corrections_made, color: "#4ade80", icon: "✏️" },
                  { label: "Need to Retrain", value: learningStats.model_will_improve_after || 0, color: "#facc15", icon: "🎯" },
                ].map(item => (
                  <div key={item.label} style={{
                    flex: 1, minWidth: 120,
                    background: "#0f1117", borderRadius: 10,
                    padding: "12px 16px", textAlign: "center",
                    border: "1px solid #1e2235",
                  }}>
                    <div style={{ fontSize: 20, marginBottom: 4 }}>{item.icon}</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: item.color }}>{item.value}</div>
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>{item.label}</div>
                  </div>
                ))}
              </div>

              {/* Progress bar */}
              <div style={{ marginBottom: 16 }}>
                <div style={{
                  display: "flex", justifyContent: "space-between",
                  fontSize: 12, color: "#6b7280", marginBottom: 6,
                }}>
                  <span>
                    {learningStats.ready_to_retrain
                      ? "✅ Ready to retrain!"
                      : `${learningStats.total_corrections_made}/5 corrections made`}
                  </span>
                  <span style={{ color: "#7c6af7", fontWeight: 600 }}>
                    {Math.min(100, Math.round((learningStats.total_corrections_made / 5) * 100))}%
                  </span>
                </div>
                <div style={{ height: 8, background: "#1e2235", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{
                    width: `${Math.min(100, (learningStats.total_corrections_made / 5) * 100)}%`,
                    height: "100%",
                    background: learningStats.ready_to_retrain
                      ? "linear-gradient(90deg, #4ade80, #7c6af7)"
                      : "linear-gradient(90deg, #7c6af7, #a78bfa)",
                    borderRadius: 4,
                    transition: "width 0.6s ease",
                  }} />
                </div>
              </div>

              {/* Top corrected categories */}
              {learningStats.most_corrected_categories?.length > 0 && (
                <div style={{
                  background: "#0f1117", borderRadius: 8,
                  padding: "12px 14px", marginBottom: 16,
                  border: "1px solid #1e2235",
                }}>
                  <div style={{ fontSize: 11, color: "#4a5080", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.4px" }}>
                    Most Corrected Categories
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {learningStats.most_corrected_categories.map(([cat, count]) => (
                      <span key={cat} style={{
                        background: "#1a1d27", border: "1px solid #2d3354",
                        borderRadius: 20, padding: "3px 10px",
                        fontSize: 12, color: "#a78bfa",
                      }}>
                        {cat} <span style={{ color: "#6b7280" }}>×{count}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 16 }}>
                💡 {learningStats.message}
              </div>

              {/* ── RETRAIN BUTTON — always visible, not gated ── */}
              <RetrainButton
                correctionCount={learningStats.total_corrections_made}
                merchantCount={learningStats.merchant_mappings_learned}
                onSuccess={load}
              />

            </div>
          )}

        </>
      )}
    </div>
  );
}


// ── Retrain Button Component ──────────────────────────────────────────────────
function RetrainButton({ correctionCount, merchantCount, onSuccess }) {
  const [status, setStatus] = React.useState("idle"); // idle | loading | success | error
  const [message, setMessage] = React.useState("");

  const handleRetrain = async () => {
    setStatus("loading");
    setMessage("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/feedback/retrain-model",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );

      const data = await response.json();

      if (data.status === "success") {
        setStatus("success");
        setMessage(
          `Model retrained with ${correctionCount} correction${correctionCount !== 1 ? "s" : ""} ` +
          `and ${merchantCount} merchant pattern${merchantCount !== 1 ? "s" : ""}. ` +
          `New SMS transactions will now use the updated model.`
        );
        if (onSuccess) setTimeout(onSuccess, 1000);
      } else {
        setStatus("error");
        setMessage(data.error || data.message || "Retraining failed. Check terminal.");
      }
    } catch (err) {
      setStatus("error");
      setMessage("Could not reach the backend. Make sure it is running on port 8000.");
    }
  };

  const isLoading = status === "loading";

  return (
    <div>
      <button
        className="btn btn-primary"
        style={{
          width: "100%",
          padding: "12px 20px",
          fontSize: 14,
          fontWeight: 600,
          background: status === "success"
            ? "linear-gradient(135deg, #4ade80, #22c55e)"
            : status === "error"
              ? "linear-gradient(135deg, #f87171, #ef4444)"
              : "linear-gradient(135deg, #7c6af7, #a78bfa)",
          color: status === "success" ? "#000" : "#fff",
          opacity: isLoading ? 0.7 : 1,
          cursor: isLoading ? "not-allowed" : "pointer",
          transition: "all 0.3s ease",
        }}
        disabled={isLoading}
        onClick={handleRetrain}
      >
        {isLoading
          ? "⏳ Retraining AI... please wait"
          : status === "success"
            ? "✅ Retrained Successfully!"
            : status === "error"
              ? "❌ Failed — Click to Retry"
              : `🧠 Retrain AI with My Corrections (${correctionCount} corrections, ${merchantCount} merchants)`}
      </button>

      {/* Info banner below button */}
      {status === "idle" && correctionCount > 0 && (
        <div style={{
          marginTop: 10, padding: "10px 14px",
          background: "#0f1117", borderRadius: 8,
          border: "1px solid #1e2235", fontSize: 12, color: "#6b7280",
        }}>
          🔬 Clicking Retrain will teach the AI using your <strong style={{ color: "#a78bfa" }}>{correctionCount} past correction{correctionCount !== 1 ? "s" : ""}</strong> and <strong style={{ color: "#a78bfa" }}>{merchantCount} merchant pattern{merchantCount !== 1 ? "s" : ""}</strong>. Future transactions from the same merchants will be auto-categorised correctly.
        </div>
      )}

      {status === "idle" && correctionCount === 0 && (
        <div style={{
          marginTop: 10, padding: "10px 14px",
          background: "#0f1117", borderRadius: 8,
          border: "1px solid #1e2235", fontSize: 12, color: "#6b7280",
        }}>
          💡 No corrections yet. Make corrections in <strong style={{ color: "#a78bfa" }}>Transaction History</strong> or <strong style={{ color: "#a78bfa" }}>Review Queue</strong> first, then retrain.
        </div>
      )}

      {/* Result message */}
      {(status === "success" || status === "error") && message && (
        <div style={{
          marginTop: 10, padding: "10px 14px",
          background: status === "success" ? "#0a2e1a" : "#2e0a0a",
          borderRadius: 8,
          border: `1px solid ${status === "success" ? "#4ade80" : "#f87171"}`,
          fontSize: 12,
          color: status === "success" ? "#4ade80" : "#f87171",
        }}>
          {message}
        </div>
      )}
    </div>
  );
}