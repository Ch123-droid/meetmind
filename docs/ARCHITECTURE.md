# Architecture technique

1. **Entrées** : `.txt/.vtt/.srt` ou audio → `Segment(text, speaker, start)`.
2. **Prétraitement** : `chunk_segments` (≈3000 mots, chevauchement de 3 prises de parole).
3. **MAP** : un appel LLM par bloc avec `prompts/extraction.md` → JSON ; `call_json` relance si le JSON est invalide ; `_build` ignore les éléments invalides.
4. **REDUCE** : `merge_reports` (dédoublonnage par similarité ≥ 0,6, complétion des champs manquants) + appel `merge.md` pour titre/résumé/points clés globaux.
5. **Dates** : `resolve_deadline(echeance_texte, date_réunion)` — conventions documentées dans `core/dates.py`.
6. **Vérification** : `verify_report` — présence de la citation (exacte puis floue ≥ 0,85), horodatage du segment source.
7. **API** : FastAPI expose ces briques en JSON (`/api/analyze`, `/api/chat`, `/api/export/*`).
8. **Présentation** : Next.js / React (édition, vue source surlignée, chat) ; exports DOCX/MD/JSON/e-mail/ICS.

**Pourquoi deux applications ?** Le cœur NLP est en Python (tests, dates, vérification) ; FastAPI l'expose sans le réécrire, et la clé API reste côté serveur. Next.js apporte une interface professionnelle et déployable séparément (Vercel).

**Choix de conception à défendre**
- Le LLM extrait le texte de l'échéance, **le code** calcule la date.
- Le LLM est injecté via l'interface `LLMClient` → tests sans réseau (`FakeClient`), changement de fournisseur trivial.
- Un extracteur à règles partage la même interface : baseline mesurable + mode 100 % local.
