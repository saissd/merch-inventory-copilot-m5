import { useEffect, useState } from "react";
import { getRecs } from "../api/client";
import { SimpleTable } from "../components/SimpleTable";

export function PricingPage() {
  const [storeId, setStoreId] = useState("");
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    getRecs("pricing", storeId || undefined)
      .then((r) => setRows(Array.isArray(r) ? r : []))
      .catch(() => setRows([]));
  }, [storeId]);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Pricing / markdown recommendations</h2>

      <input
        placeholder="store_id (optional)"
        value={storeId}
        onChange={(e) => setStoreId(e.target.value)}
        style={{ padding: 8, borderRadius: 10, border: "1px solid #e5e7eb", marginBottom: 12 }}
      />

      <SimpleTable rows={rows} />
    </div>
  );
}
