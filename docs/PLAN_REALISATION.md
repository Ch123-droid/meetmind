# Plan de réalisation pas à pas (6 semaines)

| Semaine | Objectif | Livrables | Fichiers concernés |
|---|---|---|---|
| **1 · Cadrage & données** | Cadrer, collecter, annoter | Cahier des charges, 10–15 transcriptions, 3 références manuelles | `docs/`, `data/` |
| **2 · Socle** | Lire et préparer les transcriptions | Parsing txt/vtt/srt, découpage, schémas Pydantic | `core/parsing.py`, `chunking.py`, `schemas.py` |
| **3 · Extraction LLM** | Le cœur du projet | Prompt système + exemples, appel Claude, JSON robuste, map-reduce | `prompts/`, `core/llm.py`, `extractor.py` |
| **4 · Fiabilité** | Éliminer l'invention | Vérification des citations, dates relatives, extracteur à règles | `core/verify.py`, `dates.py`, `offline.py` |
| **5 · Produit** | API et interface | FastAPI + Next.js, Word/e-mail/ICS, chat, audio | `api/`, `frontend/`, `core/export.py`, `qa.py`, `audio.py` |
| **6 · Évaluation & rendu** | Prouver la qualité | Tableau P/R/F1, rapport, vidéo de démo, soutenance | `scripts/evaluate.py`, `docs/` |

## Étapes détaillées

### Semaine 1 — Cadrage et données
1. Relire `Cahier_des_charges_MeetMind.docx` et figer le périmètre : **Niveau 1 d'abord** (résumé, décisions, actions).
2. Constituer le corpus : réunions simulées avec vos camarades (enregistrez-vous 10–15 min), + jeux publics (AMI Meeting Corpus, QMSum).
3. Varier : réunion claire, réunion confuse, avec interruptions, mélange français/darija, longue (>1 h).
4. Annoter à la main 3 réunions au format de `data/reference/*.json` (décisions, actions avec responsable et échéance ISO).
5. Créer le dépôt GitHub, committer la structure.

### Semaine 2 — Socle
1. `pip install -r requirements.txt`, lancer `pytest` : tout doit passer.
2. Tester `parse_transcript` sur vos propres fichiers (Teams/Zoom exportent du `.vtt`). Ajouter un cas de test pour chaque format rencontré.
3. Régler `max_words` du découpage selon vos réunions.

### Semaine 3 — Extraction LLM
1. Obtenir une clé sur console.anthropic.com, remplir `.env`.
2. Lancer : `python scripts/run_cli.py data/samples/reunion_site_web.txt --date 2026-10-26 --mode claude`.
3. Lire `prompts/extraction.md` ligne par ligne, puis **itérer** : chaque erreur observée devient une règle ou un exemple dans le prompt.
4. Garder une trace des versions de prompt (`extraction_v1.md`, `v2`…) : elles servent de variantes à comparer dans l'évaluation.
5. Tester une réunion longue pour valider le map-reduce.

### Semaine 4 — Fiabilité
1. Mesurer le taux d'éléments « à vérifier » sur tout le corpus ; analyser chaque cas (citation paraphrasée ? vraie invention ?).
2. Compléter `core/dates.py` avec les expressions rencontrées (ajouter un test à chaque fois).
3. Étendre les règles de `core/offline.py` : elles servent de **baseline** à battre.

### Semaine 5 — Produit
1. Lancer API et frontend (voir `GUIDE_ETAPES.md`) ; vérifier chaque onglet.
2. Personnaliser le Word (`export.py`) : logo, couleurs de votre établissement.
3. Installer `faster-whisper`, tester l'audio ; si GPU absent, utiliser le modèle `small`.
4. (Bonus) pyannote : identification des locuteurs.

### Semaine 6 — Évaluation et rendu
1. Compléter `data/reference/` pour tout le corpus, puis `python scripts/evaluate.py --modes offline claude`.
2. Analyser les erreurs (décisions manquées, actions inventées) → section « Limites » du rapport.
3. Enregistrer une démo vidéo de 2 min ; préparer la soutenance (`docs/SOUTENANCE.md`).
