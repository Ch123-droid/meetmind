"""Utilitaires de normalisation de texte (français)."""
import re
import unicodedata


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize(s: str) -> str:
    """Minuscule, sans accents ni ponctuation, espaces compressés."""
    s = strip_accents(s.lower().replace("’", "'"))
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


STOPWORDS = set(
    "le la les un une des du de d l et ou a au aux en dans sur pour par avec sans que qui quoi "
    "ce cette ces se sa son ses on il elle ils elles je tu nous vous y est sont etre faire "
    "va vais vont doit dois peut peux pas ne plus mais donc car si comme tres bien alors "
    "c j m n s t qu".split()
)


def tokens(s: str) -> set[str]:
    return {t for t in normalize(s).replace("'", " ").split() if t not in STOPWORDS and len(t) > 1}


def similarity(a: str, b: str) -> float:
    """Similarité lexicale 0..1 (mélange Jaccard + inclusion), sans dépendance."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    jacc = inter / len(ta | tb)
    incl = inter / min(len(ta), len(tb))
    return 0.5 * jacc + 0.5 * incl
