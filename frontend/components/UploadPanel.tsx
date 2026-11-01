"use client";

import { FileText, Lock, Mic, Play, Sparkles, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import type { Health, Mode } from "@/lib/types";
import { Spinner } from "./ui";

interface Props {
  health: Health | null;
  mode: Mode;
  setMode: (m: Mode) => void;
  date: string;
  setDate: (d: string) => void;
  text: string;
  setText: (t: string) => void;
  fileName: string;
  onFile: (f: File) => void;
  onSample: () => void;
  onAnalyze: () => void;
  loading: boolean;
  status: string;
}

export default function UploadPanel(p: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const claudeOk = p.health?.claude_available ?? false;

  return (
    <section className="card space-y-5">
      <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
        <div className="space-y-3">
          <div
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              const f = e.dataTransfer.files?.[0];
              if (f) p.onFile(f);
            }}
            onClick={() => inputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition ${
              drag ? "border-teal bg-teal/5" : "border-slate-300 hover:border-teal dark:border-slate-700"
            }`}
          >
            <UploadCloud className="h-8 w-8 text-teal" />
            <p className="text-sm font-medium">Glissez une transcription ou un audio, ou cliquez pour parcourir</p>
            <p className="text-xs text-slate-500">.txt · .vtt · .srt · .mp3 · .wav · .m4a</p>
            {p.fileName && (
              <p className="mt-1 inline-flex items-center gap-1 rounded-full bg-navy-50 px-3 py-1 text-xs font-semibold text-navy dark:bg-slate-800 dark:text-slate-100">
                <FileText className="h-3.5 w-3.5" /> {p.fileName}
              </p>
            )}
            <input ref={inputRef} type="file" hidden accept=".txt,.vtt,.srt,.mp3,.wav,.m4a"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) p.onFile(f); e.target.value = ""; }} />
          </div>
          <label className="block text-xs font-semibold text-slate-500">…ou collez la transcription</label>
          <textarea
            className="input h-36 resize-y font-mono text-xs"
            placeholder="[00:00:05] Sara: Bonjour à tous…"
            value={p.text}
            onChange={(e) => p.setText(e.target.value)}
          />
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-500">Moteur d&apos;analyse</label>
            <div className="grid grid-cols-2 gap-2">
              <button type="button" disabled={!claudeOk} onClick={() => p.setMode("claude")}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition disabled:cursor-not-allowed disabled:opacity-50 ${
                  p.mode === "claude" ? "border-teal bg-teal/10 font-semibold" : "border-slate-300 dark:border-slate-700"
                }`}>
                <Sparkles className="mb-1 h-4 w-4 text-teal" /> Claude
                <span className="block text-[11px] font-normal text-slate-500">{claudeOk ? "LLM (API)" : "clé API absente"}</span>
              </button>
              <button type="button" onClick={() => p.setMode("offline")}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                  p.mode === "offline" ? "border-teal bg-teal/10 font-semibold" : "border-slate-300 dark:border-slate-700"
                }`}>
                <Lock className="mb-1 h-4 w-4 text-teal" /> Hors-ligne
                <span className="block text-[11px] font-normal text-slate-500">règles, 100 % local</span>
              </button>
            </div>
          </div>
          <div>
            <label htmlFor="date" className="mb-1 block text-xs font-semibold text-slate-500">
              Date de la réunion <span className="font-normal">(pour « vendredi », « demain »…)</span>
            </label>
            <input id="date" type="date" className="input" value={p.date} onChange={(e) => p.setDate(e.target.value)} />
          </div>
          <button className="btn-primary w-full" disabled={p.loading || !p.text.trim()} onClick={p.onAnalyze}>
            {p.loading ? <Spinner /> : <Play className="h-4 w-4" />} Générer le compte rendu
          </button>
          <button className="btn-ghost w-full" disabled={p.loading} onClick={p.onSample}>
            <FileText className="h-4 w-4" /> Charger l&apos;exemple
          </button>
          {p.health && !p.health.audio_available && (
            <p className="flex items-start gap-1 text-[11px] text-slate-500">
              <Mic className="mt-0.5 h-3 w-3 shrink-0" /> Audio désactivé côté serveur (faster-whisper non installé).
            </p>
          )}
          {p.status && <p className="text-xs text-slate-500" role="status">{p.status}</p>}
        </div>
      </div>
    </section>
  );
}
