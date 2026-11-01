"""Pipeline d'extraction par LLM : map (par bloc) -> reduce (fusion) -> dates -> vérification."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable, Optional

from pydantic import ValidationError

from .chunking import chunk_segments
from .dates import resolve_deadline
from .llm import LLMClient, call_json
from .parsing import participants_from, render
from .schemas import Action, CompteRendu, Decision, Segment
from .textutils import similarity
from .verify import verify_report

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
Progress = Optional[Callable[[int, int, str], None]]


def _load(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def _build(data: dict) -> CompteRendu:
    """Construit un CompteRendu en ignorant les éléments invalides (validation Pydantic tolérante)."""
    def many(cls, key):
        out = []
        for raw in data.get(key) or []:
            try:
                out.append(cls.model_validate(raw))
            except ValidationError:
                continue
        return out

    def strings(key):
        return [str(x) for x in (data.get(key) or []) if x]

    return CompteRendu(
        titre=data.get("titre") or "Compte rendu de réunion",
        resume_executif=data.get("resume_executif") or "",
        participants=strings("participants"),
        points_cles=strings("points_cles"),
        decisions=many(Decision, "decisions"),
        actions=many(Action, "actions"),
        questions_ouvertes=strings("questions_ouvertes"),
    )


def _dedupe_strings(items: list[str], thr: float = 0.7) -> list[str]:
    out: list[str] = []
    for it in items:
        if not any(similarity(it, o) >= thr for o in out):
            out.append(it)
    return out


def merge_reports(parts: list[CompteRendu], thr: float = 0.6) -> CompteRendu:
    """Étape « reduce » : fusionne et dédoublonne les résultats des blocs."""
    merged = CompteRendu(titre=parts[0].titre, resume_executif=parts[0].resume_executif)
    for p in parts:
        for d in p.decisions:
            if not any(similarity(d.decision, e.decision) >= thr for e in merged.decisions):
                merged.decisions.append(d)
        for a in p.actions:
            dup = next((e for e in merged.actions if similarity(a.description, e.description) >= thr), None)
            if dup is None:
                merged.actions.append(a)
            else:  # complète les champs manquants de l'existante
                dup.responsable = dup.responsable or a.responsable
                dup.echeance_texte = dup.echeance_texte or a.echeance_texte
        merged.participants += p.participants
        merged.points_cles += p.points_cles
        merged.questions_ouvertes += p.questions_ouvertes
    merged.participants = list(dict.fromkeys(merged.participants))
    merged.points_cles = _dedupe_strings(merged.points_cles)
    merged.questions_ouvertes = _dedupe_strings(merged.questions_ouvertes)
    return merged


def finalize(cr: CompteRendu, segments: list[Segment], meeting_date: Optional[date]) -> CompteRendu:
    """Calcule les dates, complète les participants et vérifie les citations."""
    cr.participants = list(dict.fromkeys([*participants_from(segments), *cr.participants]))
    if meeting_date:
        cr.date_reunion = meeting_date.isoformat()
        for a in cr.actions:
            a.echeance = resolve_deadline(a.echeance_texte, meeting_date)
    return verify_report(cr, segments)


class MeetingExtractor:
    def __init__(self, llm: LLMClient, max_words: int = 3000):
        self.llm = llm
        self.max_words = max_words
        self.system = _load("extraction.md")

    def run(self, segments: list[Segment], meeting_date: Optional[date] = None, progress: Progress = None) -> CompteRendu:
        chunks = chunk_segments(segments, self.max_words)
        known = ", ".join(participants_from(segments)) or "inconnus"
        parts: list[CompteRendu] = []
        total = len(chunks) + (1 if len(chunks) > 1 else 0)
        for i, chunk in enumerate(chunks, 1):
            if progress:
                progress(i, total, f"Analyse du bloc {i}/{len(chunks)}…")
            user = (
                f"Date de la réunion : {meeting_date.isoformat() if meeting_date else 'inconnue'}\n"
                f"Participants connus : {known}\n\nTRANSCRIPTION :\n{render(chunk)}"
            )
            parts.append(_build(call_json(self.llm, self.system, user)))

        if len(parts) == 1:
            cr = parts[0]
        else:
            if progress:
                progress(total, total, "Fusion des résultats…")
            cr = merge_reports(parts)
            digest = "\n\n".join(f"BLOC {i}\nRésumé : {p.resume_executif}\nPoints : {p.points_cles}" for i, p in enumerate(parts, 1))
            try:
                syn = call_json(self.llm, _load("merge.md"), digest, max_tokens=1500)
                cr.titre = syn.get("titre") or cr.titre
                cr.resume_executif = syn.get("resume_executif") or cr.resume_executif
                cr.points_cles = [str(x) for x in syn.get("points_cles") or cr.points_cles]
            except RuntimeError:
                pass  # on garde le résumé du premier bloc
        return finalize(cr, segments, meeting_date)
