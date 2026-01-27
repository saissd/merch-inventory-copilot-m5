import VoiceButton from "./VoiceButton";

export default function Composer({
  value,
  setValue,
  onSend,
  disabled,
}: {
  value: string;
  setValue: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="w-full border-t bg-white p-3">
      <div className="flex gap-2 items-end max-w-3xl mx-auto">
        <div className="flex-1 border rounded-2xl p-3">
          <textarea
            className="w-full resize-none outline-none"
            rows={2}
            placeholder="Ask about inventory, pricing, or what-if scenarios…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
          />
        </div>
        <VoiceButton onText={(t) => setValue(t)} />
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="px-4 py-3 rounded-2xl bg-black text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
