"""Découpage des longues réunions en blocs (étape « map »)."""
from __future__ import annotations

from .schemas import Segment


def chunk_segments(segments: list[Segment], max_words: int = 3000, overlap: int = 3) -> list[list[Segment]]:
    """Découpe sur des frontières de prises de parole, avec chevauchement de `overlap` segments."""
    chunks: list[list[Segment]] = []
    cur: list[Segment] = []
    words = 0
    for seg in segments:
        w = len(seg.text.split())
        if cur and words + w > max_words:
            chunks.append(cur)
            cur = cur[-overlap:] if overlap else []
            words = sum(len(s.text.split()) for s in cur)
        cur.append(seg)
        words += w
    if cur:
        chunks.append(cur)
    return chunks
