"""« Discuter avec la réunion » : récupération d'extraits + réponse du LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .llm import LLMClient
from .schemas import Segment
from .textutils import tokens

QA_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "qa.md"


def retrieve(question: str, segments: list[Segment], k: int = 6) -> list[Segment]:
    """Sélection lexicale des k segments les plus proches (suffisant pour une réunion ; RAG vectoriel en option)."""
    q = tokens(question)
    scored = []
    for i, seg in enumerate(segments):
        t = tokens(seg.text + " " + (seg.speaker or ""))
        score = len(q & t) / (len(q) or 1)
        if score > 0:
            scored.append((score, i))
    top = sorted(scored, reverse=True)[:k]
    return [segments[i] for _, i in sorted(top, key=lambda x: x[1])]


def answer(question: str, segments: list[Segment], llm: Optional[LLMClient] = None) -> tuple[str, list[Segment]]:
    hits = retrieve(question, segments)
    if not hits:
        return "Cette information n'apparaît pas dans la réunion.", []
    if llm is None:
        return "Extraits les plus pertinents (mode hors-ligne, sans génération) :", hits
    context = "\n".join(s.render() for s in hits)
    reply = llm.complete(QA_PROMPT.read_text(encoding="utf-8"), f"EXTRAITS :\n{context}\n\nQUESTION : {question}", max_tokens=600)
    return reply.strip(), hits
