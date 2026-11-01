"""API MeetMind (FastAPI).  Lancer :  uvicorn api.main:app --reload --port 8000"""
from __future__ import annotations

import importlib.util
import os
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from core import export
from core.llm import DEFAULT_MODEL, ClaudeClient
from core.pipeline import process_text
from core.qa import answer
from core.schemas import CompteRendu, Segment

from .schemas import (AnalyzeRequest, AnalyzeResponse, ChatRequest, ChatResponse, HealthResponse,
                      SampleResponse, SegmentOut)

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
MAX_AUDIO_MB = 200

app = FastAPI(title="MeetMind API", version=VERSION,
              description="Transcription de réunion → compte rendu structuré (décisions, actions, sources vérifiées).")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])


def _claude_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _seg_out(s: Segment) -> SegmentOut:
    return SegmentOut(text=s.text, speaker=s.speaker, start=s.start, timestamp=s.timestamp)


def _require_claude(mode: str):
    if mode == "claude" and not _claude_available():
        raise HTTPException(400, "Le mode Claude nécessite la variable d'environnement ANTHROPIC_API_KEY côté serveur.")


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", claude_available=_claude_available(), model=DEFAULT_MODEL,
                          audio_available=importlib.util.find_spec("faster_whisper") is not None, version=VERSION)


@app.get("/api/sample", response_model=SampleResponse)
def sample():
    p = ROOT / "data/samples/reunion_site_web.txt"
    return SampleResponse(filename=p.name, text=p.read_text(encoding="utf-8"), meeting_date="2026-10-26")


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    _require_claude(req.mode)
    t0 = time.perf_counter()
    try:
        report, segments = process_text(req.text, req.filename, req.mode, req.meeting_date, req.model)
    except ValueError as exc:  # transcription vide / illisible
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:  # erreur LLM / réseau
        raise HTTPException(502, f"Échec de l'analyse : {exc}") from exc
    return AnalyzeResponse(report=report, segments=[_seg_out(s) for s in segments], mode=req.mode,
                           elapsed_seconds=round(time.perf_counter() - t0, 2))


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = "fr", model_size: str = "small"):
    """Audio -> transcription texte horodatée (nécessite faster-whisper)."""
    if importlib.util.find_spec("faster_whisper") is None:
        raise HTTPException(501, "faster-whisper n'est pas installé : `pip install faster-whisper`.")
    data = await file.read()
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(413, f"Fichier trop volumineux (max {MAX_AUDIO_MB} Mo).")
    from core.audio import audio_to_segments
    from core.parsing import render

    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
    try:
        segs = audio_to_segments(tmp.name, model_size=model_size, language=language)
    finally:
        os.unlink(tmp.name)
    return {"text": render(segs), "segments": [_seg_out(s).model_dump() for s in segs]}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    _require_claude(req.mode)
    segs = [Segment(text=s.text, speaker=s.speaker, start=s.start) for s in req.segments]
    llm = ClaudeClient() if req.mode == "claude" else None
    try:
        reply, hits = answer(req.question, segs, llm)
    except Exception as exc:
        raise HTTPException(502, f"Échec de la réponse : {exc}") from exc
    return ChatResponse(answer=reply, excerpts=[_seg_out(s) for s in hits])


_FILES = {
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", lambda cr: export.to_docx(cr)),
    "md": ("text/markdown; charset=utf-8", lambda cr: export.to_markdown(cr).encode("utf-8")),
    "json": ("application/json", lambda cr: export.to_json(cr).encode("utf-8")),
    "ics": ("text/calendar; charset=utf-8", lambda cr: export.to_ics(cr).encode("utf-8")),
}


@app.post("/api/export/email")
def export_email(report: CompteRendu):
    return export.to_email(report)


@app.post("/api/export/{fmt}")
def export_file(fmt: str, report: CompteRendu):
    if fmt not in _FILES:
        raise HTTPException(404, f"Format inconnu : {fmt}. Formats : {', '.join(_FILES)} ou email.")
    media, build = _FILES[fmt]
    return Response(content=build(report), media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="compte_rendu.{fmt}"'})


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception):  # dernier filet : jamais de trace brute côté client
    return JSONResponse(status_code=500, content={"detail": f"Erreur interne : {type(exc).__name__}"})
