"""Modèles de requêtes / réponses de l'API."""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

from core.schemas import CompteRendu

Mode = Literal["offline", "claude"]


class SegmentOut(BaseModel):
    text: str
    speaker: Optional[str] = None
    start: Optional[float] = None
    timestamp: Optional[str] = None


class SegmentIn(BaseModel):
    text: str
    speaker: Optional[str] = None
    start: Optional[float] = None


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=600_000, description="Contenu de la transcription")
    filename: str = ""
    mode: Mode = "offline"
    meeting_date: Optional[date] = None
    model: Optional[str] = None


class AnalyzeResponse(BaseModel):
    report: CompteRendu
    segments: list[SegmentOut]
    mode: Mode
    elapsed_seconds: float


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    segments: list[SegmentIn]
    mode: Mode = "offline"


class ChatResponse(BaseModel):
    answer: str
    excerpts: list[SegmentOut]


class HealthResponse(BaseModel):
    status: str
    claude_available: bool
    model: str
    audio_available: bool
    version: str


class SampleResponse(BaseModel):
    filename: str
    text: str
    meeting_date: str
