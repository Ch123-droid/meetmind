"""Évaluation : précision / rappel / F1 face à une référence manuelle + indicateurs de fiabilité."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from .schemas import CompteRendu
from .textutils import similarity


@dataclass
class PRF:
    precision: float
    recall: float
    f1: float
    tp: int
    n_pred: int
    n_ref: int


def _prf(tp: int, n_pred: int, n_ref: int) -> PRF:
    p = tp / n_pred if n_pred else (1.0 if not n_ref else 0.0)
    r = tp / n_ref if n_ref else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return PRF(round(p, 3), round(r, 3), round(f, 3), tp, n_pred, n_ref)


def match(pred: list[str], ref: list[str], thr: float = 0.45) -> list[tuple[int, int]]:
    """Appariement glouton un-pour-un par similarité décroissante."""
    pairs = sorted(((similarity(p, r), i, j) for i, p in enumerate(pred) for j, r in enumerate(ref)), reverse=True)
    used_p, used_r, out = set(), set(), []
    for s, i, j in pairs:
        if s < thr:
            break
        if i not in used_p and j not in used_r:
            used_p.add(i), used_r.add(j)
            out.append((i, j))
    return out


def evaluate(pred: CompteRendu, ref: dict, thr: float = 0.45) -> dict:
    d_pairs = match([d.decision for d in pred.decisions], [d["decision"] for d in ref.get("decisions", [])], thr)
    a_pairs = match([a.description for a in pred.actions], [a["description"] for a in ref.get("actions", [])], thr)
    ref_actions = ref.get("actions", [])

    owner_ok = sum(1 for i, j in a_pairs if (pred.actions[i].responsable or "").lower() == (ref_actions[j].get("responsable") or "").lower())
    date_ok = sum(1 for i, j in a_pairs if pred.actions[i].echeance == ref_actions[j].get("echeance"))
    prio_ok = sum(1 for i, j in a_pairs if pred.actions[i].priorite == ref_actions[j].get("priorite", "moyenne"))
    n = len(a_pairs) or 1

    # Invention : action avec responsable renseigné alors que la référence n'en a pas (ou inversement non mesuré)
    invented = sum(1 for i, j in a_pairs if pred.actions[i].responsable and not ref_actions[j].get("responsable"))
    q_pairs = match(pred.questions_ouvertes, ref.get("questions_ouvertes", []), 0.3)

    return {
        "decisions": asdict(_prf(len(d_pairs), len(pred.decisions), len(ref.get("decisions", [])))),
        "actions": asdict(_prf(len(a_pairs), len(pred.actions), len(ref_actions))),
        "questions": asdict(_prf(len(q_pairs), len(pred.questions_ouvertes), len(ref.get("questions_ouvertes", [])))),
        "exactitude_responsable": round(owner_ok / n, 3),
        "exactitude_echeance": round(date_ok / n, 3),
        "exactitude_priorite": round(prio_ok / n, 3),
        "taux_invention": round(invented / n, 3),
        "fidelite_citations": round(pred.taux_fidelite, 3),
    }


def to_markdown_table(results: dict[str, dict]) -> str:
    """results = {nom_du_système: evaluate(...)} -> tableau Markdown comparatif."""
    head = "| Système | F1 décisions | F1 actions | Rappel actions | Responsable | Échéance | Fidélité sources |\n|---|---|---|---|---|---|---|"
    rows = [f"| {n} | {r['decisions']['f1']:.2f} | {r['actions']['f1']:.2f} | {r['actions']['recall']:.2f} | "
            f"{r['exactitude_responsable']:.0%} | {r['exactitude_echeance']:.0%} | {r['fidelite_citations']:.0%} |" for n, r in results.items()]
    return "\n".join([head, *rows])
