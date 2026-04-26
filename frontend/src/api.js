import axios from "axios";

const BASE = "http://127.0.0.1:8000";
const api = axios.create({ baseURL: BASE });

export const getUserId = () => {
  const id = localStorage.getItem("finance_ai_user_id");
  return id ? parseInt(id) : null;
};

export const USER_ID = getUserId;

// ── SMS ──────────────────────────────────────────────────────────
export const ingestSMS = (sms_text, location_label = null) =>
  api.post("/api/sms/ingest", { user_id: getUserId(), sms_text, location_label });

export const bulkIngestSMS = (sms_list) =>
  api.post("/api/sms/bulk-ingest", { user_id: getUserId(), sms_list });

// ── Transactions ─────────────────────────────────────────────────
export const getTransactions = (params = {}) =>
  api.get("/api/transactions/", { params: { user_id: getUserId(), ...params } });

export const deleteTransaction = (id) =>
  api.delete(`/api/transactions/${id}`, { params: { user_id: getUserId() } });

// ── New transaction actions ───────────────────────────────────────
export const p2pReview = (transaction_id, context) =>
  api.post("/api/transactions/p2p-review", { user_id: getUserId(), transaction_id, context });

export const basketSplit = (transaction_id, splits) =>
  api.post("/api/transactions/basket-split", { user_id: getUserId(), transaction_id, splits });

export const familyTag = (transaction_id, is_family = true) =>
  api.post("/api/transactions/family-tag", { user_id: getUserId(), transaction_id, is_family });

export const subscriptionReview = (transaction_id, subscription_type, member_count) =>
  api.post("/api/transactions/subscription-review", {
    user_id: getUserId(), transaction_id, subscription_type, member_count
  });

export const getPaymentMethodBreakdown = (days = 30) =>
  api.get("/api/transactions/payment-method-breakdown", {
    params: { user_id: getUserId(), days }
  });

// ── Feedback ─────────────────────────────────────────────────────
export const correctCategory = (transaction_id, category, sub_category, is_reimbursement = false) =>
  api.post("/api/feedback/correct", { user_id: getUserId(), transaction_id, category, sub_category, is_reimbursement });

// ── Splits ───────────────────────────────────────────────────────
export const detectSplits = (days = 30) =>
  api.get("/api/splits/detect", { params: { user_id: getUserId(), days } });

// ── Insights ─────────────────────────────────────────────────────
export const getMonthlySummary = (year, month) =>
  api.get("/api/insights/monthly-summary", { params: { user_id: getUserId(), year, month } });

export const getRecurring = (days = 90) =>
  api.get("/api/insights/recurring", { params: { user_id: getUserId(), days } });

export const getTopMerchants = (days = 30) =>
  api.get("/api/insights/top-merchants", { params: { user_id: getUserId(), days } });

export const getFestivalContext = () =>
  api.get("/api/insights/festival-context");

export const getCashbackSavings = (days = 30) =>
  api.get("/api/insights/cashback-savings", { params: { user_id: getUserId(), days } });

// ── Review Queue ─────────────────────────────────────────────────
export const getReviewQueue = () =>
  api.get("/api/review/queue", { params: { user_id: getUserId() } });

export const approveReview = (transaction_id, category, sub_category, is_reimbursement = false) =>
  api.post("/api/review/approve", { user_id: getUserId(), transaction_id, category, sub_category, is_reimbursement });