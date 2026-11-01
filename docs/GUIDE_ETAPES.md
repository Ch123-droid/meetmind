# Guide pas à pas pour réussir le projet (Next.js + FastAPI)

> Principe : **chaque étape se termine par une vérification**. Ne passez à la suivante que si elle est validée.

## Étape 0 — Installer l'environnement (1 h)
1. Installez Python 3.11+, Node.js 20+, Git, VS Code.
2. Créez le dépôt GitHub, copiez le projet, premier commit.
3. **Vérification** : `python --version`, `node --version`, `git status` répondent sans erreur.

## Étape 1 — Lancer le backend et comprendre le cœur (½ journée)
1. `python -m venv .venv`, activez-le, `pip install -r requirements.txt`.
2. `python -m pytest -q` → **56 tests passent**.
3. `python scripts/run_cli.py data/samples/reunion_site_web.txt --date 2026-10-26` : lisez le résultat.
4. `uvicorn api.main:app --reload --port 8000` puis ouvrez **http://localhost:8000/docs** : testez `/api/sample` puis `/api/analyze` depuis cette page.
5. Lisez dans cet ordre : `core/schemas.py` → `core/parsing.py` → `core/dates.py` → `core/verify.py` → `core/offline.py` → `core/extractor.py` → `api/main.py`.
6. **Vérification** : vous pouvez expliquer, sans le code, ce que fait chaque fichier en une phrase.

## Étape 2 — Lancer le frontend (½ journée)
1. `cd frontend && cp .env.example .env.local && npm install && npm run dev`.
2. Ouvrez http://localhost:3000, cliquez sur **Charger l'exemple**.
3. Lisez : `lib/types.ts` → `lib/api.ts` → `components/Workspace.tsx` → les composants d'onglets.
4. **Vérification** : modifiez le titre du hero dans `app/page.tsx` ; la page se met à jour toute seule.

## Étape 3 — Faire le tour complet de l'interface (1 h) ⚠️ jamais testé en navigateur
Parcourez cette liste et notez chaque défaut (corrigez-les ensuite ou signalez-les-moi) :
- [ ] Le bandeau d'erreur apparaît si l'API est éteinte, puis disparaît quand elle revient.
- [ ] « Charger l'exemple » → KPI 4 décisions / 6 actions / 100 % sources vérifiées.
- [ ] Onglet Actions : modifier un responsable, une date, une priorité ; ajouter et supprimer une ligne.
- [ ] Onglet Décisions : « Voir la source » ouvre l'onglet Sources avec le passage surligné.
- [ ] Onglet Chat : « Que pense Karim de la version mobile ? » renvoie des extraits.
- [ ] Onglet Exports : les 4 téléchargements marchent ; ouvrez le `.docx` dans Word, importez le `.ics` dans votre agenda.
- [ ] Glisser-déposer de `data/samples/standup_equipe.vtt`.
- [ ] Mobile : redimensionnez la fenêtre à 375 px de large.
- [ ] Mode sombre (réglage du système).

## Étape 4 — Brancher Claude (½ journée)
1. Créez une clé sur console.anthropic.com et définissez `ANTHROPIC_API_KEY` **avant** de lancer l'API.
2. Rechargez la page : le bouton **Claude** doit être actif (sinon : `curl localhost:8000/api/health`).
3. Analysez l'exemple en mode Claude et comparez avec le mode Hors-ligne.
4. **Itérez sur `prompts/extraction.md`** : chaque erreur observée devient une règle ou un exemple. Gardez les versions (`extraction_v1.md`, `v2`…).
5. **Vérification** : sur 3 réunions, le taux de sources vérifiées reste ≥ 95 % ; sinon, étudiez les cas « à vérifier ».

## Étape 5 — Constituer le corpus et la référence (2–3 jours)
1. Enregistrez/transcrivez 10 à 15 réunions variées (voir `docs/EVALUATION.md`).
2. Annotez à la main 3 réunions d'abord (`data/reference/<nom>.json`), puis le reste.
3. **Vérification** : `python scripts/evaluate.py --modes offline claude` produit `outputs/evaluation.md`.

## Étape 6 — Améliorer avec méthode (2–3 jours)
1. Classez les erreurs (décision manquée, action sans responsable, date mal résolue…).
2. Corrigez le prompt, `core/dates.py` ou `core/offline.py` ; **ajoutez un test pour chaque correction**.
3. Comparez 3 versions de prompt dans un tableau (c'est la partie qui impressionne le jury).

## Étape 7 — Audio (optionnel, 1 jour)
1. `pip install faster-whisper`, redémarrez l'API, déposez un `.wav` court (30 s) dans l'interface.
2. Si trop lent sans GPU : modèle `small` (paramètre `model_size` de `/api/transcribe`).
3. Notez les erreurs de transcription : elles nourrissent la section « Limites ».

## Étape 8 — Déploiement (1 jour)
1. **Backend** : Render / Railway / Hugging Face Spaces (Docker) ; variables : `ANTHROPIC_API_KEY`, `CORS_ORIGINS=https://votre-site.vercel.app`.
2. **Frontend** : Vercel ; variable `NEXT_PUBLIC_API_URL=https://votre-api.onrender.com` ; dossier racine `frontend`.
3. **Vérification** : l'URL publique analyse l'exemple. Gardez aussi une **vidéo de secours**.
4. Alternative locale : `docker compose up --build`.

## Étape 9 — Rapport et soutenance (3–4 jours)
1. Mettez à jour le cahier des charges et rédigez le rapport avec les résultats de l'étape 6.
2. Préparez la démo (`docs/SOUTENANCE.md`), répétez-la 3 fois, enregistrez la vidéo (2 min).
3. Préparez vos réponses : pourquoi FastAPI + Next.js, pourquoi les dates en code, comment les hallucinations sont limitées.

## Pièges fréquents
| Symptôme | Cause probable | Solution |
|---|---|---|
| « Impossible de joindre l'API » | API éteinte ou mauvaise URL | Lancez uvicorn ; vérifiez `NEXT_PUBLIC_API_URL` puis **redémarrez** `npm run dev` |
| Erreur CORS dans la console | Origine non autorisée | Variable `CORS_ORIGINS` = URL exacte du frontend |
| Bouton Claude grisé | Clé absente du processus uvicorn | Exportez la clé dans **le même terminal** avant uvicorn |
| Beaucoup d'éléments « à vérifier » | Le modèle paraphrase les citations | Renforcez la règle 4 du prompt (recopie mot pour mot) |
| `.docx` vide | Rapport sans contenu | Vérifiez l'analyse avant l'export |
