"""Schémas de données de MeetMind (validation Pydantic)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel, Field


@dataclass
class Segment:
    """Une prise de parole de la transcription."""
    text: str
    speaker: Optional[str] = None
    start: Optional[float] = None  # secondes

    @property
    def timestamp(self) -> Optional[str]:
        if self.start is None:
            return None
        s = int(self.start)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"

    def render(self) -> str:
        parts = []
        if self.timestamp:
            parts.append(f"[{self.timestamp}]")
        if self.speaker:
            parts.append(f"{self.speaker}:")
        parts.append(self.text)
        return " ".join(parts)


class Action(BaseModel):
    description: str
    responsable: Optional[str] = None
    echeance_texte: Optional[str] = Field(None, description="Échéance telle que prononcée")
    echeance: Optional[str] = Field(None, description="Date ISO AAAA-MM-JJ calculée par le code")
    priorite: Literal["haute", "moyenne", "basse"] = "moyenne"
    source_citation: str = ""
    horodatage: Optional[str] = None
    segment_index: Optional[int] = None  # indice du segment source dans la transcription
    verifie: bool = False


class Decision(BaseModel):
    decision: str
    contexte: str = ""
    source_citation: str = ""
    horodatage: Optional[str] = None
    segment_index: Optional[int] = None
    verifie: bool = False


class CompteRendu(BaseModel):
    titre: str = "Compte rendu de réunion"
    date_reunion: Optional[str] = None
    resume_executif: str = ""
    participants: list[str] = Field(default_factory=list)
    points_cles: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    questions_ouvertes: list[str] = Field(default_factory=list)

    @property
    def taux_fidelite(self) -> float:
        """Part des éléments dont la citation source a été retrouvée."""
        items = [*self.decisions, *self.actions]
        if not items:
            return 1.0
        return sum(1 for i in items if i.verifie) / len(items)
