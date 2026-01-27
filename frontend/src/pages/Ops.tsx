import { useState } from "react";
import { runPipeline } from "../api/client";

export function OpsPage() {
  const [zipPath, setZipPath] = useState("data/m5-forecasting-accuracy.zip");
  const [maxSeries, setMaxSeries] = useState(3000);
  const [log, setLog] = useState<any>(null);

  async function run(endpoint: "run_all" | "forecast_future" | "run_sql" | "retrain") {
    const res = await runPipeline(endpoint, zipPath, maxSeries);
    setLog(res);
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Ops (run pipelines)</h2>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
        <input
          value={zipPath}
          onChange={(e) => setZipPath(e.target.value)}
          style={{ padding: 8, borderRadius: 10, border: "1px solid #e5e7eb", minWidth: 360 }}
        />
        <input
          type="number"
          value={maxSeries}
          onChange={(e) => setMaxSeries(Number(e.target.value))}
          style={{ padding: 8, borderRadius: 10, border: "1px solid #e5e7eb", width: 140 }}
        />
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button onClick={() => run("run_all")} style={{ padding: "8px 12px", borderRadius: 10 }}>
          Run all
        </button>
        <button onClick={() => run("forecast_future")} style={{ padding: "8px 12px", borderRadius: 10 }}>
          Forecast future
        </button>
        <button onClick={() => run("run_sql")} style={{ padding: "8px 12px", borderRadius: 10 }}>
          Run SQL
        </button>
        <button onClick={() => run("retrain")} style={{ padding: "8px 12px", borderRadius: 10 }}>
          Retrain
        </button>
      </div>

      <h3>Last response</h3>
      <pre style={{ whiteSpace: "pre-wrap", border: "1px solid #e5e7eb", borderRadius: 12, padding: 12 }}>
        {log ? JSON.stringify(log, null, 2) : "—"}
      </pre>
    </div>
  );
}
