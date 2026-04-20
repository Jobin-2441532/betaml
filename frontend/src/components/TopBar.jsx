import React from "react";

export default function TopBar({ title, sub }) {
  return (
    <div className="topbar">
      <div>
        <div className="topbar-title">{title}</div>
        <div className="topbar-sub">{sub}</div>
      </div>
      <div style={{ fontSize: 12, color: "#4a5080" }}>
        {new Date().toLocaleDateString("en-IN", {
          weekday: "long", day: "numeric", month: "long", year: "numeric",
        })}
      </div>
    </div>
  );
}