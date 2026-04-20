import React from "react";

const COLORS = {
  "Food & Dining":    { bg: "#2d1f0e", color: "#fb923c" },
  "Transport":        { bg: "#0e1f2d", color: "#38bdf8" },
  "Shopping":         { bg: "#1f0e2d", color: "#c084fc" },
  "Groceries":        { bg: "#0e2d1a", color: "#4ade80" },
  "Entertainment":    { bg: "#2d0e28", color: "#f472b6" },
  "Travel":           { bg: "#0e2020", color: "#2dd4bf" },
  "Health":           { bg: "#2d1a0e", color: "#fb923c" },
  "Utilities":        { bg: "#1a1a0e", color: "#facc15" },
  "Telecom":          { bg: "#0e1a2d", color: "#60a5fa" },
  "Insurance":        { bg: "#1a2d0e", color: "#86efac" },
  "Investment":       { bg: "#0e2d20", color: "#34d399" },
  "Loan EMI":         { bg: "#2d0e0e", color: "#f87171" },
  "Credit Card":      { bg: "#2d1a1a", color: "#fca5a5" },
  "Income":           { bg: "#0e2d15", color: "#4ade80" },
  "Refund":           { bg: "#1a2d1a", color: "#86efac" },
  "Cash Withdrawal":  { bg: "#2d2a0e", color: "#fde047" },
  "Wallet":           { bg: "#0e1a2d", color: "#93c5fd" },
  "Personal Transfer":{ bg: "#1a1a2d", color: "#a5b4fc" },
  "Personal Care":    { bg: "#2d0e1f", color: "#f9a8d4" },
  "Household":        { bg: "#1f2d0e", color: "#bef264" },
  "Services":         { bg: "#0e2d2d", color: "#67e8f9" },
  "Uncategorised":    { bg: "#1e2235", color: "#6b7280" },
};

export default function CategoryBadge({ category }) {
  const style = COLORS[category] || COLORS["Uncategorised"];
  return (
    <span
      className="badge"
      style={{ background: style.bg, color: style.color }}
    >
      {category}
    </span>
  );
}