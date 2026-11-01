import json

import pytest
from fastapi.testclient import TestClient

import core.pipeline as pipeline
from api.main import app
from core.extractor import MeetingExtractor
from core.llm import FakeClient

client = TestClient(app)
RAW = "[00:00:10] Omar: Je vais demander trois devis d'ici vendredi.\n[00:00:30] Lina: On valide le budget, c'est décidé.\n"


def test_health():
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and "claude_available" in r and r["model"]


def test_sample_and_analyze_offline():
    s = client.get("/api/sample").json()
    r = client.post("/api/analyze", json={"text": s["text"], "filename": s["filename"], "mode": "offline", "meeting_date": s["meeting_date"]})
    assert r.status_code == 200
    body = r.json()
    assert len(body["report"]["decisions"]) == 4 and len(body["report"]["actions"]) == 6
    assert body["report"]["actions"][0]["segment_index"] is not None
    assert len(body["segments"]) == 26 and body["segments"][0]["speaker"] == "Sara"
    assert all(a["verifie"] for a in body["report"]["actions"])


def test_analyze_empty_text_is_rejected():
    assert client.post("/api/analyze", json={"text": "", "mode": "offline"}).status_code == 422
    assert client.post("/api/analyze", json={"text": "# juste un commentaire", "mode": "offline"}).status_code == 422


def test_claude_mode_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/analyze", json={"text": RAW, "mode": "claude"})
    assert r.status_code == 400 and "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_claude_mode_with_fake_llm(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    fake = FakeClient(lambda s, u: json.dumps({
        "titre": "Test", "resume_executif": "R", "decisions": [], "questions_ouvertes": [],
        "actions": [{"description": "Demander trois devis", "responsable": "Omar", "echeance_texte": "vendredi",
                     "priorite": "moyenne", "source_citation": "Je vais demander trois devis d'ici vendredi"}]}))
    monkeypatch.setattr(pipeline, "build_extractor", lambda mode, model=None: MeetingExtractor(fake))
    r = client.post("/api/analyze", json={"text": RAW, "mode": "claude", "meeting_date": "2026-10-26"})
    assert r.status_code == 200
    a = r.json()["report"]["actions"][0]
    assert a["echeance"] == "2026-10-30" and a["verifie"] is True


def _report():
    s = client.get("/api/sample").json()
    return client.post("/api/analyze", json={"text": s["text"], "filename": s["filename"], "meeting_date": s["meeting_date"]}).json()["report"]


@pytest.mark.parametrize("fmt,magic", [("docx", b"PK"), ("md", b"# "), ("json", b"{"), ("ics", b"BEGIN:VCALENDAR")])
def test_exports(fmt, magic):
    r = client.post(f"/api/export/{fmt}", json=_report())
    assert r.status_code == 200 and r.content.startswith(magic)
    assert "attachment" in r.headers["content-disposition"]


def test_export_email_and_unknown_format():
    mail = client.post("/api/export/email", json=_report()).json()
    assert mail["subject"].startswith("Compte rendu") and "ACTIONS" in mail["body"]
    assert client.post("/api/export/pdf", json=_report()).status_code == 404


def test_export_rejects_invalid_report():
    assert client.post("/api/export/docx", json={"actions": [{"priorite": "urgentissime"}]}).status_code == 422


def test_chat_offline():
    s = client.get("/api/sample").json()
    segs = client.post("/api/analyze", json={"text": s["text"], "filename": s["filename"]}).json()["segments"]
    r = client.post("/api/chat", json={"question": "Que pense Karim de la version mobile ?", "segments": segs}).json()
    assert r["excerpts"] and any(e["speaker"] == "Karim" for e in r["excerpts"])


def test_transcribe_without_whisper():
    import importlib.util
    if importlib.util.find_spec("faster_whisper") is None:
        r = client.post("/api/transcribe", files={"file": ("a.wav", b"RIFF", "audio/wav")})
        assert r.status_code == 501


def test_cors_header():
    r = client.options("/api/analyze", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
