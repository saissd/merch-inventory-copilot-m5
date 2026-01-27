export function SimpleTable({ rows }: { rows: any[] }) {
  if (!rows || rows.length === 0) return <div style={{ opacity: 0.7 }}>No data yet. Run the pipeline.</div>;

  const cols = Object.keys(rows[0]).slice(0, 12);

  return (
    <div style={{ overflowX: "auto", border: "1px solid #e5e7eb", borderRadius: 12 }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            {cols.map((c) => (
              <th
                key={c}
                style={{ textAlign: "left", padding: 10, fontSize: 12, borderBottom: "1px solid #e5e7eb" }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 50).map((r, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c} style={{ padding: 10, fontSize: 12, borderBottom: "1px solid #f3f4f6" }}>
                  {String(r[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
