export function KPI({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string;
  subtitle?: string;
}) {
  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: 12, padding: 12, minWidth: 220 }}>
      <div style={{ fontSize: 12, opacity: 0.7 }}>{title}</div>
      <div style={{ fontSize: 22, fontWeight: 700, marginTop: 6 }}>{value}</div>
      {subtitle ? <div style={{ fontSize: 12, opacity: 0.7, marginTop: 6 }}>{subtitle}</div> : null}
    </div>
  );
}
