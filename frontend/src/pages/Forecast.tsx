import { useEffect, useMemo, useState } from "react";
import { getFutureForecast } from "../api/client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { SimpleTable } from "../components/SimpleTable";

export function ForecastPage() {
  const [storeId, setStoreId] = useState("");
  const [itemId, setItemId] = useState("");
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    getFutureForecast(storeId || undefined, itemId || undefined)
      .then((r) => setRows(Array.isArray(r) ? r : []))
      .catch(() => setRows([]));
  }, [storeId, itemId]);

  const chartData = useMemo(
    () =>
      rows.map((r) => ({
        date: String(r.date).slice(0, 10),
        pred_units: Number(r.pred_units),
      })),
    [rows]
  );

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Future demand forecast (next horizon)</h2>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
        <input
          placeholder="store_id (e.g., CA_1)"
          value={storeId}
          onChange={(e) => setStoreId(e.target.value)}
          style={{ padding: 8, borderRadius: 10, border: "1px solid #e5e7eb" }}
        />
        <input
          placeholder="item_id (optional)"
          value={itemId}
          onChange={(e) => setItemId(e.target.value)}
          style={{ padding: 8, borderRadius: 10, border: "1px solid #e5e7eb" }}
        />
      </div>

      <div style={{ height: 320, border: "1px solid #e5e7eb", borderRadius: 12, padding: 8 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <XAxis dataKey="date" hide />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="pred_units" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h3>Rows</h3>
      <SimpleTable rows={rows} />
    </div>
  );
}
