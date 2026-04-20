import React, { useState } from "react";
import { ingestSMS, bulkIngestSMS } from "../api";
import CategoryBadge from "../components/CategoryBadge";
import { Send, Upload } from "lucide-react";

const SAMPLES = [
  "Rs.450 debited from A/c XX1234. VPA swiggy@icici. Date 14/04/2024",
  "INR 75,000 credited to A/c XX5678. Remarks: SALARY APR 2024",
  "ATM WDL Rs.5000 from A/c XX1234. Date 14-04-2024",
  "Rs.499 debited for Netflix subscription. Date 01/04/2024",
  "REFUND of Rs.350 credited. Swiggy order cancelled.",
  "Rs.8500 debited. NACH debit HOME LOAN EMI. Date 01/04/2024",
];

export default function SMSInput({ showToast }) {
  const [sms, setSms] = useState("");
  const [bulkText, setBulkText] = useState("");
  const [result, setResult] = useState(null);
  const [bulkResults, setBulkResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("single");

  // Replace the handleSingle function:
  const handleSingle = async () => {
    if (!sms.trim()) return;
    setLoading(true);
    try {
      const res = await ingestSMS(sms.trim());
      setResult(res.data);
      showToast("Transaction classified successfully!");

      // Trigger popups if needed
      if (res.data.needs_p2p_review && triggerP2PPopup) {
        setTimeout(() => triggerP2PPopup(res.data), 800);
      }
      if (res.data.needs_subscription_review && triggerSubPopup) {
        setTimeout(() => triggerSubPopup(res.data), 800);
      }
    } catch (e) {
      showToast(e.response?.data?.detail || "Error classifying SMS", "error");
    } finally {
      setLoading(false);
    }
  };

  

  const handleBulk = async () => {
    const lines = bulkText.split("\n").map(l => l.trim()).filter(Boolean);
    if (!lines.length) return;
    setLoading(true);
    try {
      const res = await bulkIngestSMS(lines);
      setBulkResults(res.data.results || []);
      showToast(`Processed ${res.data.processed} SMS messages!`);
    } catch (e) {
      showToast("Bulk import failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {["single", "bulk"].map(t => (
          <button
            key={t}
            className={`btn ${tab === t ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setTab(t)}
          >
            {t === "single" ? "Single SMS" : "Bulk Import"}
          </button>
        ))}
      </div>

      <div className="grid-2">
        {/* Input Panel */}
        <div>
          {tab === "single" ? (
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>
                Paste a Bank SMS
              </div>
              <div className="form-group">
                <label>SMS Text</label>
                <textarea
                  rows={5}
                  value={sms}
                  onChange={e => setSms(e.target.value)}
                  placeholder="Paste your bank SMS here..."
                />
              </div>
              <button className="btn btn-primary" onClick={handleSingle} disabled={loading}>
                <Send size={14} />
                {loading ? "Classifying..." : "Classify SMS"}
              </button>

              {/* Sample SMSes */}
              <div style={{ marginTop: 24 }}>
                <div style={{ fontSize: 11, color: "#4a5080", marginBottom: 10,
                              textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Try a Sample
                </div>
                {SAMPLES.map((s, i) => (
                  <div
                    key={i}
                    onClick={() => setSms(s)}
                    style={{
                      padding: "8px 12px", background: "#0f1117",
                      border: "1px solid #1e2235", borderRadius: 6,
                      fontSize: 11, color: "#6b7280", cursor: "pointer",
                      marginBottom: 6, transition: "all 0.15s",
                    }}
                    onMouseEnter={e => e.target.style.borderColor = "#7c6af7"}
                    onMouseLeave={e => e.target.style.borderColor = "#1e2235"}
                  >
                    {s.slice(0, 70)}...
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>
                Bulk SMS Import
              </div>
              <div className="form-group">
                <label>One SMS per line</label>
                <textarea
                  rows={10}
                  value={bulkText}
                  onChange={e => setBulkText(e.target.value)}
                  placeholder={"Rs.450 debited. VPA swiggy@icici.\nINR 75000 credited. SALARY APR 2024.\n..."}
                />
              </div>
              <button className="btn btn-primary" onClick={handleBulk} disabled={loading}>
                <Upload size={14} />
                {loading ? "Processing..." : `Import ${bulkText.split("\n").filter(l=>l.trim()).length} SMS`}
              </button>
            </div>
          )}
        </div>

        {/* Results Panel */}
        <div>
          {tab === "single" && result && (
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>
                Classification Result
              </div>
              <ResultCard result={result} />
            </div>
          )}

          {tab === "bulk" && bulkResults.length > 0 && (
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>
                Bulk Results ({bulkResults.length})
              </div>
              <div style={{ maxHeight: 500, overflowY: "auto" }}>
                {bulkResults.map((r, i) => (
                  <div key={i} style={{
                    padding: "10px 12px", background: "#0f1117",
                    border: `1px solid ${r.status === "ok" ? "#1e2235" : "#5c2d3d"}`,
                    borderRadius: 8, marginBottom: 8,
                  }}>
                    {r.status === "ok" ? (
                      <div style={{ display: "flex", alignItems: "center",
                                    justifyContent: "space-between" }}>
                        <div>
                          <CategoryBadge category={r.data.category} />
                          <span style={{ fontSize: 12, color: "#6b7280", marginLeft: 8 }}>
                            {r.data.merchant || "Unknown"}
                          </span>
                        </div>
                        <span className={r.data.type === "credit" ? "credit-amount" : "debit-amount"}
                              style={{ fontSize: 13 }}>
                          ₹{(r.data.amount || 0).toLocaleString("en-IN")}
                        </span>
                      </div>
                    ) : (
                      <span style={{ fontSize: 12, color: "#f87171" }}>
                        ❌ {r.detail}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultCard({ result }) {
  const conf = Math.round((result.confidence || 0) * 100);
  const confColor = conf >= 85 ? "#4ade80" : conf >= 65 ? "#facc15" : "#f87171";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <CategoryBadge category={result.category} />
          {result.sub_category && (
            <span style={{ fontSize: 11, color: "#6b7280", marginLeft: 8 }}>
              {result.sub_category}
            </span>
          )}
        </div>
        <span className={result.type === "credit" ? "credit-amount" : "debit-amount"}
              style={{ fontSize: 20 }}>
          {result.type === "credit" ? "+" : "−"}₹{(result.amount || 0).toLocaleString("en-IN")}
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
        {[
          ["Merchant", result.merchant || "Unknown"],
          ["Payment Method", result.payment_method || "—"],
          ["Type", result.type?.toUpperCase()],
          ["Net Amount", `₹${(result.net_amount || 0).toLocaleString("en-IN")}`],
        ].map(([k, v]) => (
          <div key={k} style={{ background: "#0f1117", borderRadius: 8, padding: "10px 14px" }}>
            <div style={{ fontSize: 10, color: "#4a5080", textTransform: "uppercase",
                          letterSpacing: "0.5px", marginBottom: 4 }}>{k}</div>
            <div style={{ fontSize: 13, color: "#e2e8f0" }}>{v}</div>
          </div>
        ))}
      </div>

      {/* Confidence */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between",
                      fontSize: 12, marginBottom: 6 }}>
          <span style={{ color: "#6b7280" }}>Confidence</span>
          <span style={{ color: confColor, fontWeight: 600 }}>{conf}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${conf}%`,
            background: conf >= 85 ? "#4ade80" : conf >= 65 ? "#facc15" : "#f87171" }} />
        </div>
        <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>
          {result.confidence_display}
        </div>
      </div>

      {/* Explanation */}
      {result.explanation && (
        <div style={{ background: "#0f1117", borderRadius: 8, padding: "12px 14px",
                      fontSize: 12, color: "#9ca3af", lineHeight: 1.6 }}>
          💡 {result.explanation}
        </div>
      )}

      {/* Flags */}
      <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
        {result.is_recurring && <span className="tag">🔁 Recurring</span>}
        {result.is_split    && <span className="tag">👥 Split</span>}
        {result.is_refund   && <span className="tag">↩️ Refund</span>}
        {result.is_income   && <span className="tag">💰 Income</span>}
      </div>
    </div>
  );
}