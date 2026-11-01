"""Résolution des échéances relatives en français (« vendredi prochain » -> date ISO).

Conventions (documentées pour la soutenance) :
- « vendredi » / « vendredi prochain » : prochaine occurrence STRICTEMENT après la date de réunion.
- « la semaine prochaine » : vendredi de la semaine suivante (échéance de fin de semaine).
- « fin de semaine » : vendredi de la semaine courante.
- « fin du mois » : dernier jour du mois courant.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, timedelta
from typing import Optional

from .textutils import normalize

JOURS = {"lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4, "samedi": 5, "dimanche": 6}
MOIS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
    "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}
NOMBRES = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
           "huit": 8, "neuf": 9, "dix": 10, "quinze": 15}


def _next_weekday(ref: date, wd: int) -> date:
    delta = (wd - ref.weekday()) % 7 or 7
    return ref + timedelta(days=delta)


def _safe(y: int, m: int, d: int) -> Optional[date]:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def resolve_deadline(text: Optional[str], ref: date) -> Optional[str]:
    """Retourne une date ISO ou None si l'expression n'est pas reconnue."""
    if not text:
        return None
    t = normalize(text)

    if re.search(r"\baujourd'?hui\b|\bce jour\b|\bce soir\b", t):
        return ref.isoformat()
    if re.search(r"\bapres[- ]?demain\b", t):
        return (ref + timedelta(days=2)).isoformat()
    if re.search(r"\bdemain\b", t):
        return (ref + timedelta(days=1)).isoformat()

    m = re.search(r"\bdans (\w+) (jour|jours|semaine|semaines|mois)\b", t)
    if m:
        n = int(m.group(1)) if m.group(1).isdigit() else NOMBRES.get(m.group(1))
        if n:
            unit = m.group(2)
            if unit.startswith("jour"):
                return (ref + timedelta(days=n)).isoformat()
            if unit.startswith("semaine"):
                return (ref + timedelta(weeks=n)).isoformat()
            month = ref.month - 1 + n
            y, mo = ref.year + month // 12, month % 12 + 1
            d = min(ref.day, calendar.monthrange(y, mo)[1])
            return date(y, mo, d).isoformat()

    if re.search(r"\bsemaine (prochaine|suivante)\b", t):
        monday_next = ref + timedelta(days=7 - ref.weekday())
        return (monday_next + timedelta(days=4)).isoformat()
    if re.search(r"\bfin de (la )?semaine\b", t):
        return (ref + timedelta(days=(4 - ref.weekday()) % 7)).isoformat()
    if re.search(r"\bfin (du|de ce) mois\b", t):
        return date(ref.year, ref.month, calendar.monthrange(ref.year, ref.month)[1]).isoformat()
    if re.search(r"\bmois prochain\b", t):
        y, mo = (ref.year + 1, 1) if ref.month == 12 else (ref.year, ref.month + 1)
        return date(y, mo, 1).isoformat()

    # Date explicite : 15/11, 15/11/2026, 2026-11-15
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m and (d := _safe(int(m.group(1)), int(m.group(2)), int(m.group(3)))):
        return d.isoformat()
    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
    if m:
        y = int(m.group(3)) if m.group(3) else ref.year
        y += 2000 if y < 100 else 0
        d = _safe(y, int(m.group(2)), int(m.group(1)))
        if d:
            if not m.group(3) and d < ref:
                d = _safe(y + 1, d.month, d.day) or d
            return d.isoformat()

    # « 5 novembre », « le 1er décembre »
    m = re.search(r"\b(\d{1,2})(?:er)? (janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\b(?: (\d{4}))?", t)
    if m:
        y = int(m.group(3)) if m.group(3) else ref.year
        d = _safe(y, MOIS[m.group(2)], int(m.group(1)))
        if d:
            if not m.group(3) and d < ref:
                d = _safe(y + 1, d.month, d.day) or d
            return d.isoformat()

    # Jour de semaine
    for nom, wd in JOURS.items():
        if re.search(rf"\b{nom}\b", t):
            return _next_weekday(ref, wd).isoformat()

    return None


# Motif utilisé par l'extracteur hors-ligne pour repérer une expression d'échéance dans une phrase.
DEADLINE_PATTERN = re.compile(
    r"(?i)\b(aujourd['’]hui|apr[èe]s-demain|demain|ce soir|"
    r"(?:d['’]ici |avant |pour |pour le |avant le |d['’]ici le )?(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)(?: prochain)?|"
    r"(?:d['’]ici |pour |avant )?(?:la )?semaine prochaine|fin de (?:la )?semaine|fin du mois|le mois prochain|"
    r"dans \w+ (?:jours?|semaines?|mois)|"
    r"(?:le )?\d{1,2}(?:er)? (?:janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)(?: \d{4})?|"
    r"\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b"
)
