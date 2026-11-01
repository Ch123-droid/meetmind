from pathlib import Path

from core.parsing import parse_transcript, participants_from, render
from core.chunking import chunk_segments

ROOT = Path(__file__).resolve().parent.parent


def test_parse_txt_timestamp_and_speaker():
    segs = parse_transcript("[00:01:23] Sara: Bonjour à tous.\n[00:01:30] Karim: Salut.")
    assert segs[0].speaker == "Sara" and segs[0].start == 83 and segs[0].text == "Bonjour à tous."
    assert segs[1].timestamp == "00:01:30"


def test_parse_plain_without_speaker():
    segs = parse_transcript("On avance sur le budget.\nEt le planning aussi.")
    assert len(segs) == 2 and segs[0].speaker is None and segs[0].start is None


def test_parse_vtt_voice_tags():
    raw = (ROOT / "data/samples/standup_equipe.vtt").read_text(encoding="utf-8")
    segs = parse_transcript(raw, "x.vtt")
    assert len(segs) == 5
    assert segs[0].speaker == "Amine" and segs[0].start == 3
    assert participants_from(segs) == ["Amine", "Nadia"]


def test_parse_srt():
    raw = "1\n00:00:01,000 --> 00:00:03,000\nAmine: Bonjour\n\n2\n00:00:04,000 --> 00:00:06,000\nNadia: Salut\n"
    segs = parse_transcript(raw, "a.srt")
    assert [s.speaker for s in segs] == ["Amine", "Nadia"]


def test_sample_loads_and_roundtrips():
    segs = parse_transcript((ROOT / "data/samples/reunion_site_web.txt").read_text(encoding="utf-8"))
    assert len(segs) == 26 and "Sara: Bonjour" in render(segs)


def test_chunking_overlap_and_coverage():
    segs = parse_transcript("\n".join(f"[00:00:{i:02d}] A: " + "mot " * 50 for i in range(20)))
    chunks = chunk_segments(segs, max_words=300, overlap=2)
    assert len(chunks) > 1
    assert chunks[1][0] is chunks[0][-2]  # chevauchement
    assert {id(s) for c in chunks for s in c} == {id(s) for s in segs}
