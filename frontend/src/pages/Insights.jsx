import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line, Legend,
} from "recharts";
import { getMonthlySummary, getRecurring, getTopMerchants } from "../api";
import CategoryBadge from "../components/CategoryBadge";

export default function Insights() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [summary, setSummary] = useState(null);
  const [recurring, setRecurring] = useState([]);
  const [topMerchants, setTopMerchants] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      getMonthlySummary(year, month),
      getRecurring(90),
      getTopMerchants(30),
    ]).then(([s, r, t]) => {
      setSummary(s.data);
      setRecurring(r.data.recurring_expenses || []);
      setTopMerchants(t.data.top_merchants || []);
    }).catch(() => {}).finally(() => setLoading(false));
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
            <select value={year} onChange={e => setYear(Number(e.target.value))}
                    style={{ width: 100 }}>
              {[2023, 2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
            </select>
          </div>
          <div>
            <label>Month</label>
            <select value={month} onChange={e => setMonth(Number(e.target.value))}
                    style={{ width: 130 }}>
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

          <div className="grid-2" style={{ marginBottom: 24 }}>
            {/* Category Breakdown */}
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>
                Category Breakdown
              </div>
              {(summary?.category_breakdown?.length || 0) > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={summary.category_breakdown.slice(0, 8)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e2235" />
                    <XAxis dataKey="category"
                           tick={{ fill: "#6b7280", fontSize: 9 }}
                           angle={-30} textAnchor="end" height={50} />
                    <YAxis tick={{ fill: "#6b7280", fontSize: 11 }}
                           tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      formatter={v => `₹${v.toLocaleString("en-IN")}`}
                      contentStyle={{ background: "#1a1d27", border: "1px solid #2d3354", borderRadius: 8 }}
                    />
                    <Bar dataKey="amount" fill="#7c6af7" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state"><p>No data for this month</p></div>
              )}
            </div>

            {/* Top Merchants */}
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>
                Top Merchants (Last 30 Days)
              </div>
              {topMerchants.length > 0 ? (
                <div>
                  {topMerchants.map((m, i) => (
                    <div key={i} style={{
                      display: "flex", justifyContent: "space-between",
                      alignItems: "center", padding: "10px 0",
                      borderBottom: "1px solid #1e2235",
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{
                          width: 24, height: 24, borderRadius: "50%",
                          background: "#1e2235", display: "flex",
                          alignItems: "center", justifyContent: "center",
                          fontSize: 11, color: "#7c6af7", fontWeight: 700,
                        }}>{i + 1}</span>
                        <span style={{ fontSize: 13 }}>{m.merchant}</span>
                      </div>
                      <span className="debit-amount">
                        ₹{(m.total_spend || 0).toLocaleString("en-IN")}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state"><p>No data yet</p></div>
              )}
            </div>
          </div>

          {/* Recurring Expenses */}
          <div className="card">
            <div className="section-header">
              <div className="section-title">Recurring Expenses</div>
              <span style={{ fontSize: 12, color: "#6b7280" }}>
                {recurring.length} detected
              </span>
            </div>
            {recurring.length > 0 ? (
              <div className="table-wrap" style={{ border: "none" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Merchant</th>
                      <th>Category</th>
                      <th>Frequency</th>
                      <th>Occurrences</th>
                      <th>Next Expected</th>
                      <th>Confidence</th>
                      <th style={{ textAlign: "right" }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recurring.map((r, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 500 }}>{r.merchant}</td>
                        <td><CategoryBadge category={r.category} /></td>
                        <td>
                          <span className="badge" style={{ background: "#0e2d1a", color: "#4ade80" }}>
                            {r.frequency}
                          </span>
                        </td>
                        <td style={{ color: "#9ca3af" }}>{r.occurrences}x</td>
                        <td style={{ color: "#6b7280", fontSize: 12 }}>
                          {r.next_expected
                            ? new Date(r.next_expected).toLocaleDateString("en-IN")
                            : "—"}
                        </td>
                        <td>
                          <span style={{
                            color: r.confidence >= 0.85 ? "#4ade80" : "#facc15",
                            fontWeight: 600, fontSize: 12,
                          }}>
                            {Math.round(r.confidence * 100)}%
                          </span>
                        </td>
                        <td style={{ textAlign: "right" }}>
                          <span className="debit-amount">
                            ₹{(r.amount || 0).toLocaleString("en-IN")}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>No recurring expenses detected yet. Add more transactions to detect patterns.</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}