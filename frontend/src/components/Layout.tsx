import React from "react";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial",
        padding: 16,
        maxWidth: 1200,
        margin: "0 auto",
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          gap: 12,
          marginBottom: 16,
          flexWrap: "wrap",
        }}
      >
        <div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>
            Merchandising & Inventory ML Dashboard
          </div>
          <div style={{ opacity: 0.75 }}>
            Forecasting → Inventory → Pricing/Markdown → Assortment
          </div>
        </div>

        <nav style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <a href="#/" style={{ textDecoration: "none" }}>Summary</a>
	      <a href="#/copilot" style={{ textDecoration: "none" }}>Copilot</a>
          <a href="#/forecast" style={{ textDecoration: "none" }}>Forecast</a>
          <a href="#/inventory" style={{ textDecoration: "none" }}>Inventory</a>
          <a href="#/pricing" style={{ textDecoration: "none" }}>Pricing</a>
          <a href="#/assortment" style={{ textDecoration: "none" }}>Assortment</a>
          <a href="#/ops" style={{ textDecoration: "none" }}>Ops</a>
        </nav>
      </header>

      <main>{children}</main>

      <footer style={{ marginTop: 18, opacity: 0.6, fontSize: 12 }}>
        Demo app (M5 dataset) aligned to Nordstrom Merchandising & Inventory ML role.
      </footer>
    </div>
  );
}
