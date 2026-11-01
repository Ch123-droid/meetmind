import json
from datetime import date
from pathlib import Path

from core.evaluate import evaluate, match
from core.offline import OfflineExtractor
from core.parsing import parse_transcript

ROOT = Path(__file__).resolve().parent.parent
REF_DATE = date(2026, 10, 26)


def _run(name="reunion_site_web.txt"):
    segs = parse_transcript((ROOT / "data/samples" / name).read_text(encoding="utf-8"), name)
    return OfflineExtractor().run(segs, REF_DATE), segs


def test_offline_finds_decisions_and_actions():
    cr, _ = _run()
    assert len(cr.decisions) == 4 and len(cr.actions) == 6
    leila = [a for a in cr.actions if a.responsable == "Leila"]
    assert any("maquettes" in a.description for a in leila)


def test_offline_resolves_deadlines_and_priority():
    cr, _ = _run()
    by_owner = {(a.responsable, a.description.split()[0]): a for a in cr.actions}
    assert by_owner[("Karim", "Configurer")].echeance == "2026-10-28"
    assert by_owner[("Sara", "Envoyer")].echeance == "2026-10-27"
    tresor = by_owner[("Youssef", "Contacter")]
    assert tresor.echeance == "2026-11-02" and tresor.priorite == "haute"


def test_offline_sources_are_all_verified():
    cr, _ = _run()
    assert cr.taux_fidelite == 1.0


def test_proposal_is_not_a_decision():
    cr, _ = _run()
    assert not any("je propose" in d.source_citation.lower() for d in cr.decisions)


def test_vtt_sample():
    cr, _ = _run("standup_equipe.vtt")
    assert any(a.responsable == "Nadia" for a in cr.actions)
    assert any("12 novembre" in d.decision for d in cr.decisions)


def test_evaluation_metrics_on_reference():
    cr, _ = _run()
    ref = json.loads((ROOT / "data/reference/reunion_site_web.json").read_text(encoding="utf-8"))
    res = evaluate(cr, ref)
    assert res["decisions"]["f1"] >= 0.8
    assert res["actions"]["f1"] >= 0.8
    assert res["exactitude_responsable"] == 1.0
    assert res["fidelite_citations"] == 1.0


def test_match_is_one_to_one():
    pairs = match(["envoyer le compte rendu"], ["envoyer le compte rendu", "envoyer le compte rendu à tous"])
    assert len(pairs) == 1
