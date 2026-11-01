"""Audio -> transcription (faster-whisper) + identification des locuteurs (pyannote, optionnelle).

Dépendances lourdes, importées à la demande :  pip install faster-whisper  [pyannote.audio]
NB : module non couvert par les tests automatiques (nécessite un fichier audio réel).
"""
from __future__ import annotations

import os
from typing import Optional

from .schemas import Segment


def transcribe_segments(path: str, model_size: str = "medium", language: Optional[str] = "fr", device: str = "auto") -> list[tuple[float, float, str]]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device=device, compute_type="int8" if device == "cpu" else "default")
    raw, _ = model.transcribe(path, language=language, vad_filter=True, beam_size=5)
    return [(s.start, s.end, s.text.strip()) for s in raw if s.text.strip()]


def diarize(path: str, hf_token: Optional[str] = None) -> list[tuple[float, float, str]]:
    """Retourne [(début, fin, 'SPEAKER_00'), ...]. Nécessite un jeton Hugging Face (modèle pyannote gated)."""
    from pyannote.audio import Pipeline

    pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token or os.getenv("HF_TOKEN"))
    return [(t.start, t.end, spk) for t, _, spk in pipe(path).itertracks(yield_label=True)]


def audio_to_segments(path: str, model_size: str = "medium", language: Optional[str] = "fr",
                      with_speakers: bool = False, hf_token: Optional[str] = None) -> list[Segment]:
    """Transcrit, puis attribue à chaque phrase le locuteur au plus grand recouvrement temporel."""
    phrases = transcribe_segments(path, model_size, language)
    turns = diarize(path, hf_token) if with_speakers else []
    out: list[Segment] = []
    for start, end, text in phrases:
        speaker = None
        best = 0.0
        for ts, te, spk in turns:
            overlap = min(end, te) - max(start, ts)
            if overlap > best:
                best, speaker = overlap, spk
        out.append(Segment(text=text, speaker=speaker, start=start))
    return out
