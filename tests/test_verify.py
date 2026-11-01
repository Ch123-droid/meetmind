from core.schemas import Action, CompteRendu, Decision, Segment
from core.verify import citation_score, locate, verify_report
from core.textutils import normalize

SEGS = [
    Segment("Je vais configurer l'environnement de test d'ici mercredi.", "Karim", 245),
    Segment("On part sur du mobile first, c'est décidé.", "Sara", 80),
]


def test_exact_citation_found():
    assert citation_score("configurer l'environnement de test", normalize(" ".join(s.text for s in SEGS))) == 1.0


def test_accent_and_case_insensitive():
    assert citation_score("ON PART SUR DU MOBILE FIRST", normalize(SEGS[1].text)) == 1.0


def test_hallucinated_citation_rejected():
    hay = normalize(" ".join(s.text for s in SEGS))
    assert citation_score("nous avons embauché trois développeurs supplémentaires", hay) < 0.85


def test_locate_returns_segment():
    assert locate("configurer l'environnement", SEGS) == 0
    assert locate("mobile first", SEGS) == 1


def test_verify_report_flags_and_timestamps():
    cr = CompteRendu(
        decisions=[Decision(decision="Mobile first", source_citation="On part sur du mobile first")],
        actions=[Action(description="Inventée", source_citation="phrase qui n'existe absolument nulle part ici")],
    )
    verify_report(cr, SEGS)
    assert cr.decisions[0].verifie and cr.decisions[0].horodatage == "00:01:20"
    assert not cr.actions[0].verifie
    assert cr.taux_fidelite == 0.5
