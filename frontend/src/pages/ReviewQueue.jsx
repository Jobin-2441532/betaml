import React, { useEffect, useState } from "react";
import { getReviewQueue, approveReview, basketSplit, familyTag } from "../api";
import CategoryBadge from "../components/CategoryBadge";
import { CheckCircle, AlertCircle } from "lucide-react";

const CATEGORIES = [
  "Food & Dining", "Transport", "Shopping", "Groceries", "Entertainment",
  "Travel", "Health", "Utilities", "Telecom", "Insurance", "Investment",
  "Loan EMI", "Credit Card", "Income", "Refund", "Cash Withdrawal",
  "Wallet", "Personal Transfer", "Personal Care", "Household",
  "Services", "Uncategorised",
];

const QUICK_CATEGORIES = [
  { label: "🥦 Groceries",     value: "Groceries" },
  { label: "🧴 Personal Care", value: "Personal Care" },
  { label: "🧹 Household",     value: "Household" },
  { label: "👕 Clothing",      value: "Shopping" },
  { label: "💊 Health",        value: "Health" },
  { label: "🍕 Food",          value: "Food & Dining" },
];

export default function ReviewQueue({ showToast }) {
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selections, setSelections] = useState({});

  // Basket split state
  const [basketTx, setBasketTx] = useState(null);
  const [basketItems, setBasketItems] = useState([]);

  const load = () => {
    setLoading(true);
    getReviewQueue()
      .then((r) => {
        const items = r.data.transactions || [];
        setTxs(items);
        const sel = {};
        items.forEach((tx) => {
          sel[tx.id] = tx.category || "Uncategorised";
        });
        setSelections(sel);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  // ── Approve single transaction ───────────────────────────────────────────
  const handleApprove = async (tx) => {
    try {
      await approveReview(tx.id, selections[tx.id], "General");
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

  // ── Basket split save ─────────────────────────────────────────────────────
  const handleBasketSave = async () => {
    if (!basketTx) return;
    const total = basketItems.reduce((s, i) => s + Number(i.amount || 0), 0);
    if (Math.abs(total - basketTx.amount) > 1) {
      showToast(
        `Amounts don't add up. Need ₹${basketTx.amount}, got ₹${total.toFixed(0)}`,
        "error"
      );
      return;
    }
    try {
      await basketSplit(basketTx.id, basketItems);
      showToast("Split saved successfully! ✅");
      setBasketTx(null);
      setBasketItems([]);
      load();
    } catch {
      showToast("Failed to save split", "error");
    }
  };

  const openBasket = (tx) => {
    setBasketTx(tx);
    setBasketItems([]);
  };

  const basketTotal = basketItems.reduce(
    (s, i) => s + Number(i.amount || 0), 0
  );
  const basketBalanced =
    basketTx && Math.abs(basketTotal - basketTx.amount) < 1;

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
              splitting. Your input teaches the AI.
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

                      {/* Mixed basket badge */}
                      {tx.is_mixed_basket && (
                        <span className="badge" style={{
                          background: "#2d2a0e", color: "#facc15",
                        }}>
                          🛒 Mixed Basket
                        </span>
                      )}

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

                    {/* Tags */}
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      {(tx.tags || []).map((tag) => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                  </div>

                  {/* ── Right: Actions ── */}
                  <div style={{ flex: 1, minWidth: 200 }}>

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

                    {/* Mixed basket split button */}
                    {tx.is_mixed_basket && (
                      <button
                        className="btn btn-secondary"
                        style={{ width: "100%", marginBottom: 8 }}
                        onClick={() => openBasket(tx)}
                      >
                        🛒 Split into Categories
                      </button>
                    )}

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

      {/* ── Mixed Basket Split Modal ── */}
      {basketTx && (
        <div
          className="modal-overlay"
          onClick={() => { setBasketTx(null); setBasketItems([]); }}
        >
          <div
            className="modal"
            style={{ width: 500 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="modal-title">
              🛒 Split: {basketTx.merchant} — ₹{basketTx.amount}
            </div>
            <div style={{
              fontSize: 12, color: "#6b7280", marginBottom: 16,
            }}>
              Break this into categories. Total must equal ₹{basketTx.amount}.
            </div>

            {/* Quick-add chips */}
            <div style={{ marginBottom: 16 }}>
              <div style={{
                fontSize: 11, color: "#4a5080",
                marginBottom: 8, textTransform: "uppercase",
                letterSpacing: "0.4px",
              }}>
                Quick Add:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {QUICK_CATEGORIES.map((cat) => (
                  <span
                    key={cat.value}
                    className="chip unselected"
                    style={{ cursor: "pointer" }}
                    onClick={() =>
                      setBasketItems((prev) => [
                        ...prev,
                        { category: cat.value, amount: "" },
                      ])
                    }
                  >
                    + {cat.label}
                  </span>
                ))}
              </div>
            </div>

            {/* Line items */}
            {basketItems.length === 0 && (
              <div style={{
                padding: "20px",
                textAlign: "center",
                color: "#4a5080",
                fontSize: 13,
                background: "#0f1117",
                borderRadius: 8,
                marginBottom: 12,
              }}>
                Click Quick Add above or add items below
              </div>
            )}

            {basketItems.map((item, i) => (
              <div key={i} style={{
                display: "flex", gap: 8,
                marginBottom: 8, alignItems: "center",
              }}>
                <select
                  value={item.category}
                  onChange={(e) =>
                    setBasketItems((prev) =>
                      prev.map((it, idx) =>
                        idx === i
                          ? { ...it, category: e.target.value }
                          : it
                      )
                    )
                  }
                  style={{ flex: 2 }}
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>

                <input
                  type="number"
                  placeholder="₹ Amount"
                  value={item.amount}
                  min={0}
                  onChange={(e) =>
                    setBasketItems((prev) =>
                      prev.map((it, idx) =>
                        idx === i
                          ? { ...it, amount: e.target.value }
                          : it
                      )
                    )
                  }
                  style={{ flex: 1 }}
                />

                <button
                  className="btn btn-danger btn-sm"
                  onClick={() =>
                    setBasketItems((prev) =>
                      prev.filter((_, idx) => idx !== i)
                    )
                  }
                >
                  ×
                </button>
              </div>
            ))}

            {/* Add custom row */}
            <button
              className="btn btn-secondary btn-sm"
              style={{ marginBottom: 16 }}
              onClick={() =>
                setBasketItems((prev) => [
                  ...prev,
                  { category: "Groceries", amount: "" },
                ])
              }
            >
              + Add Row
            </button>

            {/* Running total */}
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 16px",
              background: "#0f1117",
              borderRadius: 8,
              marginBottom: 16,
              border: `1px solid ${basketBalanced ? "#4ade80" : "#2d3354"}`,
            }}>
              <span style={{ fontSize: 13, color: "#6b7280" }}>
                Total Assigned
              </span>
              <div style={{ textAlign: "right" }}>
                <span style={{
                  fontWeight: 700,
                  fontSize: 16,
                  color: basketBalanced ? "#4ade80" : "#f87171",
                }}>
                  ₹{basketTotal.toFixed(0)}
                </span>
                <span style={{ color: "#4a5080", fontSize: 12 }}>
                  {" "}/ ₹{basketTx.amount}
                </span>
              </div>
            </div>

            {!basketBalanced && basketItems.length > 0 && (
              <div style={{
                fontSize: 12, color: "#f87171",
                marginBottom: 12, textAlign: "center",
              }}>
                {basketTotal < basketTx.amount
                  ? `₹${(basketTx.amount - basketTotal).toFixed(0)} still unassigned`
                  : `₹${(basketTotal - basketTx.amount).toFixed(0)} over budget`}
              </div>
            )}

            {/* Action buttons */}
            <div style={{ display: "flex", gap: 10 }}>
              <button
                className="btn btn-primary"
                style={{ flex: 1 }}
                disabled={!basketBalanced || basketItems.length === 0}
                onClick={handleBasketSave}
              >
                ✅ Save Split
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setBasketTx(null);
                  setBasketItems([]);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}