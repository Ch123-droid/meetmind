import { Clock, Search } from "lucide-react";
import type { Report } from "@/lib/types";
import { Empty, VerifiedBadge } from "./ui";

export default function DecisionsTab({ report, onSource }: { report: Report; onSource: (idx: number | null) => void }) {
  if (!report.decisions.length) return <Empty>Aucune décision identifiée dans cette réunion.</Empty>;
  return (
    <ul className="space-y-3">
      {report.decisions.map((d, i) => (
        <li key={i} className={`rounded-xl border border-l-4 p-4 ${d.verifie ? "border-slate-200 border-l-teal dark:border-slate-800" : "border-amber-300 border-l-accent"}`}>
          <p className="font-semibold">{d.decision}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <VerifiedBadge ok={d.verifie} />
            {d.horodatage && (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold dark:bg-slate-800">
                <Clock className="h-3 w-3" /> {d.horodatage}
              </span>
            )}
            {d.segment_index !== null && (
              <button className="inline-flex items-center gap-1 text-xs font-semibold text-teal hover:underline" onClick={() => onSource(d.segment_index)}>
                <Search className="h-3 w-3" /> Voir la source
              </button>
            )}
          </div>
          {d.source_citation && <p className="mt-2 text-sm italic text-slate-500">« {d.source_citation} »</p>}
        </li>
      ))}
    </ul>
  );
}
