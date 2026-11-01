import { ShieldCheck, Sparkles, Target } from "lucide-react";
import Workspace from "@/components/Workspace";

export default function Home() {
  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
      <header className="rounded-3xl bg-gradient-to-br from-navy to-teal px-8 py-10 text-white shadow-card">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">
          <Target className="h-3.5 w-3.5" /> Projet NLP · Next.js + FastAPI
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">MeetMind</h1>
        <p className="mt-3 max-w-2xl text-lg opacity-95">
          De la transcription au compte rendu : résumé, décisions et actions avec responsable et échéance.
          Chaque élément est relié à sa source.
        </p>
        <div className="mt-5 flex flex-wrap gap-4 text-sm opacity-95">
          <span className="inline-flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Sources vérifiées automatiquement</span>
          <span className="inline-flex items-center gap-2"><Sparkles className="h-4 w-4" /> Claude ou mode hors-ligne</span>
        </div>
      </header>
      <Workspace />
      <footer className="pb-6 text-center text-xs text-slate-500">
        MeetMind · ERRACHDI Chaimae · Relecture humaine recommandée avant diffusion.
      </footer>
    </main>
  );
}
