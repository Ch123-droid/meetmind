import json
from datetime import date

from core import export
from core.extractor import MeetingExtractor, merge_reports
from core.llm import FakeClient, call_json, extract_json
from core.parsing import parse_transcript
from core.qa import answer, retrieve
from core.schemas import Action, CompteRendu, Decision

RAW = (
    "[00:00:10] Omar: Je vais demander trois devis d'ici vendredi.\n"
    "[00:00:30] Lina: Ok. On valide le budget de 5000 dirhams, c'est décidé.\n"
)
GOOD = {
    "titre": "Test", "resume_executif": "Résumé.", "participants": ["Omar"],
    "points_cles": ["Devis"],
    "decisions": [{"decision": "Valider le budget de 5000 dirhams", "contexte": "", "source_citation": "On valide le budget de 5000 dirhams"}],
    "actions": [
        {"description": "Demander trois devis", "responsable": "Omar", "echeance_texte": "vendredi", "priorite": "moyenne",
         "source_citation": "Je vais demander trois devis d'ici vendredi"},
        {"description": "Action hallucinée", "responsable": "Zoé", "echeance_texte": None, "priorite": "moyenne",
         "source_citation": "Zoé embauchera dix personnes en janvier prochain sans discussion"},
        {"priorite": "urgentissime"},  # élément invalide -> ignoré
    ],
    "questions_ouvertes": [],
}


def test_extract_json_handles_fences_and_noise():
    assert extract_json('Voici :\n```json\n{"a": 1}\n```') == {"a": 1}


def test_call_json_retries_on_invalid():
    replies = iter(["pas du json", json.dumps({"ok": True})])
    llm = FakeClient(lambda s, u: next(replies))
    assert call_json(llm, "sys", "user") == {"ok": True}
    assert "invalide" in llm.calls[1][1]


def test_llm_pipeline_dates_verification_and_tolerance():
    llm = FakeClient(lambda s, u: json.dumps(GOOD))
    segs = parse_transcript(RAW)
    cr = MeetingExtractor(llm).run(segs, date(2026, 10, 26))
    assert len(cr.actions) == 2  # l'élément invalide a été écarté
    ok, fake = cr.actions
    assert ok.echeance == "2026-10-30" and ok.verifie and ok.horodatage == "00:00:10"
    assert not fake.verifie                      # citation inventée -> « à vérifier »
    assert cr.decisions[0].verifie
    assert "Lina" in cr.participants             # complété depuis la transcription
    assert "Date de la réunion : 2026-10-26" in llm.calls[0][1]


def test_map_reduce_on_long_meeting():
    long_raw = "\n".join(f"[00:{i // 60:02d}:{i % 60:02d}] Omar: " + "blabla " * 40 for i in range(30))
    long_raw += "\n[00:59:00] Omar: Je vais demander trois devis d'ici vendredi."

    def handler(system, user):
        if "résumés partiels" in system:
            return json.dumps({"titre": "Global", "resume_executif": "Synthèse.", "points_cles": ["A", "B"]})
        return json.dumps({"titre": "Bloc", "resume_executif": "r", "actions": [
            {"description": "Demander trois devis", "responsable": "Omar", "echeance_texte": "vendredi",
             "priorite": "moyenne", "source_citation": "Je vais demander trois devis d'ici vendredi"}]})

    llm = FakeClient(handler)
    cr = MeetingExtractor(llm, max_words=400).run(parse_transcript(long_raw), date(2026, 10, 26))
    assert len(llm.calls) > 2
    assert cr.titre == "Global" and len(cr.actions) == 1  # dédoublonnage entre blocs


def test_merge_fills_missing_fields():
    a = CompteRendu(actions=[Action(description="Envoyer le compte rendu à l'équipe")])
    b = CompteRendu(actions=[Action(description="Envoyer le compte rendu à toute l'équipe", responsable="Sara", echeance_texte="demain")])
    m = merge_reports([a, b])
    assert len(m.actions) == 1 and m.actions[0].responsable == "Sara"


def _sample_cr():
    return CompteRendu(
        titre="Réunion test", date_reunion="2026-10-26", resume_executif="Résumé.", participants=["Omar", "Lina"],
        points_cles=["Budget"], decisions=[Decision(decision="Valider le budget", verifie=True, horodatage="00:00:30")],
        actions=[Action(description="Demander trois devis", responsable="Omar", echeance="2026-10-30", priorite="haute", verifie=True),
                 Action(description="Sans date", verifie=False)],
        questions_ouvertes=["Quel prestataire ?"],
    )


def test_exports():
    cr = _sample_cr()
    md = export.to_markdown(cr)
    assert "## Décisions" in md and "30/10/2026" in md and "⚠️" in md
    docx = export.to_docx(cr)
    assert docx[:2] == b"PK" and len(docx) > 5000
    mail = export.to_email(cr)
    assert "Omar : Demander trois devis" in mail["body"] and mail["subject"].startswith("Compte rendu")
    ics = export.to_ics(cr)
    assert ics.count("BEGIN:VEVENT") == 1 and "DTSTART;VALUE=DATE:20261030" in ics


def test_qa_retrieval_offline():
    segs = parse_transcript("[00:00:05] Sara: Le budget est de cinq mille dirhams.\n[00:00:20] Karim: Le serveur sera prêt mercredi.")
    hits = retrieve("Quel est le budget ?", segs)
    assert hits and hits[0].speaker == "Sara"
    reply, _ = answer("Quel est le budget ?", segs, None)
    assert "hors-ligne" in reply
    assert answer("xyzzy", segs, None)[0].startswith("Cette information")
