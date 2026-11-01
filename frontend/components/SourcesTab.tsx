import { useEffect, useRef } from "react";
import type { Report, Segment } from "@/lib/types";

interface Props {
  report: Report;
  segments: Segment[];
  selected: number | null;
  onSelect: (idx: number | null) => void;
}

export default function SourcesTab({ report, segments, selected, onSelect }: Props) {
  const markRef = useRef<HTMLParagraphElement>(null);
  useEffect(() => { markRef.current?.scrollIntoView({ block: "center", behavior: "smooth" }); }, [selected]);

  const items = [
    ...report.decisions.map((d) => ({ label: `Décision · ${d.decision}`, idx: d.segment_index })),
    ...report.actions.map((a) => ({ label: `Action · ${a.description}`, idx: a.segment_index })),
  ].filter((i) => i.idx !== null);

  return (
    <div className="space-y-3">
      <select className="input" value={selected ?? ""} onChange={(e) => onSelect(e.target.value === "" ? null : Number(e.target.value))} aria-label="Choisir un élément">
        <option value="">— Voir la source de… —</option>
        {items.map((it, k) => <option key={k} value={it.idx as number}>{it.label}</option>)}
      </select>
      <div className="max-h-[480px] space-y-1 overflow-y-auto rounded-xl border border-slate-200 p-3 text-sm leading-relaxed dark:border-slate-800">
        {segments.map((s, i) => (
          <p key={i} ref={i === selected ? markRef : undefined}
            className={`rounded px-2 py-1 ${i === selected ? "bg-yellow-200 text-slate-900" : ""}`}>
            {s.timestamp && <span className="mr-2 text-xs opacity-60">{s.timestamp}</span>}
            {s.speaker && <span className="mr-1 font-bold text-teal">{s.speaker}</span>}
            {s.text}
          </p>
        ))}
      </div>
    </div>
  );
}
