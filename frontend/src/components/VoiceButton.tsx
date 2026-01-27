import { useEffect, useRef, useState } from "react";

type Props = { onText: (t: string) => void };

export default function VoiceButton({ onText }: Props) {
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const recogRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }
    const recog = new SpeechRecognition();
    recog.lang = "en-US";
    recog.interimResults = true;
    recog.continuous = false;

    recog.onresult = (e: any) => {
      const transcript = Array.from(e.results).map((r: any) => r[0].transcript).join("");
      onText(transcript);
    };
    recog.onend = () => setListening(false);
    recog.onerror = () => setListening(false);
    recogRef.current = recog;
  }, [onText]);

  if (!supported) return <button className="opacity-50 cursor-not-allowed px-3 py-2 rounded-xl border">🎙️</button>;

  const toggle = () => {
    if (!recogRef.current) return;
    if (listening) {
      recogRef.current.stop();
      setListening(false);
    } else {
      setListening(true);
      recogRef.current.start();
    }
  };

  return (
    <button
      onClick={toggle}
      className={`px-3 py-2 rounded-xl border ${listening ? "bg-black text-white" : "bg-white"}`}
      title={listening ? "Listening..." : "Voice input"}
    >
      🎙️
    </button>
  );
}
