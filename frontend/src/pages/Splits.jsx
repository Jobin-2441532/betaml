import React, { useEffect, useState } from "react";
import { detectSplits } from "../api";
import { Users, CheckCircle, Clock, AlertCircle } from "lucide-react";

const STATUS_STYLE = {
  settled: { bg: "#0e2d15", color: "#4ade80", icon: CheckCircle, label: "Settled" },
  partial: { bg: "#2d2a0e", color: "#facc15", icon: Clock,        label: "Partial" },
  open:    { bg: "#2d1a1a", color: "#f87171", icon: AlertCircle,  label: "Open" },
};

export default function Splits() {
  const [splits, setSplits] = useState([]);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    detectSplits(days)
      .then(r => setSplits(r.data.split_groups || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const totalNet = splits.reduce((s, g) => s + (g.net_expense || 0), 0);
  const totalPaid = splits.reduce((s, g) => s + (g.total_debit || 0), 0);
  const totalBack = splits.reduce((s, g) => s + (g.total_credited_back || 0), 0);

  return (
    <div className="page">
      {/* Controls */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
          <div>
            <label>Analysis Window</label>
            <select value={days} onChange={e => setDays(Number(e.target.value))}
                    style={{ width: 140 }}>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={60}>Last 60 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
          <button className="btn btn-primary" onClick={load}>
            <Users size={14} /> Detect Splits
          </button>
        </div>
      </div>

      {/* Summary */}
      {splits.length > 0 && (
        <div className="grid-3" style={{ marginBottom: 24 }}>
          {[
            { t: "Total Paid",      v: totalPaid, c: "#f87171" },
            { t: "Received Back",   v: totalBack, c: "#4ade80" },
            { t: "Your Net Share",  v: totalNet,  c: "#7c6af7" },
          ].map(({ t, v, c }) => (
            <div className="card" key={t}>
              <div className="card-title">{t}</div>
              <div className="card-value" style={{ color: c }}>
                ₹{(v || 0).toLocaleString("en-IN")}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Split Groups */}
      {loading ? (
        <div className="loading">⏳ Detecting splits...</div>
      ) : splits.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <Users size={40} />
            <p style={{ marginTop: 8 }}>
              No split groups detected in the last {days} days.
            </p>
            <p style={{ marginTop: 4, fontSize: 12 }}>
              Add more transactions — the AI looks for debits followed by smaller credits.
            </p>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {splits.map((g, i) => {
            const st = STATUS_STYLE[g.status] || STATUS_STYLE.open;
            const StatusIcon = st.icon;
            const conf = Math.round((g.confidence || 0) * 100);
            return (
              <div key={i} className="card">
                <div style={{ display: "flex", justifyContent: "space-between",
                              alignItems: "flex-start", marginBottom: 16 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 14, fontWeight: 600 }}>
                        Group Expense #{g.anchor_tx_id}
                      </span>
                      <span className="badge" style={{ background: st.bg, color: st.color }}>
                        <StatusIcon size={10} /> {st.label}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>
                      {g.member_count} people · Confidence {conf}%
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 20, fontWeight: 700, color: "#7c6af7" }}>
                      ₹{(g.net_expense || 0).toLocaleString("en-IN")}
                    </div>
                    <div style={{ fontSize: 11, color: "#6b7280" }}>your net share</div>
                  </div>
                </div>

                {/* Progress bar */}
                <div style={{ marginBottom: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between",
                                fontSize: 11, color: "#6b7280", marginBottom: 4 }}>
                    <span>₹0</span>
                    <span>Received: ₹{(g.total_credited_back || 0).toLocaleString("en-IN")} of ₹{((g.total_debit || 0) - (g.net_expense || 0)).toLocaleString("en-IN")}</span>
                    <span>₹{(g.total_debit || 0).toLocaleString("en-IN")}</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill"
                         style={{ width: `${Math.min(100, ((g.total_credited_back || 0) / ((g.total_debit || 1))) * 100)}%` }} />
                  </div>
                </div>

                {/* Breakdown */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                  {[
                    ["You Paid",     `₹${(g.total_debit || 0).toLocaleString("en-IN")}`,          "#f87171"],
                    ["Received Back",`₹${(g.total_credited_back || 0).toLocaleString("en-IN")}`,  "#4ade80"],
                    ["Net Expense",  `₹${(g.net_expense || 0).toLocaleString("en-IN")}`,           "#7c6af7"],
                  ].map(([k, v, c]) => (
                    <div key={k} style={{ background: "#0f1117", borderRadius: 8,
                                         padding: "10px 14px", textAlign: "center" }}>
                      <div style={{ fontSize: 10, color: "#4a5080",
                                    textTransform: "uppercase", marginBottom: 4 }}>{k}</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: c }}>{v}</div>
                    </div>
                  ))}
                </div>

                {g.explanation && (
                  <div style={{ marginTop: 12, fontSize: 12, color: "#6b7280",
                                background: "#0f1117", borderRadius: 8, padding: "10px 14px" }}>
                    💡 {g.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}