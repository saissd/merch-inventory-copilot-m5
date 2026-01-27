import { useEffect, useMemo, useState } from "react";
import { chatAgent } from "../api/client";
import type { ChatMsg, WhatIf } from "../types";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";

function uuid() {
  return crypto.randomUUID();
}

const LS_CONV = "conv_id";
const LS_MSGS = "chat_msgs";

export default function ChatShell() {
  const [storeId, setStoreId] = useState("CA_1");

  const [conversationId, setConversationId] = useState(() => {
    return localStorage.getItem(LS_CONV) || uuid();
  });

  const [messages, setMessages] = useState<ChatMsg[]>(() => {
    const raw = localStorage.getItem(LS_MSGS);
    try {
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [whatIf, setWhatIf] = useState<WhatIf>({
    service_level: 0.95,
    lead_time_days: 7,
    holding_cost_per_unit: 0.1,
    stockout_penalty_per_unit: 1.0,
  });

  // Persist
  useEffect(() => {
    localStorage.setItem(LS_CONV, conversationId);
    localStorage.setItem(LS_MSGS, JSON.stringify(messages));
  }, [conversationId, messages]);

  // Backend-friendly history
  const history = useMemo(
    () => messages.map((m) => ({ role: m.role, content: m.text })),
    [messages]
  );

  async function onSend() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMsg = { role: "user", text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const payload = {
        message: text,
        store_id: storeId,
        conversation_id: conversationId,
        history,
        whatif: whatIf,
      };

      const res: any = await chatAgent(payload);

      const assistantText =
        res?.memo ||
        res?.explanation ||
        res?.response ||
        JSON.stringify(res, null, 2);

      const assistantMsg: ChatMsg = { role: "assistant", text: assistantText, ts: Date.now() };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      const errText = e?.message ? String(e.message) : String(e);
      const errMsg: ChatMsg = { role: "assistant", text: `Error: ${errText}`, ts: Date.now() };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  function newChat() {
    setConversationId(uuid());
    setMessages([]);
    setInput("");
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      <header className="border-b">
        <div className="max-w-5xl mx-auto p-3 flex items-center gap-3">
          <div className="font-semibold">Merch & Inventory Copilot (M5 Demo)</div>
          <div className="ml-auto flex items-center gap-2">
            <select
              value={storeId}
              onChange={(e) => setStoreId(e.target.value)}
              className="border rounded-xl px-3 py-2"
            >
              <option value="CA_1">CA_1</option>
              <option value="CA_2">CA_2</option>
              <option value="TX_1">TX_1</option>
              <option value="WI_1">WI_1</option>
            </select>

            <button onClick={newChat} className="border rounded-xl px-3 py-2">
              New chat
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-gray-500 border rounded-2xl p-4">
              Try: “What should I order today for CA_1? Include order_qty and days_of_supply.”
            </div>
          )}

          {messages.map((m, idx) => (
            <MessageBubble key={idx} msg={m} />
          ))}

          {loading && <div className="text-gray-500">Thinking…</div>}
        </div>
      </main>

      {/* What-if mini panel */}
      <div className="border-t bg-gray-50">
        <div className="max-w-3xl mx-auto p-3 flex flex-wrap gap-3 items-center">
          <div className="text-sm font-medium">What-if</div>

          <label className="text-sm">
            Service:
            <select
              className="ml-2 border rounded-xl px-2 py-1"
              value={whatIf.service_level}
              onChange={(e) => setWhatIf({ ...whatIf, service_level: Number(e.target.value) })}
            >
              <option value={0.9}>0.90</option>
              <option value={0.95}>0.95</option>
              <option value={0.98}>0.98</option>
            </select>
          </label>

          <label className="text-sm">
            Lead time:
            <input
              className="ml-2 w-20 border rounded-xl px-2 py-1"
              type="number"
              value={whatIf.lead_time_days}
              onChange={(e) => setWhatIf({ ...whatIf, lead_time_days: Number(e.target.value) })}
            />
          </label>

          <label className="text-sm">
            Holding:
            <input
              className="ml-2 w-24 border rounded-xl px-2 py-1"
              type="number"
              step="0.01"
              value={whatIf.holding_cost_per_unit}
              onChange={(e) => setWhatIf({ ...whatIf, holding_cost_per_unit: Number(e.target.value) })}
            />
          </label>

          <label className="text-sm">
            Stockout:
            <input
              className="ml-2 w-24 border rounded-xl px-2 py-1"
              type="number"
              step="0.01"
              value={whatIf.stockout_penalty_per_unit}
              onChange={(e) => setWhatIf({ ...whatIf, stockout_penalty_per_unit: Number(e.target.value) })}
            />
          </label>
        </div>
      </div>

      <Composer value={input} setValue={setInput} onSend={onSend} disabled={loading} />
    </div>
  );
}
