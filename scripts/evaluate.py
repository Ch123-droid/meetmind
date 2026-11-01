"""Évalue un ou plusieurs systèmes sur les réunions de data/reference/.
Usage :  python scripts/evaluate.py --modes offline            (sans clé API)
         python scripts/evaluate.py --modes offline claude     (compare règles vs Claude)
Produit outputs/evaluation.md (tableau à intégrer au rapport)."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.evaluate import evaluate, to_markdown_table  # noqa: E402
from core.pipeline import process_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", nargs="+", default=["offline"], choices=["offline", "claude"])
    ap.add_argument("--model", default=None)
    a = ap.parse_args()

    results: dict[str, dict] = {}
    for ref_file in sorted((ROOT / "data/reference").glob("*.json")):
        ref = json.loads(ref_file.read_text(encoding="utf-8"))
        sample = next((ROOT / "data/samples").glob(ref_file.stem + ".*"))
        raw = sample.read_text(encoding="utf-8")
        for mode in a.modes:
            cr, _ = process_text(raw, sample.name, mode, date.fromisoformat(ref["date_reunion"]), a.model)
            name = {"offline": "Règles (baseline)", "claude": "Claude (LLM)"}[mode]
            results[f"{name} — {ref_file.stem}"] = evaluate(cr, ref)

    table = to_markdown_table(results)
    print(table)
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    (out / "evaluation.md").write_text("# Résultats d'évaluation\n\n" + table + "\n", encoding="utf-8")
    (out / "evaluation.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
