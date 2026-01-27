import type { ChatMsg } from "../types";

export default function MessageBubble({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === "user";

  return (
    <div className={`w-full flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser ? "bg-black text-white" : "bg-gray-100 text-gray-900"
        }`}
      >
        <pre className="whitespace-pre-wrap font-sans m-0">{msg.text}</pre>
      </div>
    </div>
  );
}
