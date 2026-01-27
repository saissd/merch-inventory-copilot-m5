import { useEffect, useMemo, useRef, useState } from "react";
import { chatAgent, downloadsUrl, getSummary } from "../api/client";
import { KPI } from "../components/KPI";
import { SimpleTable } from "../components/SimpleTable";
import type { AgentChatPayload, ChatMsg } from "../types";

declare global {
  interface Window {
    webkitSpeechRecognition?: any;
    SpeechRecognition?: any;
  }
}

function uid() {
  return crypto.randomUUID();
}

const LS_KEY = "m5_copilot_chat_v1";

export function CopilotPage() {
  const [storeId, setStoreId] = useState<string>("CA_1");
  const [itemId, setItemId] = useState<string>("");

  const [conversationId, setConversationId] = useState<string>(() => {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return uid();
    try {
      const parsed = JSON.parse(raw);
      return parsed?.conversationId || uid();
    } catch {
      return uid();
    }
  });

  const [msgs, setMsgs] = useState<ChatMsg[]>(() => {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) {
      return [
        {
          role: "assistant",
          text: "Hi! I'm your Merch & Inventory Copilot (M5 demo). Ask about a store like CA_1 and I’ll propose actions using the generated reports.",
          ts: Date.now(),
        },
      ];
    }
    try {
      const parsed = JSON.parse(raw);
      return parsed?.msgs?.length
        ? parsed.msgs
        : [
            {
              role: "assistant",
              text: "Hi! I'm your Merch & Inventory Copilot (M5 demo). Ask about a store like CA_1 and I’ll propose actions using the generated reports.",
              ts: Date.now(),
            },
          ];
    } catch {
      return [
        {
          role: "assistant",
          text: "Hi! I'm your Merch & Inventory Copilot (M5 demo). Ask about a store like CA_1 and I’ll propose actions using the generated reports.",
          ts: Date.now(),
        },
      ];
    }
  });

  const [input, setInput] = useState<string>(
    "What should I order today for CA_1? Include order_qty and days_of_supply."
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [listening, setListening] = useState<boolean>(false);

  const [agent, setAgent] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  // persist conversation
  useEffect(() => {
    localStorage.setItem(LS_KEY, JSON.stringify({ conversationId, msgs }));
  }, [conversationId, msgs]);

  useEffect(() => {
    getSummary().then(setSummary).catch(() => setSummary(null));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, loading, agent]);

  const canVoice = useMemo(() => Boolean(window.SpeechRecognition || window.webkitSpeechRecognition), []);

  const history = useMemo(
    () =>
      msgs
        .filter((m) => m.role === "user" || m.role === "assistant")
        .slice(-16)
        .map((m) => ({ role: m.role, content: m.text })),
    [msgs]
  );

  const startVoice = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = false;

    setListening(true);

    rec.onresult = (e: any) => {
      const transcript = Array.from(e.results)
        .map((r: any) => r[0].transcript)
        .join("");
      if (transcript) setInput(transcript);
    };

    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);

    rec.start();
  };

  const newChat = () => {
    setConversationId(uid());
    setAgent(null);
    setMsgs([
      {
        role: "assistant",
        text: "New chat started. Tell me the store (e.g., CA_1) and your objective (min cost vs max service level).",
        ts: Date.now(),
      },
    ]);
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setMsgs((m) => [...m, { role: "user", text, ts: Date.now() }]);
    setLoading(true);

    try {
      const payload: AgentChatPayload = {
        message: text,
        store_id: storeId || null,
        item_id: itemId || null,
        conversation_id: conversationId,
        history,
      };

      const resp = await chatAgent(payload);
      const a = resp?.answer ?? resp;   // ✅ unwrap
      setAgent(a);

      let assistantText =
        a?.explanation ||
        a?.memo ||
        "Done. See the decision panels on the right.";

      if (a?.downloads && typeof a.downloads === "object") {
        const links = Object.entries(a.downloads)
          .map(([k, v]: any) => `- ${k}: ${downloadsUrl(String(v))}`)
          .join("\n");
        assistantText += `\n\nDOWNLOAD LINKS\n${links}`;
      }   
      setMsgs((m) => [...m, { role: "assistant", text: assistantText, ts: Date.now() }]);
    } catch (e: any) {
      setMsgs((m) => [...m, { role: "assistant", text: `Error: ${String(e?.message || e)}`, ts: Date.now() }]);
    } finally {
      setLoading(false);
    }
  };

  const km = agent?.key_metrics || {};
  const inv = agent?.inventory_actions || [];
  const prc = agent?.pricing_actions || [];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.35fr 1fr", gap: 16, alignItems: "start" }}>
      {/* LEFT: Chat */}
      <div>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 10 }}>
          <div>
            <h2 style={{ margin: 0 }}>Merch Copilot</h2>
            <div style={{ opacity: 0.75, fontSize: 13 }}>
              Chat-style assistant over M5 reports (demo). Deterministic + tool-backed outputs.
            </div>
          </div>

          <button
            onClick={newChat}
            style={{ padding: "8px 12px", borderRadius: 12, border: "1px solid #e5e7eb", background: "#fff" }}
          >
            New chat
          </button>
        </div>

        <div
          style={{
            marginTop: 12,
            border: "1px solid #e5e7eb",
            borderRadius: 16,
            padding: 12,
            height: 560,
            overflowY: "auto",
            background: "#fff",
          }}
        >
          {msgs.map((m, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                margin: "10px 0",
              }}
            >
              <div
                style={{
                  maxWidth: "88%",
                  padding: "10px 12px",
                  borderRadius: 14,
                  border: "1px solid #e5e7eb",
                  background: m.role === "user" ? "#111827" : "#f9fafb",
                  color: m.role === "user" ? "#fff" : "#111827",
                  fontSize: 13,
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.35,
                }}
              >
                {m.text}
              </div>
            </div>
          ))}
          {loading && <div style={{ opacity: 0.7, fontSize: 13, padding: 8 }}>Thinking…</div>}
          <div ref={bottomRef} />
        </div>

        {/* Composer */}
        <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
          <input
            value={storeId}
            onChange={(e) => setStoreId(e.target.value)}
            placeholder="store_id (e.g., CA_1)"
            style={{ padding: 10, borderRadius: 12, border: "1px solid #e5e7eb", width: 140 }}
          />
          <input
            value={itemId}
            onChange={(e) => setItemId(e.target.value)}
            placeholder="item_id (optional)"
            style={{ padding: 10, borderRadius: 12, border: "1px solid #e5e7eb", width: 170 }}
          />
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the copilot…"
            style={{ flex: 1, minWidth: 280, padding: 10, borderRadius: 12, border: "1px solid #e5e7eb" }}
            onKeyDown={(e) => {
              if (e.key === "Enter") send();
            }}
          />
          {canVoice && (
            <button
              onClick={startVoice}
              style={{
                padding: "10px 12px",
                borderRadius: 12,
                border: "1px solid #e5e7eb",
                background: listening ? "#111827" : "#fff",
                color: listening ? "#fff" : "#111827",
              }}
              title={listening ? "Listening…" : "Voice input"}
            >
              🎙️
            </button>
          )}
          <button
            onClick={send}
            disabled={loading}
            style={{
              padding: "10px 14px",
              borderRadius: 12,
              border: "1px solid #111827",
              background: "#111827",
              color: "#fff",
              cursor: "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            Send
          </button>
        </div>

        <div style={{ marginTop: 10, opacity: 0.7, fontSize: 12 }}>
          Try: “Which items will stock out in CA_1 in the next 7 days?” • “Suggest markdowns to reduce excess inventory.”
        </div>
      </div>

      {/* RIGHT: Panels */}
      <div>
        <h3 style={{ marginTop: 0 }}>Decision panels</h3>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <KPI title="WAPE (validation)" value={km?.forecast_valid_wape ?? summary?.forecast_valid_wape ?? "—"} />
          <KPI title="RMSE (validation)" value={km?.forecast_valid_rmse ?? summary?.forecast_valid_rmse ?? "—"} />
          <KPI
            title="Stockouts (before → after)"
            value={
              (km?.stockout_units_before ?? summary?.inventory_before?.stockout_units) != null &&
              (km?.stockout_units_after ?? summary?.inventory_after?.stockout_units) != null
              ? `${Math.round(km?.stockout_units_before ?? summary.inventory_before.stockout_units)} → ${Math.round(
                km?.stockout_units_after ?? summary.inventory_after.stockout_units
                )}`
              : "—"
            }
          />

          <KPI
            title="Cost proxy (before → after)"
            value={
              (km?.total_cost_before ?? summary?.inventory_before?.total_cost) != null &&
              (km?.total_cost_after ?? summary?.inventory_after?.total_cost) != null
                ? `${Math.round(km?.total_cost_before ?? summary.inventory_before.total_cost)} → ${Math.round(
                    km?.total_cost_after ?? summary.inventory_after.total_cost
                  )}`
                : "—"
            }
          />
        </div>

        <div style={{ marginTop: 12, padding: 12, border: "1px solid #e5e7eb", borderRadius: 16 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>Decision</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
            {(agent?.decisions || []).slice(0, 6).map((d: string, i: number) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>Inventory actions (Top 10)</div>
          <SimpleTable rows={inv} />
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>Pricing actions (Top 10)</div>
          <SimpleTable rows={prc} />
        </div>

        <div style={{ marginTop: 12, padding: 12, border: "1px solid #e5e7eb", borderRadius: 16 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>Tool trace</div>
          <pre style={{ margin: 0, fontSize: 12, whiteSpace: "pre-wrap" }}>
            {JSON.stringify(agent?.tool_calls || [], null, 2)}
          </pre>
        </div>

        <div style={{ marginTop: 12, padding: 12, border: "1px solid #e5e7eb", borderRadius: 16 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>Downloads</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 13 }}>
            {agent?.downloads
              ? Object.entries(agent.downloads).map(([k, v]: any) => (
                  <a key={k} href={downloadsUrl(String(v))} target="_blank" rel="noreferrer">
                    {k}
                  </a>
                ))
              : "Run the agent to populate links."}
          </div>
        </div>
      </div>
    </div>
  );
}
