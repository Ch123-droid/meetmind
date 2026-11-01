"use client";

import { AlertTriangle, BookOpen, CheckSquare, Download, ListChecks, MessageCircle, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { analyze, getHealth, getSample, transcribeAudio } from "@/lib/api";
import type { Health, Mode, Report, Segment } from "@/lib/types";
import ActionsTab from "./ActionsTab";
import ChatTab from "./ChatTab";
import DecisionsTab from "./DecisionsTab";
import ExportTab from "./ExportTab";
import SourcesTab from "./SourcesTab";
import SummaryTab from "./SummaryTab";
import UploadPanel from "./UploadPanel";
import { Kpi } from "./ui";

const TABS = [
  { id: "summary", label: "Résumé", icon: BookOpen },
  { id: "decisions", label: "Décisions", icon: CheckSquare },
  { id: "actions", label: "Actions", icon: ListChecks },
  { id: "sources", label: "Sources", icon: Search },
  { id: "chat", label: "Chat", icon: MessageCircle },
  { id: "export", label: "Exports", icon: Download },
] as const;
type TabId = (typeof TABS)[number]["id"];

const AUDIO = /\.(mp3|wav|m4a)$/i;
const today = () => new Date().toISOString().slice(0, 10);

export default function Workspace() {
  const [health, setHealth] = useState<Health | null>(null);
  const [mode, setMode] = useState<Mode>("offline");
  const [date, setDate] = useState(today());
  const [text, setText] = useState("");
  const [fileName, setFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [tab, setTab] = useState<TabId>("summary");
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    getHealth()
      .then((h) => { setHealth(h); if (h.claude_available) setMode("claude"); })
      .catch((e: Error) => setError(e.message));
  }, []);

  const run = useCallback(async (content: string, name: string, d: string, m: Mode) => {
    setLoading(true); setError(""); setStatus(m === "claude" ? "Analyse par Claude en cours…" : "Analyse en cours…");
    try {
      const r = await analyze({ text: content, filename: name, mode: m, meeting_date: d || null });
      setReport(r.report); setSegments(r.segments); setSelected(null); setTab("summary");
      setStatus(`Terminé en ${r.elapsed_seconds} s`);
    } catch (e) {
      setError((e as Error).message); setStatus("");
    } finally {
      setLoading(false);
    }
  }, []);

  async function onFile(f: File) {
    setError(""); setFileName(f.name);
    if (AUDIO.test(f.name)) {
      setLoading(true); setStatus("Transcription audio en cours (peut être longue)…");
      try { setText(await transcribeAudio(f)); setStatus("Audio transcrit : vérifiez le texte puis lancez l'analyse."); }
      catch (e) { setError((e as Error).message); setStatus(""); }
      finally { setLoading(false); }
      return;
    }
    setText(await f.text()); setStatus("");
  }

  async function onSample() {
    try {
      const s = await getSample();
      setText(s.text); setFileName(s.filename); setDate(s.meeting_date);
      await run(s.text, s.filename, s.meeting_date, mode);
    } catch (e) { setError((e as Error).message); }
  }

  const goSource = (idx: number | null) => { setSelected(idx); setTab("sources"); };
  const fidelity = report ? Math.round(([...report.decisions, ...report.actions].length
    ? [...report.decisions, ...report.actions].filter((i) => i.verifie).length / [...report.decisions, ...report.actions].length
    : 1) * 100) : 0;

  return (
    <div className="space-y-6">
      <UploadPanel health={health} mode={mode} setMode={setMode} date={date} setDate={setDate} text={text} setText={setText}
        fileName={fileName} onFile={onFile} onSample={onSample} onAnalyze={() => run(text, fileName, date, mode)} loading={loading} status={status} />

      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {report && (
        <section className="space-y-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Kpi value={report.participants.length} label="participants" />
            <Kpi value={report.decisions.length} label="décisions" />
            <Kpi value={report.actions.length} label="actions" />
            <Kpi value={`${fidelity} %`} label="sources vérifiées" />
          </div>
          <div className="card !p-0">
            <div role="tablist" className="flex overflow-x-auto border-b border-slate-200 px-2 dark:border-slate-800">
              {TABS.map(({ id, label, icon: Icon }) => (
                <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
                  className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-semibold transition ${
                    tab === id ? "border-teal text-teal" : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-100"
                  }`}>
                  <Icon className="h-4 w-4" /> {label}
                </button>
              ))}
            </div>
            <div className="p-5" role="tabpanel">
              {tab === "summary" && <SummaryTab report={report} onChange={setReport} />}
              {tab === "decisions" && <DecisionsTab report={report} onSource={goSource} />}
              {tab === "actions" && <ActionsTab report={report} onChange={setReport} onSource={goSource} />}
              {tab === "sources" && <SourcesTab report={report} segments={segments} selected={selected} onSelect={setSelected} />}
              {tab === "chat" && <ChatTab segments={segments} mode={mode} />}
              {tab === "export" && <ExportTab report={report} />}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
