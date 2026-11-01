"""Usage :  python scripts/run_cli.py data/samples/reunion_site_web.txt --date 2026-10-26 --mode offline
Écrit dans outputs/ : JSON, Markdown, DOCX, e-mail, ICS."""
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import export  # noqa: E402
from core.pipeline import process_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="MeetMind : transcription -> compte rendu structuré")
    ap.add_argument("file")
    ap.add_argument("--date", default=None, help="Date de la réunion AAAA-MM-JJ (sert à résoudre « vendredi », « demain »…)")
    ap.add_argument("--mode", choices=["offline", "claude"], default="offline")
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default="outputs")
    a = ap.parse_args()

    path = Path(a.file)
    cr, _ = process_text(path.read_text(encoding="utf-8"), path.name, a.mode,
                         date.fromisoformat(a.date) if a.date else None, a.model,
                         progress=lambda i, n, m: print(f"[{i}/{n}] {m}"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    (out / f"{stem}.json").write_text(export.to_json(cr), encoding="utf-8")
    (out / f"{stem}.md").write_text(export.to_markdown(cr), encoding="utf-8")
    (out / f"{stem}.docx").write_bytes(export.to_docx(cr))
    (out / f"{stem}.ics").write_text(export.to_ics(cr), encoding="utf-8")
    mail = export.to_email(cr)
    (out / f"{stem}_email.txt").write_text(f"Objet : {mail['subject']}\n\n{mail['body']}", encoding="utf-8")
    print(export.to_markdown(cr))
    print(f"\nFichiers écrits dans {out}/")


if __name__ == "__main__":
    main()
