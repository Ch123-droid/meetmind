from datetime import date

import pytest

from core.dates import resolve_deadline

REF = date(2026, 10, 26)  # lundi


@pytest.mark.parametrize("text,expected", [
    ("demain", "2026-10-27"),
    ("après-demain", "2026-10-28"),
    ("vendredi", "2026-10-30"),
    ("vendredi prochain", "2026-10-30"),
    ("lundi", "2026-11-02"),          # même jour de semaine -> semaine suivante
    ("d'ici mercredi", "2026-10-28"),
    ("la semaine prochaine", "2026-11-06"),
    ("fin de semaine", "2026-10-30"),
    ("fin du mois", "2026-10-31"),
    ("le 5 novembre", "2026-11-05"),
    ("le 1er décembre", "2026-12-01"),
    ("dans deux semaines", "2026-11-09"),
    ("dans 3 jours", "2026-10-29"),
    ("15/11", "2026-11-15"),
    ("2026-12-24", "2026-12-24"),
])
def test_resolve(text, expected):
    assert resolve_deadline(text, REF) == expected


def test_past_date_rolls_to_next_year():
    assert resolve_deadline("le 3 mars", REF) == "2027-03-03"


def test_unknown_returns_none():
    assert resolve_deadline("bientôt", REF) is None
    assert resolve_deadline(None, REF) is None
