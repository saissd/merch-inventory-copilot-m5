export type Role = "user" | "assistant";

export type ChatMsg = {
  role: Role;
  text: string;
  ts: number;
};

export type WhatIf = {
  service_level: number;
  lead_time_days: number;
  holding_cost_per_unit: number;
  stockout_penalty_per_unit: number;
};

export type AgentChatPayload = {
  message: string;
  store_id?: string | null;
  item_id?: string | null;

  // optional (safe to send even if backend ignores for now)
  conversation_id?: string;
  history?: { role: Role; content: string }[];
  prefs?: { objective?: "cost" | "service" };
  whatif?: WhatIf;
};
