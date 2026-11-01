"""Extracteur HORS-LIGNE à base de règles (français).

Rôle : (1) démo sans clé API, (2) *baseline* de comparaison dans l'évaluation face au LLM,
(3) filet de sécurité si l'API est indisponible. Il est volontairement simple et explicable.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

from .dates import DEADLINE_PATTERN
from .extractor import finalize, _dedupe_strings
from .parsing import participants_from
from .schemas import Action, CompteRendu, Decision, Segment
from .textutils import similarity

DECISION_RE = re.compile(
    r"(?i)\b(c['’]est (?:décidé|validé|acté|entendu)|on d[ée]cide|nous d[ée]cidons|on valide|on retient|on fixe|"
    r"on part sur|on garde|on opte|on adopte|on tranche|on choisit|il est d[ée]cid[ée]|d['’]accord pour)\b"
)
FIRST_PERSON_RE = re.compile(
    r"(?i)\bje (?:vais|m['’]occupe(?: de| d['’])?|me charge(?: de| d['’])?|"
    r"(\w+rai)|ferai|enverrai)\b"
)
ADDRESSED_RE = re.compile(r"(?i)^(?:ok|d['’]accord|très bien|parfait|alors)?[, ]*(?P<name>[A-ZÀ-Ý][\wÀ-ÿ\-]+)[, ]+(?:tu|peux-tu|pourrais-tu)\s*(?:peux|pourrais|dois|devrais|vas)?\s*(?P<rest>.+)")
THIRD_RE = re.compile(r"(?P<name>[A-ZÀ-Ý][\wÀ-ÿ\-]+)\s+(?:va|s['’]occupe(?: de| d['’])?|se charge(?: de| d['’])?|devra)\s+(?P<rest>.+)")
OPEN_RE = re.compile(
    r"(?i)(reste à (?:trancher|décider|définir|voir)|à trancher|pas encore (?:décidé|validé|tranché)|"
    r"n['’]est pas encore (?:décidé|validé|tranché)|on ne sait pas encore|à voir avec|on en reparle)"
)
TOPIC_RE = re.compile(r"(?i)\b(?:passons à|on commence par|point suivant|parlons de|concernant)\s+(.+)")
URGENT_RE = re.compile(r"(?i)\b(urgent|urgence|bloquant|bloque|au plus vite|prioritaire|critique)\b")
IRREGULAR = {"enverrai": "envoyer", "ferai": "faire", "serai": "être", "aurai": "avoir", "irai": "aller", "verrai": "voir"}
LEADING_FILLER = re.compile(r"(?i)^(?:oui|ok|d['’]accord|très bien|parfait|bonne idée|bonne question|alors|du coup|donc|moi|écoute)[, ]+")
CUT_RE = re.compile(r"(?i)(?:[,;]?\s*\b(?:mais|parce que|car|puisque)\b.*|\s+et (?:vous|te) l['’]\w+)$")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _strip_fillers(s: str) -> str:
    prev = None
    while prev != s:
        prev, s = s, LEADING_FILLER.sub("", s).strip()
    return s


def _cap(s: str) -> str:
    s = s.strip(" ,;.!?")
    return s[:1].upper() + s[1:] if s else s


def _infinitive(verb: str) -> str:
    v = verb.lower()
    if v in IRREGULAR:
        return IRREGULAR[v]
    return v[:-2] if v.endswith("erai") else v


def _clean_task(rest: str, deadline: Optional[str]) -> str:
    if deadline:
        rest = rest.replace(deadline, "")
    rest = re.sub(r"(?i)\s+(?:pour|avant|d['’]ici|le)\s*$", "", rest.strip(" ,;.!?"))
    rest = CUT_RE.sub("", rest.strip(" ,;.!?"))
    rest = re.sub(r"\s{2,}", " ", rest)
    return _cap(rest)


def _find_deadline(sentence: str, segment_text: str) -> Optional[str]:
    for scope in (sentence, segment_text):
        m = DEADLINE_PATTERN.search(scope)
        if m:
            return m.group(0).strip()
    return None


def _owner_from_name(name: str, people: list[str]) -> Optional[str]:
    for p in people:
        if p.lower() == name.lower():
            return p
    return None


class OfflineExtractor:
    """Même interface que MeetingExtractor.run()."""

    def run(self, segments: list[Segment], meeting_date: Optional[date] = None, progress=None) -> CompteRendu:
        people = participants_from(segments)
        decisions: list[Decision] = []
        actions: list[Action] = []
        questions: list[str] = []
        topics: list[str] = []

        prev: Optional[Segment] = None
        for seg in segments:
            urgent = bool(URGENT_RE.search(seg.text))
            question_found = False
            for sent in _sentences(seg.text):
                core = _strip_fillers(sent)

                if (t := TOPIC_RE.search(core)):
                    topics.append(_cap(re.split(r"[.?!]", t.group(1))[0]))

                if DECISION_RE.search(core) and not core.rstrip().endswith("?"):
                    txt = re.sub(r"(?i)[, ]*c['’]est (?:décidé|validé|acté|entendu)\s*$", "", core.strip(" .!"))
                    decisions.append(Decision(decision=_cap(txt), contexte=seg.text[:160], source_citation=txt))
                    continue

                owner, task, cite = None, None, None
                m = FIRST_PERSON_RE.search(core)
                if m and "m'en occupe" not in core.replace("’", "'") and seg.speaker:
                    owner = seg.speaker
                    verb = m.group(1)
                    rest = core[m.end():].strip()
                    if verb and verb.lower() != "ferai" and verb.lower() not in ("vais",):
                        rest = f"{_infinitive(verb)} {rest}"
                    elif verb:
                        rest = f"{_infinitive(verb)} {rest}"
                    task, cite = rest, core
                elif (m := ADDRESSED_RE.match(core)) and core.rstrip().endswith("?") is not None:
                    name = _owner_from_name(m.group("name"), people)
                    if name and re.search(r"(?i)\btu\b", core):
                        owner, task, cite = name, m.group("rest"), core
                elif (m := THIRD_RE.search(core)):
                    name = _owner_from_name(m.group("name"), people)
                    if name:
                        owner, task, cite = name, m.group("rest"), core

                if owner and task:
                    deadline = _find_deadline(core, seg.text)
                    actions.append(Action(
                        description=_clean_task(task, deadline),
                        responsable=owner,
                        echeance_texte=deadline,
                        priorite="haute" if urgent else "moyenne",
                        source_citation=cite.strip(" .!?"),
                    ))
                    continue

                if OPEN_RE.search(core) and not question_found:
                    question_found = True
                    q = _cap(re.sub(r"(?i)^(?:je crois que|je pense que)\s+", "", core))
                    if len(q.split()) <= 6 and prev and prev.text.rstrip().endswith("?"):
                        q = _cap(_sentences(prev.text)[-1])  # reprend la question posée juste avant
                        q = _cap(re.sub(r"^[^:]{1,30}:\s*", "", q))
                    questions.append(q)
            prev = seg

        cr = CompteRendu(
            titre="Compte rendu de réunion",
            decisions=self._dedupe(decisions, "decision"),
            actions=self._dedupe(actions, "description"),
            questions_ouvertes=_dedupe_strings(questions, 0.4),
            points_cles=_dedupe_strings(topics),
            participants=people,
        )
        cr.resume_executif = self._summary(cr, len(segments))
        return finalize(cr, segments, meeting_date)

    @staticmethod
    def _dedupe(items, attr, thr=0.6):
        out = []
        for it in items:
            if not any(similarity(getattr(it, attr), getattr(o, attr)) >= thr for o in out):
                out.append(it)
        return out

    @staticmethod
    def _summary(cr: CompteRendu, n_segments: int) -> str:
        parts = [f"Réunion de {len(cr.participants)} participant(s)" + (f" ({', '.join(cr.participants)})" if cr.participants else "") + "."]
        if cr.points_cles:
            parts.append("Sujets abordés : " + " ; ".join(cr.points_cles[:4]) + ".")
        parts.append(f"{len(cr.decisions)} décision(s), {len(cr.actions)} action(s) et {len(cr.questions_ouvertes)} question(s) ouverte(s) identifiée(s).")
        if cr.decisions:
            parts.append("Décision principale : " + cr.decisions[0].decision + ".")
        return " ".join(parts)
