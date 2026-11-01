"""Vérification anti-hallucination : chaque citation doit exister dans la transcription."""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Optional

from .schemas import CompteRendu, Segment
from .textutils import normalize

try:  # accélération facultative
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover
    fuzz = None

THRESHOLD = 0.85


def citation_score(citation: str, haystack_norm: str) -> float:
    """Score 0..1 de présence de la citation dans la transcription normalisée."""
    c = normalize(citation)
    if not c:
        return 0.0
    if c in haystack_norm:
        return 1.0
    if fuzz is not None:
        return fuzz.partial_ratio(c, haystack_norm) / 100
    sm = SequenceMatcher(None, c, haystack_norm, autojunk=False)
    return sm.find_longest_match(0, len(c), 0, len(haystack_norm)).size / len(c)


def locate(citation: str, segments: list[Segment]) -> Optional[int]:
    """Indice du segment le plus proche de la citation (pour surligner la source)."""
    c = normalize(citation)
    if not c:
        return None
    best, best_i = 0.0, None
    for i, seg in enumerate(segments):
        s = normalize(seg.text)
        if c in s or (len(s) > 12 and s in c):
            return i
        score = fuzz.partial_ratio(c, s) / 100 if fuzz else SequenceMatcher(None, c, s).ratio()
        if score > best:
            best, best_i = score, i
    return best_i if best >= 0.6 else None


def verify_report(cr: CompteRendu, segments: list[Segment]) -> CompteRendu:
    """Marque `verifie` et renseigne l'horodatage de chaque décision / action."""
    hay = normalize(" ".join(s.text for s in segments))
    for item in [*cr.decisions, *cr.actions]:
        item.verifie = citation_score(item.source_citation, hay) >= THRESHOLD
        idx = locate(item.source_citation, segments) if item.source_citation else None
        item.segment_index = idx
        if idx is not None and segments[idx].timestamp:
            item.horodatage = segments[idx].timestamp
    return cr
