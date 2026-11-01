"""Exports : Markdown, DOCX, e-mail de suivi, calendrier .ics, JSON."""
from __future__ import annotations

import io
from datetime import date, datetime, timedelta, timezone

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from .schemas import CompteRendu

NAVY, TEAL = RGBColor(0x1F, 0x3A, 0x5F), RGBColor(0x0E, 0x9A, 0xA7)
PRIO_FILL = {"haute": "F8D7DA", "moyenne": "FFF3CD", "basse": "D4EDDA"}
PRIO_LABEL = {"haute": "Haute", "moyenne": "Moyenne", "basse": "Basse"}


def _fr_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


# ------------------------------------------------------------------ Markdown
def to_markdown(cr: CompteRendu) -> str:
    L = [f"# {cr.titre}", ""]
    if cr.date_reunion:
        L.append(f"**Date :** {_fr_date(cr.date_reunion)}  ")
    if cr.participants:
        L.append(f"**Participants :** {', '.join(cr.participants)}")
    L += ["", "## Résumé exécutif", cr.resume_executif or "—", ""]
    if cr.points_cles:
        L += ["## Points clés"] + [f"- {p}" for p in cr.points_cles] + [""]
    L.append("## Décisions")
    L += [f"{i}. **{d.decision}**" + (f" _(source {d.horodatage})_" if d.horodatage else "") + ("" if d.verifie else " ⚠️ à vérifier")
          for i, d in enumerate(cr.decisions, 1)] or ["_Aucune décision identifiée._"]
    L += ["", "## Actions", "", "| # | Action | Responsable | Échéance | Priorité |", "|---|---|---|---|---|"]
    for i, a in enumerate(cr.actions, 1):
        flag = "" if a.verifie else " ⚠️"
        L.append(f"| {i} | {a.description}{flag} | {a.responsable or '—'} | {_fr_date(a.echeance) if a.echeance else (a.echeance_texte or '—')} | {PRIO_LABEL[a.priorite]} |")
    if cr.questions_ouvertes:
        L += ["", "## Questions ouvertes"] + [f"- {q}" for q in cr.questions_ouvertes]
    L += ["", f"---\n_Généré par MeetMind · fidélité des sources : {cr.taux_fidelite:.0%}_"]
    return "\n".join(L)


# ---------------------------------------------------------------------- DOCX
def _shade(cell, hex_fill: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def _heading(doc, text: str, size=15):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold, r.font.size, r.font.color.rgb = True, Pt(size), NAVY
    pPr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", "6"), ("space", "2"), ("color", "0E9AA7")):
        b.set(qn(f"w:{k}"), v)
    bdr.append(b)
    pPr.append(bdr)


def _table(doc, headers, rows, widths, fills=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold, r.font.size, r.font.color.rgb = True, Pt(10), RGBColor(255, 255, 255)
        _shade(c, "1F3A5F")
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            cells[i].paragraphs[0].add_run(str(val)).font.size = Pt(10)
            if fills and fills[ri].get(i):
                _shade(cells[i], fills[ri][i])
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Pt(w)
    return t


def to_docx(cr: CompteRendu) -> bytes:
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)
    p = doc.add_paragraph()
    r = p.add_run("COMPTE RENDU DE RÉUNION")
    r.bold, r.font.size, r.font.color.rgb = True, Pt(10), TEAL
    p = doc.add_paragraph()
    r = p.add_run(cr.titre)
    r.bold, r.font.size, r.font.color.rgb = True, Pt(24), NAVY
    meta = doc.add_paragraph()
    meta.add_run("Date : ").bold = True
    meta.add_run(_fr_date(cr.date_reunion) + "    ")
    meta.add_run("Participants : ").bold = True
    meta.add_run(", ".join(cr.participants) or "—")

    _heading(doc, "Résumé exécutif")
    doc.add_paragraph(cr.resume_executif or "—")
    if cr.points_cles:
        _heading(doc, "Points clés")
        for pt in cr.points_cles:
            doc.add_paragraph(pt, style="List Bullet")

    _heading(doc, f"Décisions ({len(cr.decisions)})")
    if cr.decisions:
        _table(doc, ["#", "Décision", "Source"],
               [(i, d.decision + ("" if d.verifie else "  ⚠ à vérifier"), d.horodatage or "—") for i, d in enumerate(cr.decisions, 1)],
               [24, 360, 60])
    else:
        doc.add_paragraph("Aucune décision identifiée.")

    _heading(doc, f"Actions à réaliser ({len(cr.actions)})")
    if cr.actions:
        rows = [(i, a.description + ("" if a.verifie else "  ⚠"), a.responsable or "—",
                 _fr_date(a.echeance) if a.echeance else (a.echeance_texte or "—"), PRIO_LABEL[a.priorite])
                for i, a in enumerate(cr.actions, 1)]
        fills = [{4: PRIO_FILL[a.priorite]} for a in cr.actions]
        _table(doc, ["#", "Action", "Responsable", "Échéance", "Priorité"], rows, [22, 220, 75, 70, 60], fills)
    else:
        doc.add_paragraph("Aucune action identifiée.")

    if cr.questions_ouvertes:
        _heading(doc, "Questions ouvertes")
        for q in cr.questions_ouvertes:
            doc.add_paragraph(q, style="List Bullet")

    foot = doc.add_paragraph()
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = foot.add_run(f"\nGénéré par MeetMind · fidélité des sources : {cr.taux_fidelite:.0%} · relecture humaine recommandée")
    fr.italic, fr.font.size, fr.font.color.rgb = True, Pt(9), RGBColor(0x5A, 0x6B, 0x7D)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------- Email
def to_email(cr: CompteRendu) -> dict:
    lines = ["Bonjour à toutes et à tous,", "", f"Voici le compte rendu de la réunion « {cr.titre} »"
             + (f" du {_fr_date(cr.date_reunion)}." if cr.date_reunion else "."), "", "RÉSUMÉ", cr.resume_executif, ""]
    if cr.decisions:
        lines += ["DÉCISIONS"] + [f"  • {d.decision}" for d in cr.decisions] + [""]
    if cr.actions:
        lines.append("ACTIONS À RÉALISER")
        for a in cr.actions:
            due = _fr_date(a.echeance) if a.echeance else (a.echeance_texte or "à définir")
            lines.append(f"  • {a.responsable or 'À attribuer'} : {a.description} (pour le {due})" if a.echeance else
                         f"  • {a.responsable or 'À attribuer'} : {a.description} ({due})")
        lines.append("")
    if cr.questions_ouvertes:
        lines += ["POINTS À TRAITER À LA PROCHAINE RÉUNION"] + [f"  • {q}" for q in cr.questions_ouvertes] + [""]
    lines += ["N'hésitez pas à me signaler toute correction.", "", "Cordialement,"]
    return {"subject": f"Compte rendu — {cr.titre}" + (f" ({_fr_date(cr.date_reunion)})" if cr.date_reunion else ""),
            "body": "\n".join(lines)}


# ----------------------------------------------------------------------- ICS
def to_ics(cr: CompteRendu) -> str:
    """Un événement « journée entière » par action datée, importable dans Google/Outlook/Apple Calendar."""
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MeetMind//FR", "CALSCALE:GREGORIAN"]
    for i, a in enumerate(cr.actions):
        if not a.echeance:
            continue
        d = date.fromisoformat(a.echeance)
        summary = f"{a.description} ({a.responsable})" if a.responsable else a.description
        out += ["BEGIN:VEVENT", f"UID:meetmind-{cr.date_reunion or 'x'}-{i}@meetmind", f"DTSTAMP:{now}",
                f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
                "SUMMARY:" + summary.replace(",", "\\,").replace(";", "\\;"),
                f"DESCRIPTION:Action issue de la réunion « {cr.titre} »", "END:VEVENT"]
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"


def to_json(cr: CompteRendu) -> str:
    return cr.model_dump_json(indent=2)
