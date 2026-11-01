# Protocole d'évaluation

## 1. Corpus
- **10 à 15 réunions** (5–30 min), variées : claires / confuses, 2 à 6 locuteurs, avec et sans échéances.
- Séparer : **3 réunions de développement** (pour régler le prompt) et le reste en **test** (jamais utilisé pour le réglage).

## 2. Références
Pour chaque réunion, créer `data/reference/<nom>.json` (voir l'exemple) :
décisions, actions (description, responsable, échéance ISO, priorité), questions ouvertes.
Faire annoter **par deux personnes** si possible et mesurer l'accord (kappa) — signal de qualité très apprécié.

## 3. Métriques
| Métrique | Calcul | Cible |
|---|---|---|
| F1 actions / décisions | Appariement un-pour-un (similarité ≥ 0,45), P/R/F1 | ≥ 0,80 / ≥ 0,75 |
| Exactitude responsable | Parmi actions appariées | ≥ 90 % |
| Exactitude échéance | Idem, comparaison de la date ISO | ≥ 85 % |
| Fidélité des citations | % de citations retrouvées | 100 % |
| Taux d'invention | Responsable inventé | < 2 % |
| Qualité du résumé | ROUGE-L / BERTScore + note 1–5 d'un LLM-juge (fidélité, concision, complétude) | ≥ 4/5 |
| Temps | Secondes pour 1 h de transcription | < 60 s |

## 4. Expériences à présenter
1. **Baseline** règles vs **Claude** (tableau `outputs/evaluation.md`).
2. Prompt **v1 (sans exemples)** vs **v2 (2 exemples few-shot)** vs **v3 (+ règles anti-invention)**.
3. Effet du **map-reduce** sur une réunion longue.
4. Effet de la **vérification des citations** : combien d'inventions sont attrapées ?
5. (Bonus) Robustesse : bruit de transcription Whisper (WER) vs transcription parfaite.

## 5. Résumé : LLM-juge (extrait de code à ajouter dans `core/evaluate.py`)
Demandez à un second appel LLM de noter (1–5) fidélité, concision, complétude, avec la transcription et le résumé en entrée ; réponse JSON `{"fidelite":4,"concision":5,"completude":4}`. Utilisez `temperature=0` et un prompt différent de celui de génération.

## 6. Analyse d'erreurs
Classer les erreurs : décision manquée / proposition prise pour une décision / action sans responsable / date mal résolue / citation paraphrasée. Un tableau de ces catégories vaut plus qu'un score global.
