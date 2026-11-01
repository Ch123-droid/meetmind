import { Loader2 } from "lucide-react";
import type { Priority } from "@/lib/types";

export function Spinner({ className = "" }: { className?: string }) {
  return <Loader2 className={`h-4 w-4 animate-spin ${className}`} aria-hidden />;
}

export function Kpi({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="rounded-xl border-l-4 border-teal bg-navy-50 px-4 py-3 text-navy dark:bg-slate-900 dark:text-slate-100">
      <div className="text-3xl font-bold leading-none">{value}</div>
      <div className="mt-1 text-xs opacity-75">{label}</div>
    </div>
  );
}

const PRIO: Record<Priority, string> = {
  haute: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200",
  moyenne: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
  basse: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
};

export function PriorityBadge({ p }: { p: Priority }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${PRIO[p]}`}>{p}</span>;
}

export function VerifiedBadge({ ok }: { ok: boolean }) {
  return ok ? (
    <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
      source vérifiée
    </span>
  ) : (
    <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-950 dark:text-amber-200">
      à vérifier
    </span>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-slate-700">{children}</p>;
}
