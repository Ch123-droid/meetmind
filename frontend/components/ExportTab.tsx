"use client";

import { CalendarPlus, Copy, FileJson, FileText, Mail, FileType2 } from "lucide-react";
import { useEffect, useState } from "react";
import { downloadExport, exportEmail } from "@/lib/api";
import type { EmailDraft, ExportFormat, Report } from "@/lib/types";
import { Spinner } from "./ui";

const BUTTONS: { fmt: ExportFormat; label: string; icon: React.ReactNode }[] = [
  { fmt: "docx", label: "Word (.docx)", icon: <FileType2 className="h-4 w-4" /> },
  { fmt: "md", label: "Markdown", icon: <FileText className="h-4 w-4" /> },
  { fmt: "ics", label: "Calendrier (.ics)", icon: <CalendarPlus className="h-4 w-4" /> },
  { fmt: "json", label: "JSON", icon: <FileJson className="h-4 w-4" /> },
];

export default function ExportTab({ report }: { report: Report }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [mail, setMail] = useState<EmailDraft | null>(null);

  useEffect(() => {
    exportEmail(report).then(setMail).catch((e: Error) => setError(e.message));
  }, [report]);

  async function dl(fmt: ExportFormat) {
    setBusy(fmt); setError("");
    try { await downloadExport(fmt, report, "compte_rendu_meetmind"); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(null); }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {BUTTONS.map((b) => (
          <button key={b.fmt} className="btn-ghost" disabled={busy !== null} onClick={() => dl(b.fmt)}>
            {busy === b.fmt ? <Spinner /> : b.icon} {b.label}
          </button>
        ))}
      </div>
      {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-200">{error}</p>}
      {mail && (
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-bold text-navy dark:text-teal"><Mail className="h-4 w-4" /> E-mail de suivi</h3>
          <input className="input" readOnly value={mail.subject} aria-label="Objet" />
          <textarea className="input h-72 font-mono text-xs" readOnly value={mail.body} aria-label="Corps du message" />
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={() => navigator.clipboard.writeText(`${mail.subject}\n\n${mail.body}`)}><Copy className="h-4 w-4" /> Copier</button>
            <a className="btn-primary" href={`mailto:?subject=${encodeURIComponent(mail.subject)}&body=${encodeURIComponent(mail.body)}`}><Mail className="h-4 w-4" /> Ouvrir dans la messagerie</a>
          </div>
        </div>
      )}
    </div>
  );
}
