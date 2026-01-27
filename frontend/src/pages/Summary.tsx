import { useEffect, useState } from "react";
import { getSummary } from "../api/client";
import { KPI } from "../components/KPI";

export function SummaryPage() {
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    getSummary().then(setSummary).catch(() => setSummary(null));
  }, []);

  const invBefore = summary?.inventory_before;
  const invAfter = summary?.inventory_after;

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Executive summary</h2>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <KPI
          title="Forecast WAPE (validation)"
          value={summary?.forecast_valid_wape != null ? Number(summary.forecast_valid_wape).toFixed(3) : "—"}
        />
        <KPI
          title="Forecast RMSE (validation)"
          value={summary?.forecast_valid_rmse != null ? Number(summary.forecast_valid_rmse).toFixed(3) : "—"}
        />
        <KPI
          title="Stockout units (before → after)"
          value={
            invBefore && invAfter
              ? `${Math.round(invBefore.stockout_units)} → ${Math.round(invAfter.stockout_units)}`
              : "—"
          }
        />
        <KPI
          title="Cost proxy (before → after)"
          value={
            invBefore && invAfter
              ? `${Math.round(invBefore.total_cost)} → ${Math.round(invAfter.total_cost)}`
              : "—"
          }
        />
        <KPI title="Pricing recs rows" value={summary?.pricing_recommendations_rows ?? "—"} />
      </div>

      <div style={{ marginTop: 16, padding: 12, border: "1px solid #e5e7eb", borderRadius: 12 }}>
        <div style={{ fontWeight: 700 }}>What this demo shows (Nordstrom JD)</div>
        <ul style={{ marginTop: 8 }}>
          <li>Demand forecasting (future horizon)</li>
          <li>Inventory positioning (reorder/safety stock outputs)</li>
          <li>Pricing / markdown optimization recommendations</li>
          <li>Assortment recommendation hooks</li>
          <li>Ops: run pipeline + retrain from UI</li>
        </ul>
      </div>
    </div>
  );
}
