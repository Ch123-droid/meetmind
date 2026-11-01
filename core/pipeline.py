"""Point d'entrée unique : fichier -> CompteRendu (+ segments), en mode Claude ou hors-ligne."""
from __future__ import annotations

from datetime import date
from typing import Optional

from .extractor import MeetingExtractor
from .llm import ClaudeClient
from .offline import OfflineExtractor
from .parsing import parse_transcript
from .schemas import CompteRendu, Segment


def build_extractor(mode: str = "offline", model: Optional[str] = None):
    if mode == "claude":
        return MeetingExtractor(ClaudeClient(model=model))
    return OfflineExtractor()


def process_text(raw: str, filename: str = "", mode: str = "offline", meeting_date: Optional[date] = None,
                 model: Optional[str] = None, progress=None) -> tuple[CompteRendu, list[Segment]]:
    segments = parse_transcript(raw, filename)
    if not segments:
        raise ValueError("Transcription vide ou illisible.")
    cr = build_extractor(mode, model).run(segments, meeting_date, progress)
    return cr, segments
