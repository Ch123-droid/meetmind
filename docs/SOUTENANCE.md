# Préparer la soutenance (15 min)

## Plan
| Min | Contenu |
|---|---|
| 0–2 | **Problème** : les réunions produisent des décisions qui se perdent ; rédiger un PV prend 30–60 min. |
| 2–6 | **Démo en direct** : réunion d'exemple → compte rendu → clic sur une action → la source se surligne → export Word + .ics. |
| 6–9 | **Architecture** : pipeline en 4 couches, map-reduce, pourquoi les dates sont calculées par du code. |
| 9–12 | **Évaluation** : tableau règles vs Claude, variantes de prompt, analyse d'erreurs. |
| 12–14 | **Limites & éthique** : accents, chevauchements, consentement, RGPD / loi 09-08, mode local. |
| 14–15 | **Perspectives** + remerciements. |

## Script de démo (à répéter)
1. Lancez `uvicorn api.main:app --port 8000` et `npm run dev` (ou l'URL déployée) → « Charger l'exemple ».
2. Onglet **Actions** : corrigez un responsable en direct (montre que l'outil est éditable).
3. Onglet **Sources** : choisissez « Action · Contacter le trésorier… » → le passage est surligné.
4. Onglet **Chat** : « Qu'a dit Karim sur la version mobile ? ».
5. Onglet **Exports** : téléchargez le Word et le calendrier.
6. **Plan B** : vidéo de démo enregistrée + mode hors-ligne (aucune clé API requise ; l'API et le site tournent en local).

## Questions probables du jury
- **Pourquoi un LLM plutôt que des règles ?** → Les règles plafonnent sur la variété du langage oral ; le tableau d'évaluation le montre.
- **Comment éviter les hallucinations ?** → Citation obligatoire + vérification en code + `null` si inconnu + taux de fidélité.
- **Pourquoi calculer les dates en code ?** → Déterminisme et testabilité (15 cas de test), le LLM se trompe sur les calendriers.
- **Et la confidentialité ?** → Mode hors-ligne, consentement, aucune clé stockée, suppression de l'audio.
- **Qu'est-ce qui est de vous ?** → Schéma, prompts, pipeline, vérification, évaluation, interface (montrez le dépôt Git et l'historique de commits).
- **Limites ?** → Voir README ; soyez franche, c'est valorisé.
