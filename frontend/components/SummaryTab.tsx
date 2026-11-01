import { HelpCircle, Users } from "lucide-react";
import type { Report } from "@/lib/types";

export default function SummaryTab({ report, onChange }: { report: Report; onChange: (r: Report) => void }) {
  return (
    <div className="space-y-5">
      <div>
        <label className="mb-1 block text-xs font-semibold text-slate-500">Titre</label>
        <input className="input text-base font-semibold" value={report.titre} onChange={(e) => onChange({ ...report, titre: e.target.value })} />
      </div>
      <div>
        <label className="mb-1 block text-xs font-semibold text-slate-500">Résumé exécutif</label>
        <textarea className="input h-32" value={report.resume_executif} onChange={(e) => onChange({ ...report, resume_executif: e.target.value })} />
      </div>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Users className="h-4 w-4 text-teal" />
        {report.participants.length ? report.participants.map((n) => (
          <span key={n} className="rounded-full bg-navy-50 px-3 py-1 text-xs font-semibold text-navy dark:bg-slate-800 dark:text-slate-100">{n}</span>
        )) : <span className="text-slate-500">Participants non identifiés</span>}
      </div>
      {report.points_cles.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-bold text-navy dark:text-teal">Points clés</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">{report.points_cles.map((p, i) => <li key={i}>{p}</li>)}</ul>
        </div>
      )}
      {report.questions_ouvertes.length > 0 && (
        <div className="rounded-xl bg-amber-50 p-4 dark:bg-amber-950/40">
          <h3 className="mb-2 flex items-center gap-2 text-sm font-bold text-amber-800 dark:text-amber-200"><HelpCircle className="h-4 w-4" /> Questions ouvertes</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">{report.questions_ouvertes.map((q, i) => <li key={i}>{q}</li>)}</ul>
        </div>
      )}
    </div>
  );
}
