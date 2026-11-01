"""Lecture des transcriptions : .txt, .vtt, .srt."""
from __future__ import annotations

import re
from typing import Optional

from .schemas import Segment

_TS = r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?"
_RE_CUE = re.compile(rf"^\s*{_TS}\s*-->\s*{_TS}")
_RE_BRACKET_TS = re.compile(rf"^\s*[\[(]?{_TS}[\])]?\s*[-–]?\s*")
_RE_SPEAKER = re.compile(r"^([A-ZÀ-ÖØ-Þ][\w'’À-ÿ\- ]{0,40}?)\s*:\s+(.*)$")
_RE_VTT_V = re.compile(r"<v\s+([^>]+)>(.*?)(?:</v>)?$")


def _secs(h, m, s, ms=None) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + (int(ms.ljust(3, "0")) / 1000 if ms else 0)


def _split_speaker(text: str) -> tuple[Optional[str], str]:
    m = _RE_VTT_V.match(text)
    if m:
        return m.group(1).strip(), re.sub(r"<[^>]+>", "", m.group(2)).strip()
    m = _RE_SPEAKER.match(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, re.sub(r"<[^>]+>", "", text).strip()


def parse_cues(raw: str) -> list[Segment]:
    """VTT / SRT."""
    segments: list[Segment] = []
    start: Optional[float] = None
    buf: list[str] = []

    def flush():
        nonlocal buf, start
        if start is not None and buf:
            speaker, text = _split_speaker(" ".join(buf))
            if text:
                segments.append(Segment(text=text, speaker=speaker, start=start))
        buf, start = [], None

    for line in raw.splitlines():
        m = _RE_CUE.match(line)
        if m:
            flush()
            start = _secs(*m.groups()[:4])
        elif start is not None:
            if line.strip():
                buf.append(line.strip())
            else:
                flush()
        # lignes d'index SRT / en-tête WEBVTT ignorées
    flush()
    return segments


def parse_plain(raw: str) -> list[Segment]:
    """Texte brut : « [00:01:23] Sara: ... » ou « Sara: ... » ou paragraphes."""
    segments: list[Segment] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        start = None
        m = _RE_BRACKET_TS.match(line)
        if m and (line[0] in "[(" or m.group(1) is not None):
            start = _secs(*m.groups()[:4])
            line = line[m.end():]
        speaker, text = _split_speaker(line)
        if text:
            segments.append(Segment(text=text, speaker=speaker, start=start))
    return segments


def parse_transcript(raw: str, filename: str = "") -> list[Segment]:
    raw = raw.replace("\ufeff", "")
    name = filename.lower()
    if name.endswith((".vtt", ".srt")) or "-->" in raw[:2000]:
        segs = parse_cues(raw)
        if segs:
            return segs
    return parse_plain(raw)


def render(segments: list[Segment]) -> str:
    return "\n".join(s.render() for s in segments)


def participants_from(segments: list[Segment]) -> list[str]:
    seen: dict[str, None] = {}
    for s in segments:
        if s.speaker:
            seen.setdefault(s.speaker, None)
    return list(seen)
