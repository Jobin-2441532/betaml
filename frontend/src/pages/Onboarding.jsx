import React, { useState } from "react";
import axios from "axios";

const S = {
  page: {
    minHeight: "100vh",
    background: "#0a0c12",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "'Inter', sans-serif",
    padding: "20px",
  },
  card: {
    width: "100%",
    maxWidth: "440px",
    background: "#13161f",
    border: "1px solid #1e2235",
    borderRadius: "20px",
    padding: "40px",
    boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
  },
  dots: {
    display: "flex",
    gap: "6px",
    justifyContent: "center",
    marginBottom: "32px",
  },
  dot: (active, passed) => ({
    height: "6px",
    borderRadius: "3px",
    background: active || passed ? "#7c6af7" : "#1e2235",
    width: active ? "24px" : "6px",
    transition: "all 0.3s ease",
  }),
  logo: {
    textAlign: "center",
    marginBottom: "28px",
  },
  logoEmoji: {
    fontSize: "52px",
    display: "block",
    marginBottom: "12px",
  },
  logoTitle: {
    fontSize: "26px",
    fontWeight: "800",
    color: "#f1f5f9",
    margin: "0 0 6px 0",
    letterSpacing: "-0.5px",
  },
  logoSub: {
    fontSize: "14px",
    color: "#6b7280",
    margin: 0,
  },
  label: {
    display: "block",
    fontSize: "11px",
    fontWeight: "600",
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "6px",
  },
  input: {
    width: "100%",
    background: "#1a1d27",
    border: "1px solid #2d3354",
    borderRadius: "10px",
    color: "#e2e8f0",
    fontSize: "14px",
    padding: "12px 16px",
    outline: "none",
    boxSizing: "border-box",
    fontFamily: "'Inter', sans-serif",
    transition: "border 0.15s",
  },
  inputFocus: {
    border: "1px solid #7c6af7",
  },
  formGroup: {
    marginBottom: "16px",
  },
  btnPrimary: {
    width: "100%",
    background: "#7c6af7",
    color: "#fff",
    border: "none",
    borderRadius: "10px",
    padding: "13px",
    fontSize: "14px",
    fontWeight: "700",
    cursor: "pointer",
    fontFamily: "'Inter', sans-serif",
    transition: "background 0.15s",
    marginTop: "4px",
  },
  btnSecondary: {
    background: "#1e2235",
    color: "#cbd5e1",
    border: "1px solid #2d3354",
    borderRadius: "10px",
    padding: "12px 20px",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
    fontFamily: "'Inter', sans-serif",
    transition: "background 0.15s",
  },
  questionTitle: {
    fontSize: "20px",
    fontWeight: "700",
    color: "#f1f5f9",
    marginBottom: "6px",
  },
  questionSub: {
    fontSize: "13px",
    color: "#6b7280",
    marginBottom: "24px",
    lineHeight: "1.5",
  },
  optionCard: (selected) => ({
    padding: "16px 18px",
    borderRadius: "12px",
    cursor: "pointer",
    border: `2px solid ${selected ? "#7c6af7" : "#1e2235"}`,
    background: selected ? "#1e1b4b" : "#0f1117",
    marginBottom: "10px",
    transition: "all 0.15s",
  }),
  optionLabel: {
    fontWeight: "600",
    fontSize: "15px",
    color: "#f1f5f9",
    marginBottom: "3px",
  },
  optionDesc: {
    fontSize: "12px",
    color: "#6b7280",
  },
  error: {
    color: "#f87171",
    fontSize: "12px",
    marginBottom: "12px",
    padding: "10px 14px",
    background: "#2d1a1a",
    borderRadius: "8px",
    border: "1px solid #5c2d3d",
  },
  btnRow: {
    display: "flex",
    gap: "10px",
    marginTop: "20px",
  },
  stepIndicator: {
    fontSize: "12px",
    color: "#4a5080",
    textAlign: "center",
    marginBottom: "20px",
  },
};

const USER_TYPES = [
  { value: "student",    label: "🎓 Student",              desc: "Still studying" },
  { value: "working",    label: "💼 Working Professional",  desc: "Salaried employee" },
  { value: "freelancer", label: "💻 Freelancer",            desc: "Self-employed / gigs" },
  { value: "business",   label: "🏢 Business Owner",        desc: "Running a business" },
];

const SHOP_TYPES = [
  { value: "online",  label: "🛍️ Online mostly",     desc: "Amazon, Flipkart, Myntra etc." },
  { value: "offline", label: "🏪 Local shops mostly", desc: "Kirana, malls, markets" },
  { value: "mixed",   label: "🔀 Mix of both",         desc: "Depends on what I need" },
];

const FOOD_TYPES = [
  { value: "cook",  label: "👨‍🍳 Cook at home",   desc: "Prefer home-cooked meals" },
  { value: "order", label: "🍕 Order food",        desc: "Swiggy / Zomato regular" },
  { value: "both",  label: "⚖️ Both equally",      desc: "Depends on the day" },
];

export default function Onboarding({ onComplete }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    email: "", phone: "", password: "",
    user_type: "", shopping_behavior: "", food_habit: "",
  });
  const [focusedField, setFocusedField] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const setField = (key, val) =>
    setForm((f) => ({ ...f, [key]: val }));

  const handleRegister = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/users/register",
        form
      );
      localStorage.setItem("finance_ai_user_id", String(res.data.id));
      onComplete(res.data.id);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        "Registration failed. Check your details and try again."
      );
      setLoading(false);
    }
  };

  // ── Step 0: Account details ────────────────────────────────────────────────
  const StepAccount = (
    <div>
      <div style={S.logo}>
        <span style={S.logoEmoji}>💰</span>
        <h1 style={S.logoTitle}>Welcome to FinanceAI</h1>
        <p style={S.logoSub}>
          Your AI-powered money tracker. Set up takes 60 seconds.
        </p>
      </div>

      <div style={S.formGroup}>
        <label style={S.label}>Email Address</label>
        <input
          type="email"
          placeholder="you@example.com"
          value={form.email}
          style={{
            ...S.input,
            ...(focusedField === "email" ? S.inputFocus : {}),
          }}
          onFocus={() => setFocusedField("email")}
          onBlur={() => setFocusedField(null)}
          onChange={(e) => setField("email", e.target.value)}
        />
      </div>

      <div style={S.formGroup}>
        <label style={S.label}>Phone Number</label>
        <input
          type="tel"
          placeholder="9876543210"
          value={form.phone}
          style={{
            ...S.input,
            ...(focusedField === "phone" ? S.inputFocus : {}),
          }}
          onFocus={() => setFocusedField("phone")}
          onBlur={() => setFocusedField(null)}
          onChange={(e) => setField("phone", e.target.value)}
        />
      </div>

      <div style={S.formGroup}>
        <label style={S.label}>Password</label>
        <input
          type="password"
          placeholder="Create a strong password"
          value={form.password}
          style={{
            ...S.input,
            ...(focusedField === "password" ? S.inputFocus : {}),
          }}
          onFocus={() => setFocusedField("password")}
          onBlur={() => setFocusedField(null)}
          onChange={(e) => setField("password", e.target.value)}
        />
      </div>

      {error && <div style={S.error}>⚠️ {error}</div>}

      <button
        style={S.btnPrimary}
        onClick={() => {
          if (!form.email || !form.phone || !form.password) {
            setError("Please fill in all fields to continue.");
            return;
          }
          setError("");
          setStep(1);
        }}
      >
        Continue →
      </button>
    </div>
  );

  // ── Step 1: User type ──────────────────────────────────────────────────────
  const StepUserType = (
    <div>
      <div style={S.questionTitle}>What best describes you?</div>
      <div style={S.questionSub}>
        This helps us tailor financial insights for your lifestyle.
      </div>

      {USER_TYPES.map((t) => (
        <div
          key={t.value}
          style={S.optionCard(form.user_type === t.value)}
          onClick={() => setField("user_type", t.value)}
        >
          <div style={S.optionLabel}>{t.label}</div>
          <div style={S.optionDesc}>{t.desc}</div>
        </div>
      ))}

      <div style={S.btnRow}>
        <button style={S.btnSecondary} onClick={() => setStep(0)}>
          ← Back
        </button>
        <button
          style={{
            ...S.btnPrimary,
            marginTop: 0,
            flex: 1,
            opacity: form.user_type ? 1 : 0.5,
          }}
          onClick={() => { if (form.user_type) setStep(2); }}
        >
          Continue →
        </button>
      </div>
    </div>
  );

  // ── Step 2: Shopping behavior ──────────────────────────────────────────────
  const StepShopping = (
    <div>
      <div style={S.questionTitle}>Where do you mostly shop?</div>
      <div style={S.questionSub}>
        Helps us categorise your purchase transactions more accurately.
      </div>

      {SHOP_TYPES.map((t) => (
        <div
          key={t.value}
          style={S.optionCard(form.shopping_behavior === t.value)}
          onClick={() => setField("shopping_behavior", t.value)}
        >
          <div style={S.optionLabel}>{t.label}</div>
          <div style={S.optionDesc}>{t.desc}</div>
        </div>
      ))}

      <div style={S.btnRow}>
        <button style={S.btnSecondary} onClick={() => setStep(1)}>
          ← Back
        </button>
        <button
          style={{
            ...S.btnPrimary,
            marginTop: 0,
            flex: 1,
            opacity: form.shopping_behavior ? 1 : 0.5,
          }}
          onClick={() => { if (form.shopping_behavior) setStep(3); }}
        >
          Continue →
        </button>
      </div>
    </div>
  );

  // ── Step 3: Food habit ─────────────────────────────────────────────────────
  const StepFood = (
    <div>
      <div style={S.questionTitle}>How do you handle food?</div>
      <div style={S.questionSub}>
        Helps us understand your Food & Dining spending patterns.
      </div>

      {FOOD_TYPES.map((t) => (
        <div
          key={t.value}
          style={S.optionCard(form.food_habit === t.value)}
          onClick={() => setField("food_habit", t.value)}
        >
          <div style={S.optionLabel}>{t.label}</div>
          <div style={S.optionDesc}>{t.desc}</div>
        </div>
      ))}

      {error && <div style={{ ...S.error, marginTop: "12px" }}>⚠️ {error}</div>}

      <div style={S.btnRow}>
        <button style={S.btnSecondary} onClick={() => setStep(2)}>
          ← Back
        </button>
        <button
          style={{
            ...S.btnPrimary,
            marginTop: 0,
            flex: 1,
            opacity: form.food_habit && !loading ? 1 : 0.5,
            cursor: loading ? "not-allowed" : "pointer",
          }}
          disabled={!form.food_habit || loading}
          onClick={handleRegister}
        >
          {loading ? "⏳ Setting up your account..." : "🚀 Start Tracking →"}
        </button>
      </div>
    </div>
  );

  const steps = [StepAccount, StepUserType, StepShopping, StepFood];
  const stepLabels = ["Account", "About you", "Shopping", "Food"];

  return (
    <div style={S.page}>
      <div style={S.card}>

        {/* Progress dots */}
        <div style={S.dots}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={S.dot(i === step, i < step)} />
          ))}
        </div>

        {/* Step label */}
        <div style={S.stepIndicator}>
          Step {step + 1} of 4 — {stepLabels[step]}
        </div>

        {/* Step content */}
        {steps[step]}

      </div>
    </div>
  );
}