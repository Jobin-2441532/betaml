import React, { useEffect, useState } from "react";
import { getReviewQueue, approveReview, familyTag } from "../api";
import CategoryBadge from "../components/CategoryBadge";
import { CheckCircle, AlertCircle } from "lucide-react";

const CATEGORIES = [
  "Food & Dining", "Transport", "Shopping", "Groceries", "Entertainment",
  "Travel", "Health", "Utilities", "Telecom", "Insurance", "Investment",
  "Loan EMI", "Credit Card", "Income", "Refund", "Cash Withdrawal",
  "Wallet", "Personal Transfer", "Personal Care", "Household",
  "Services", "Uncategorised",
];

export default function ReviewQueue({ showToast }) {
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selections, setSelections] = useState({});
  const [reimbursements, setReimbursements] = useState({});

  const load = () => {
    setLoading(true);
    getReviewQueue()
      .then((r) => {
        const items = r.data.transactions || [];
        setTxs(items);
        const sel = {};
        const reimbs = {};
        items.forEach((tx) => {
          sel[tx.id] = tx.category || "Uncategorised";
          reimbs[tx.id] = false;
        });
        setSelections(sel);
        setReimbursements(reimbs);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  // ── Approve single transaction ───────────────────────────────────────────
  const handleApprove = async (tx) => {
    try {
      await approveReview(tx.id, selections[tx.id], "General", !!reimbursements[tx.id]);
      showToast(`✅ Approved as "${selections[tx.id]}"`);
      setTxs((prev) => prev.filter((t) => t.id !== tx.id));
    } catch {
      showToast("Failed to approve", "error");
    }
  };

  // ── Family tag ────────────────────────────────────────────────────────────
  const handleFamilyTag = async (tx) => {
    try {
      await familyTag(tx.id, !tx.is_family_expense);
      showToast(
        tx.is_family_expense
          ? "Removed family tag"
          : "Tagged as Family Expense 👨‍👩‍👧"
      );
      load();
    } catch {
      showToast("Failed to tag", "error");
    }
  };

  const conf = (tx) => Math.round((tx.confidence || 0) * 100);

  return (
    <div className="page">

      {/* ── Header Banner ── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <AlertCircle size={22} color="#facc15" />
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>
              {txs.length} transaction{txs.length !== 1 ? "s" : ""} need
              your review
            </div>
            <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
              These were auto-classified with low confidence, or need
              review. Your input teaches the AI.
            </div>
          </div>
          <button
            className="btn btn-secondary"
            style={{ marginLeft: "auto" }}
            onClick={load}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* ── Content ── */}
      {loading ? (
        <div className="loading">⏳ Loading review queue...</div>
      ) : txs.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <CheckCircle
              size={44}
              color="#4ade80"
              style={{ margin: "0 auto 12px", display: "block" }}
            />
            <p style={{ color: "#4ade80", fontWeight: 600, fontSize: 15 }}>
              All caught up!
            </p>
            <p style={{ marginTop: 6, color: "#6b7280" }}>
              No transactions need review right now.
            </p>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {txs.map((tx) => {
            const c = conf(tx);
            const confColor =
              c >= 65 ? "#facc15" : "#f87171";

            return (
              <div key={tx.id} className="card">
                <div style={{
                  display: "flex",
                  gap: 20,
                  alignItems: "flex-start",
                  flexWrap: "wrap",
                }}>

                  {/* ── Left: Transaction info ── */}
                  <div style={{ flex: 2, minWidth: 220 }}>

                    {/* Title row */}
                    <div style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      marginBottom: 6,
                      flexWrap: "wrap",
                    }}>
                      <span style={{ fontWeight: 700, fontSize: 15 }}>
                        {tx.merchant || tx.vpa || "Unknown Merchant"}
                      </span>
                      <span className={
                        tx.type === "credit" ? "credit-amount" : "debit-amount"
                      }>
                        {tx.type === "credit" ? "+" : "−"}
                        ₹{(tx.amount || 0).toLocaleString("en-IN")}
                      </span>

                      {/* Family badge */}
                      {tx.is_family_expense && (
                        <span className="badge" style={{
                          background: "#0e2d15", color: "#4ade80",
                        }}>
                          👨‍👩‍👧 Family
                        </span>
                      )}
                    </div>

                    {/* Date and method */}
                    <div style={{
                      fontSize: 12, color: "#6b7280", marginBottom: 8,
                    }}>
                      {tx.tx_date
                        ? new Date(tx.tx_date).toLocaleDateString("en-IN", {
                            day: "numeric", month: "short", year: "numeric",
                          })
                        : "—"}
                      {" · "}
                      {tx.payment_method || "Unknown method"}
                      {tx.vpa && (
                        <span style={{ marginLeft: 6, color: "#4a5080" }}>
                          · {tx.vpa}
                        </span>
                      )}
                    </div>

                    {/* AI suggestion */}
                    <div style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      flexWrap: "wrap",
                      marginBottom: 6,
                    }}>
                      <span style={{ fontSize: 11, color: "#4a5080" }}>
                        AI suggested:
                      </span>
                      <CategoryBadge category={tx.category} />
                      <span style={{
                        fontSize: 11,
                        color: confColor,
                        fontWeight: 600,
                      }}>
                        {c}% confident
                      </span>
                    </div>

                    {/* Explanation */}
                    {tx.explanation && (
                      <div style={{
                        fontSize: 11, color: "#4a5080",
                        fontStyle: "italic", marginBottom: 8,
                      }}>
                        💡 "{tx.explanation}"
                      </div>
                    )}

                    {/* Raw SMS */}
                    {tx.raw_sms && (
                      <div style={{
                        fontSize: 11, color: "#6b7280",
                        background: "#0f1117", padding: "6px 10px",
                        borderRadius: 6, marginBottom: 8,
                        border: "1px solid #1e2235",
                        fontFamily: "monospace",
                        wordBreak: "break-all"
                      }}>
                        💬 {tx.raw_sms}
                      </div>
                    )}

                    {/* Tags */}
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      {(tx.tags || []).map((tag) => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                  </div>

                  {/* ── Right: Actions ── */}
                  <div style={{ flex: 1, minWidth: 200 }}>

                    {/* Reimbursement Checkbox (Only for Credits) */}
                    {tx.type === "credit" && (
                      <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                        <input
                          type="checkbox"
                          id={`reimb-${tx.id}`}
                          checked={reimbursements[tx.id] || false}
                          onChange={(e) =>
                            setReimbursements((s) => ({
                              ...s,
                              [tx.id]: e.target.checked,
                            }))
                          }
                        />
                        <label htmlFor={`reimb-${tx.id}`} style={{ fontSize: 13, color: "#9ca3af", margin: 0, cursor: "pointer" }}>
                          Reimbursement for earlier spending
                        </label>
                      </div>
                    )}

                    {/* Category selector */}
                    <div className="form-group">
                      <label>Correct Category</label>
                      <select
                        value={selections[tx.id] || "Uncategorised"}
                        onChange={(e) =>
                          setSelections((s) => ({
                            ...s,
                            [tx.id]: e.target.value,
                          }))
                        }
                      >
                        {CATEGORIES.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    {/* Confirm button */}
                    <button
                      className="btn btn-primary"
                      style={{ width: "100%", marginBottom: 8 }}
                      onClick={() => handleApprove(tx)}
                    >
                      <CheckCircle size={13} /> Confirm & Learn
                    </button>

                    {/* Family tag button */}
                    <button
                      className="btn btn-secondary"
                      style={{
                        width: "100%",
                        color: tx.is_family_expense ? "#4ade80" : "#6b7280",
                        borderColor: tx.is_family_expense
                          ? "#4ade80" : "#2d3354",
                      }}
                      onClick={() => handleFamilyTag(tx)}
                    >
                      {tx.is_family_expense
                        ? "✅ Family Expense"
                        : "👨‍👩‍👧 Tag as Family"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}