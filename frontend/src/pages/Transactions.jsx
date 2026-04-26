import React, { useEffect, useState } from "react";
import { getTransactions, correctCategory, deleteTransaction } from "../api";
import CategoryBadge from "../components/CategoryBadge";
import { Trash2, Edit2 } from "lucide-react";

const CATEGORIES = [
  "Food & Dining","Transport","Shopping","Groceries","Entertainment",
  "Travel","Health","Utilities","Telecom","Insurance","Investment",
  "Loan EMI","Credit Card","Income","Refund","Cash Withdrawal",
  "Wallet","Personal Transfer","Personal Care","Household","Services","Uncategorised",
];

export default function Transactions({ showToast }) {
  const [txs, setTxs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ category: "", tx_type: "" });
  const [editTx, setEditTx] = useState(null);
  const [newCat, setNewCat] = useState("");
  const [isReimbursement, setIsReimbursement] = useState(false);

  const load = () => {
    setLoading(true);
    getTransactions({
      category: filter.category || undefined,
      tx_type: filter.tx_type || undefined,
      limit: 100,
    }).then(r => setTxs(r.data.transactions || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [filter]);

  const handleCorrect = async () => {
    if (!newCat) return;
    try {
      await correctCategory(editTx.id, newCat, "General", isReimbursement);
      showToast(`Category updated to "${newCat}"`);
      setEditTx(null);
      load();
    } catch {
      showToast("Failed to update", "error");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this transaction?")) return;
    try {
      await deleteTransaction(id);
      showToast("Transaction deleted");
      load();
    } catch {
      showToast("Failed to delete", "error");
    }
  };

  return (
    <div className="page">
      {/* Filters */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 160 }}>
            <label>Category</label>
            <select value={filter.category}
              onChange={e => setFilter(f => ({ ...f, category: e.target.value }))}>
              <option value="">All Categories</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 140 }}>
            <label>Type</label>
            <select value={filter.tx_type}
              onChange={e => setFilter(f => ({ ...f, tx_type: e.target.value }))}>
              <option value="">All Types</option>
              <option value="debit">Debit</option>
              <option value="credit">Credit</option>
            </select>
          </div>
          <button className="btn btn-secondary" onClick={load}>Refresh</button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading">⏳ Loading transactions...</div>
      ) : txs.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <p>No transactions found. Add some via the SMS page.</p>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Merchant</th>
                <th>Category</th>
                <th>Method</th>
                <th>Confidence</th>
                <th style={{ textAlign: "right" }}>Amount</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {txs.map(tx => {
                const conf = Math.round((tx.confidence || 0) * 100);
                const confColor = conf >= 85 ? "#4ade80" : conf >= 65 ? "#facc15" : "#f87171";
                return (
                  <tr key={tx.id}>
                    <td style={{ color: "#6b7280", fontSize: 12 }}>
                      {tx.tx_date ? new Date(tx.tx_date).toLocaleDateString("en-IN") : "—"}
                    </td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{tx.merchant || "Unknown"}</div>
                      {tx.tags?.length > 0 && (
                        <div style={{ marginTop: 2 }}>
                          {tx.tags.map(t => <span key={t} className="tag">{t}</span>)}
                        </div>
                      )}
                    </td>
                    <td><CategoryBadge category={tx.category} /></td>
                    <td><span className="tag">{tx.payment_method || "—"}</span></td>
                    <td>
                      <span style={{ color: confColor, fontWeight: 600, fontSize: 12 }}>
                        {conf}%
                      </span>
                      <div className="confidence-bar">
                        <div className="confidence-fill"
                             style={{ width: `${conf}%`, background: confColor }} />
                      </div>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <span className={tx.type === "credit" ? "credit-amount" : "debit-amount"}>
                        {tx.type === "credit" ? "+" : "−"}₹{(tx.amount || 0).toLocaleString("en-IN")}
                      </span>
                      {tx.has_refund_applied && (
                        <div style={{ fontSize: 10, color: "#10b981", marginTop: 4, fontWeight: 500, display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
                          <span>↩️ Refund Applied</span>
                          <span style={{ color: "#9ca3af", fontWeight: 400 }}>Net: ₹{(tx.net_amount || 0).toLocaleString("en-IN")}</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button className="btn btn-secondary btn-sm"
                          onClick={() => { setEditTx(tx); setNewCat(tx.category); setIsReimbursement(tx.tags?.includes("reimbursement") || false); }}>
                          <Edit2 size={12} />
                        </button>
                        <button className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(tx.id)}>
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit Modal */}
      {editTx && (
        <div className="modal-overlay" onClick={() => setEditTx(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-title">Edit Category</div>
            <div style={{ marginBottom: 12, fontSize: 13, color: "#9ca3af" }}>
              {editTx.merchant} — ₹{(editTx.amount || 0).toLocaleString("en-IN")}
            </div>
            <div style={{ marginBottom: 8, fontSize: 12, color: "#6b7280" }}>
              Current: <CategoryBadge category={editTx.category} />
            </div>
            <div className="form-group">
              <label>New Category</label>
              <select value={newCat} onChange={e => setNewCat(e.target.value)}>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            {editTx.type === "credit" && (
              <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  id="modal-reimb"
                  checked={isReimbursement}
                  onChange={(e) => setIsReimbursement(e.target.checked)}
                />
                <label htmlFor="modal-reimb" style={{ fontSize: 13, color: "#9ca3af", margin: 0, cursor: "pointer" }}>
                  Reimbursement for earlier spending
                </label>
              </div>
            )}
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" onClick={handleCorrect}>
                Save & Learn
              </button>
              <button className="btn btn-secondary" onClick={() => setEditTx(null)}>
                Cancel
              </button>
            </div>
            <div style={{ fontSize: 11, color: "#4a5080", marginTop: 10 }}>
              💡 This will teach the AI to auto-categorise this merchant in future.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}