import { Plus, Search, Trash2 } from "lucide-react";
import type { Action, Priority, Report } from "@/lib/types";
import { Empty, VerifiedBadge } from "./ui";

const EMPTY: Action = {
  description: "", responsable: null, echeance_texte: null, echeance: null, priorite: "moyenne",
  source_citation: "", horodatage: null, segment_index: null, verifie: true,
};

export default function ActionsTab({ report, onChange, onSource }: { report: Report; onChange: (r: Report) => void; onSource: (idx: number | null) => void }) {
  const update = (i: number, patch: Partial<Action>) =>
    onChange({ ...report, actions: report.actions.map((a, j) => (j === i ? { ...a, ...patch } : a)) });
  const remove = (i: number) => onChange({ ...report, actions: report.actions.filter((_, j) => j !== i) });
  const add = () => onChange({ ...report, actions: [...report.actions, { ...EMPTY }] });

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">Tout est modifiable : vos corrections sont reprises dans les exports.</p>
      {!report.actions.length && <Empty>Aucune action identifiée.</Empty>}
      {report.actions.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="w-full min-w-[820px] text-sm">
            <thead className="bg-navy text-left text-xs text-white">
              <tr>
                <th className="px-3 py-2">Action</th><th className="px-3 py-2">Responsable</th>
                <th className="px-3 py-2">Échéance</th><th className="px-3 py-2">Priorité</th>
                <th className="px-3 py-2">Source</th><th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {report.actions.map((a, i) => (
                <tr key={i} className="border-t border-slate-200 align-top dark:border-slate-800">
                  <td className="px-3 py-2"><textarea rows={2} className="input" value={a.description} onChange={(e) => update(i, { description: e.target.value })} aria-label="Description de l'action" /></td>
                  <td className="px-3 py-2"><input className="input" value={a.responsable ?? ""} placeholder="—" onChange={(e) => update(i, { responsable: e.target.value || null })} aria-label="Responsable" /></td>
                  <td className="px-3 py-2">
                    <input type="date" className="input" value={a.echeance ?? ""} onChange={(e) => update(i, { echeance: e.target.value || null })} aria-label="Échéance" />
                    {a.echeance_texte && <p className="mt-1 text-[11px] text-slate-500">dit : « {a.echeance_texte} »</p>}
                  </td>
                  <td className="px-3 py-2">
                    <select className="input" value={a.priorite} onChange={(e) => update(i, { priorite: e.target.value as Priority })} aria-label="Priorité">
                      <option value="haute">haute</option><option value="moyenne">moyenne</option><option value="basse">basse</option>
                    </select>
                  </td>
                  <td className="space-y-1 px-3 py-2">
                    <VerifiedBadge ok={a.verifie} />
                    {a.segment_index !== null && (
                      <button className="flex items-center gap-1 text-xs font-semibold text-teal hover:underline" onClick={() => onSource(a.segment_index)}>
                        <Search className="h-3 w-3" /> {a.horodatage ?? "source"}
                      </button>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <button className="rounded p-1.5 text-slate-500 hover:bg-red-50 hover:text-red-600" onClick={() => remove(i)} aria-label="Supprimer l'action"><Trash2 className="h-4 w-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <button className="btn-ghost" onClick={add}><Plus className="h-4 w-4" /> Ajouter une action</button>
    </div>
  );
}
