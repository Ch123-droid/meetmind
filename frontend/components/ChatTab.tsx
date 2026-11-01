"use client";

import { Send } from "lucide-react";
import { useState } from "react";
import { chat } from "@/lib/api";
import type { Mode, Segment } from "@/lib/types";
import { Spinner } from "./ui";

interface Msg { role: "user" | "assistant"; text: string; excerpts?: Segment[] }

export default function ChatTab({ segments, mode }: { segments: Segment[]; mode: Mode }) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    const question = q.trim();
    if (!question || busy) return;
    setQ("");
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setBusy(true);
    try {
      const r = await chat({ question, segments, mode });
      setMsgs((m) => [...m, { role: "assistant", text: r.answer, excerpts: r.excerpts }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", text: (e as Error).message }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">Posez une question sur la réunion, par exemple « Que pense Karim de la version mobile ? »{mode === "offline" && " (mode hors-ligne : extraits pertinents sans rédaction)"}</p>
      <div className="max-h-[420px] min-h-[120px] space-y-3 overflow-y-auto">
        {msgs.map((m, i) => (
          <div key={i} className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm ${m.role === "user" ? "ml-auto bg-teal text-white" : "bg-slate-100 dark:bg-slate-800"}`}>
            <p className="whitespace-pre-wrap">{m.text}</p>
            {m.excerpts && m.excerpts.length > 0 && (
              <ul className="mt-2 space-y-1 border-t border-slate-300/50 pt-2 text-xs opacity-90">
                {m.excerpts.map((s, k) => <li key={k}><b>{s.timestamp} {s.speaker}</b> : {s.text}</li>)}
              </ul>
            )}
          </div>
        ))}
        {busy && <Spinner className="text-teal" />}
      </div>
      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); void send(); }}>
        <input className="input" placeholder="Votre question…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Question" />
        <button className="btn-primary" disabled={busy || !q.trim()} aria-label="Envoyer"><Send className="h-4 w-4" /></button>
      </form>
    </div>
  );
}
