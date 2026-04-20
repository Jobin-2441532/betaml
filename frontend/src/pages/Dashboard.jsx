import React, { useEffect, useState } from "react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import axios from "axios";
import CategoryBadge from "../components/CategoryBadge";

const PIE_COLORS = [
  "#7c6af7","#f472b6","#fb923c","#4ade80",
  "#38bdf8","#facc15","#f87171","#c084fc",
  "#34d399","#60a5fa","#2dd4bf","#a78bfa",
];

const PM_COLORS = {
  UPI: "#7c6af7", CARD: "#38bdf8", ATM: "#facc15",
  WALLET: "#4ade80", NEFT: "#fb923c", IMPS: "#f472b6",
  NACH: "#c084fc", UNKNOWN: "#6b7280",
};

// Direct API calls — no dependency on api.js
const BASE = "http://127.0.0.1:8000";
const uid = () => parseInt(localStorage.getItem("finance_ai_user_id") || "1");

export default function Dashboard({ showToast }) {
  const now = new Date();
  const [summary, setSummary]           = useState(null);
  const [recentTxs, setRecentTxs]       = useState([]);
  const [reviewCount, setReviewCount]   = useState(0);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [festivalCtx, setFestivalCtx]   = useState(null);
  const [loading, setLoading]           = useState(true);
  const [debugInfo, setDebugInfo]       = useState("");

  useEffect(() => {
    const year  = now.getFullYear();
    const month = now.getMonth() + 1;
    const userId = uid();

    console.log("Dashboard: fetching for user", userId, "month", month, "year", year);
    setDebugInfo(`Fetching: user=${userId} year=${year} month=${month}`);

    const fetchAll = async () => {
      try {
        // Fetch one by one so we can see which one fails
        const sumUrl = `${BASE}/api/insights/monthly-summary?user_id=${userId}&year=${year}&month=${month}`;
        console.log("Fetching summary:", sumUrl);
        const sumRes = await axios.get(sumUrl);
        console.log("Summary data:", sumRes.data);
        setSummary(sumRes.data);
        setDebugInfo(`Income: ₹${sumRes.data.total_income} | Expense: ₹${sumRes.data.total_expense}`);

        const txRes = await axios.get(`${BASE}/api/transactions/`, {
          params: { user_id: userId, limit: 6 }
        });
        console.log("Transactions:", txRes.data);
        setRecentTxs(txRes.data.transactions || []);

        const rvRes = await axios.get(`${BASE}/api/review/queue`, {
          params: { user_id: userId }
        });
        setReviewCount(rvRes.data.pending_count || 0);

        try {
  const pmRes = await axios.get(`${BASE}/api/transactions/payment-method-breakdown`, {
    params: { user_id: userId, days: 30 }
  });
  console.log("Payment methods:", pmRes.data);
  setPaymentMethods(pmRes.data.breakdown || []);
} catch (pmErr) {
  console.log("Payment method breakdown not available:", pmErr.message);
  setPaymentMethods([]);
}

        try {
          const festRes = await axios.get(`${BASE}/api/insights/festival-context`);
          setFestivalCtx(festRes.data);
        } catch (e) {
          console.log("Festival context not available");
        }

      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setDebugInfo(`ERROR: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  if (loading) {
    return (
      <div className="page">
        <div className="loading">⏳ Loading dashboard...</div>
        <div style={{ textAlign: "center", color: "#4a5080", fontSize: 12, marginTop: 8 }}>
          {debugInfo}
        </div>
      </div>
    );
  }

  const pieData = summary?.category_breakdown?.slice(0, 8) || [];

  return (
    <div className="page">

      {/* ── Debug Banner (remove later) ── */}
      <div style={{
        background: "#0e2d15", border: "1px solid #4ade80",
        borderRadius: 8, padding: "10px 16px",
        marginBottom: 20, fontSize: 12,
        color: "#4ade80", fontFamily: "monospace",
      }}>
        🔍 Debug: {debugInfo} | Transactions loaded: {recentTxs.length} | 
        User ID: {uid()} | Month: {now.getMonth() + 1}/{now.getFullYear()}
      </div>

      {/* ── Festival Banner ── */}
      {festivalCtx?.is_festival_period && (
        <div style={{
          background: "linear-gradient(135deg, #1e1b4b, #2d1f0e)",
          border: "1px solid #7c6af7", borderRadius: 12,
          padding: "16px 24px", marginBottom: 24,
          display: "flex", alignItems: "center", gap: 16,
        }}>
          <div style={{ fontSize: 36 }}>🎉</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: "#f1f5f9" }}>
              {festivalCtx.festival?.name} Season!
            </div>
            <div style={{ fontSize: 13, color: "#9ca3af", marginTop: 2 }}>
              {festivalCtx.message}
            </div>
          </div>
        </div>
      )}

      {/* ── KPI Cards ── */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <StatCard
          title="Total Income"
          value={`₹${(summary?.total_income || 0).toLocaleString("en-IN")}`}
          sub="This month"
          color="#4ade80"
        />
        <StatCard
          title="Total Expense"
          value={`₹${(summary?.total_expense || 0).toLocaleString("en-IN")}`}
          sub="This month"
          color="#f87171"
        />
        <StatCard
          title="Net Savings"
          value={`₹${(summary?.net_savings || 0).toLocaleString("en-IN")}`}
          sub={`${summary?.savings_rate_pct || 0}% savings rate`}
          color="#7c6af7"
        />
        <StatCard
          title="Review Queue"
          value={reviewCount}
          sub="Needs attention"
          color="#facc15"
        />
      </div>

      {/* ── Charts Row 1 ── */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="section-header">
            <div className="section-title">Spending by Category</div>
          </div>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="amount"
                    nameKey="category"
                    cx="50%" cy="50%"
                    outerRadius={90} innerRadius={50}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val) => `₹${Number(val).toLocaleString("en-IN")}`}
                    contentStyle={{
                      background: "#1a1d27", border: "1px solid #2d3354",
                      borderRadius: 8, color: "#e2e8f0",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                {pieData.map((d, i) => (
                  <div key={i} style={{
                    display: "flex", alignItems: "center",
                    gap: 4, fontSize: 11, color: "#9ca3af",
                  }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: "50%",
                      background: PIE_COLORS[i % PIE_COLORS.length],
                      display: "inline-block",
                    }} />
                    {d.category}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>No expense data yet</p>
              <p style={{ fontSize: 11, marginTop: 4 }}>
                Add debit transactions via SMS page
              </p>
            </div>
          )}
        </div>

        <div className="card">
          <div className="section-header">
            <div className="section-title">Top Spending Categories</div>
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={pieData.slice(0, 6)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2235" />
                <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="category"
                  tick={{ fill: "#9ca3af", fontSize: 10 }} width={90} />
                <Tooltip
                  formatter={(val) => `₹${Number(val).toLocaleString("en-IN")}`}
                  contentStyle={{
                    background: "#1a1d27", border: "1px solid #2d3354", borderRadius: 8,
                  }}
                />
                <Bar dataKey="amount" fill="#7c6af7" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state"><p>No data yet</p></div>
          )}
        </div>
      </div>

      {/* ── Charts Row 2 ── */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="section-title" style={{ marginBottom: 16 }}>
            💳 Spending by Payment Method
          </div>
          {paymentMethods.length > 0 ? (
            paymentMethods.map((m, i) => {
              const max = paymentMethods[0]?.amount || 1;
              const color = PM_COLORS[m.method] || "#6b7280";
              return (
                <div key={i} style={{ marginBottom: 14 }}>
                  <div style={{
                    display: "flex", justifyContent: "space-between",
                    fontSize: 13, marginBottom: 5,
                  }}>
                    <span style={{ color: "#cbd5e1", fontWeight: 500 }}>{m.method}</span>
                    <span style={{ color, fontWeight: 700 }}>
                      ₹{Number(m.amount).toLocaleString("en-IN")}
                    </span>
                  </div>
                  <div style={{
                    height: 6, background: "#1e2235",
                    borderRadius: 3, overflow: "hidden",
                  }}>
                    <div style={{
                      height: "100%", borderRadius: 3,
                      background: color,
                      width: `${(m.amount / max) * 100}%`,
                      transition: "width 0.6s ease",
                    }} />
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state"><p>No payment data yet</p></div>
          )}
        </div>

        <div className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="section-title">📊 Monthly Health</div>
          {[
            { label: "Income",   value: summary?.total_income  || 0, color: "#4ade80", icon: "💰" },
            { label: "Expenses", value: summary?.total_expense || 0, color: "#f87171", icon: "💸" },
            { label: "Savings",  value: summary?.net_savings   || 0, color: "#7c6af7", icon: "🏦" },
          ].map((item) => (
            <div key={item.label} style={{
              display: "flex", alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 14px", background: "#0f1117", borderRadius: 8,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 18 }}>{item.icon}</span>
                <span style={{ fontSize: 13, color: "#9ca3af" }}>{item.label}</span>
              </div>
              <span style={{ fontWeight: 700, color: item.color, fontSize: 15 }}>
                ₹{Number(item.value).toLocaleString("en-IN")}
              </span>
            </div>
          ))}
          <div>
            <div style={{
              display: "flex", justifyContent: "space-between",
              fontSize: 12, color: "#6b7280", marginBottom: 6,
            }}>
              <span>Savings Rate</span>
              <span style={{ color: "#7c6af7", fontWeight: 700 }}>
                {summary?.savings_rate_pct || 0}%
              </span>
            </div>
            <div style={{ height: 8, background: "#1e2235", borderRadius: 4, overflow: "hidden" }}>
              <div style={{
                height: "100%", borderRadius: 4,
                background: "linear-gradient(90deg, #7c6af7, #a78bfa)",
                width: `${Math.max(0, Math.min(100, summary?.savings_rate_pct || 0))}%`,
                transition: "width 0.6s ease",
              }} />
            </div>
          </div>
        </div>
      </div>

      {/* ── Recent Transactions ── */}
      <div className="card">
        <div className="section-header">
          <div className="section-title">Recent Transactions</div>
          <a href="/transactions" style={{ fontSize: 12, color: "#7c6af7", textDecoration: "none" }}>
            View all →
          </a>
        </div>
        {recentTxs.length === 0 ? (
          <div className="empty-state">
            <p>No transactions yet.</p>
            <p style={{ marginTop: 4, fontSize: 12 }}>
              Go to "Add via SMS" to get started.
            </p>
          </div>
        ) : (
          <div className="table-wrap" style={{ border: "none" }}>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Merchant</th>
                  <th>Category</th>
                  <th>Method</th>
                  <th style={{ textAlign: "right" }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {recentTxs.map((tx) => (
                  <tr key={tx.id}>
                    <td style={{ color: "#6b7280", fontSize: 12 }}>
                      {tx.tx_date
                        ? new Date(tx.tx_date).toLocaleDateString("en-IN", {
                            day: "numeric", month: "short",
                          })
                        : "—"}
                    </td>
                    <td>
                      <div style={{ fontWeight: 500 }}>
                        {tx.merchant || tx.vpa || (
                          <span style={{ color: "#4a5080" }}>Unknown</span>
                        )}
                      </div>
                    </td>
                    <td><CategoryBadge category={tx.category} /></td>
                    <td><span className="tag">{tx.payment_method || "—"}</span></td>
                    <td style={{ textAlign: "right" }}>
                      <span className={tx.type === "credit" ? "credit-amount" : "debit-amount"}>
                        {tx.type === "credit" ? "+" : "−"}
                        ₹{(tx.amount || 0).toLocaleString("en-IN")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, sub, color }) {
  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="card-value" style={{ color }}>{value}</div>
      <div className="card-sub">{sub}</div>
    </div>
  );
}