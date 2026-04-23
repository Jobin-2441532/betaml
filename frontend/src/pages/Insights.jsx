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

              <div className="grid-3">
                {[
                  { label: "Merchants Learned", value: learningStats.merchant_mappings_learned },
                  { label: "Corrections Made", value: learningStats.total_corrections_made },
                  { label: "Until Next Retrain", value: learningStats.model_will_improve_after },
                ].map(item => (
                  <div key={item.label}>
                    <div>{item.value}</div>
                    <div>{item.label}</div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 12 }}>
                <div>
                  {learningStats.ready_to_retrain
                    ? "✅ Ready to retrain!"
                    : `${learningStats.total_corrections_made}/5 corrections`}
                </div>

                <div style={{ height: 8, background: "#1e2235" }}>
                  <div style={{
                    width: `${Math.min(100, (learningStats.total_corrections_made / 5) * 100)}%`,
                    height: "100%",
                    background: "#7c6af7"
                  }} />
                </div>
              </div>

              <div style={{ marginTop: 12 }}>
                💡 {learningStats.message}
              </div>

              {/* ✅ FIXED RETRAIN BUTTON */}
              {learningStats.ready_to_retrain && (
                <button
                  className="btn btn-primary"
                  style={{ marginBottom: 16 }}
                  onClick={async (e) => {
                    e.preventDefault();
                    const btn = e.target;
                    btn.disabled = true;
                    btn.textContent = "⏳ Retraining... please wait";

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
                        btn.textContent = "✅ Retrained Successfully!";
                        btn.style.background = "#4ade80";
                        btn.style.color = "#000";

                        alert(
                          "✅ Model retrained successfully!\n\n" +
                          "The AI will now classify transactions better.\n\n" +
                          "Tip: New SMS transactions will use the updated model."
                        );
                      } else {
                        btn.textContent = "❌ Failed - Check Terminal";
                        btn.style.background = "#f87171";

                        alert(
                          "❌ Retraining failed.\n\n" +
                          "Error: " + (data.error || data.message || "Unknown") +
                          "\n\nTry running manually:\npython scripts/train_model.py"
                        );
                      }
                    } catch (err) {
                      btn.textContent = "❌ Connection Error";
                      btn.style.background = "#f87171";

                      alert(
                        "❌ Could not reach the backend.\n\n" +
                        "Make sure backend is running on port 8000.\n" +
                        "Error: " + err.message
                      );
                    } finally {
                      setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = "🧠 Retrain AI with My Corrections";
                        btn.style.background = "";
                        btn.style.color = "";
                      }, 3000);
                    }
                  }}
                >
                  🧠 Retrain AI with My Corrections
                </button>
              )}

            </div>
          )}

        </>
      )}
    </div>
  );
}