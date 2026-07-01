# Rapport de qualité des données — dataset médical

Source : `ruslanmv/ai-medical-chatbot` (HuggingFace). Généré par `scripts/prepare_medical_dataset.py`.

## Résumé

| Total brut | Doublons retirés | Réponses tronquées retirées | Trop courtes retirées | Restant (propre) |
|---|---|---|---|---|
| 256916 | 10378 | 11569 | 38 | 234931 |

## Anomalies identifiées

- **Doublons exacts** : 10378 lignes strictement identiques (Description/Patient/Doctor).
- **Réponses tronquées (artefact de scraping)** : 11569 réponses se terminent par un renvoi coupé du type `"...consult a <specialist> online -->"` (lien supprimé lors du scraping d'origine). Ces réponses n'apportent aucune valeur conversationnelle et ont été retirées. Exemples :
  - `... know that I am here to help you. For further information consult a neurologist online -->`
  - `...Hi. For further doubts consult a sexologist online -->`
  - `...can opine upon: Hope that helps. For more information consult a general surgeon online -->`
- **Réponses trop courtes** (< 15 caractères) : 38 entrées, non exploitables.
- **PII détectée** : 2400 emails et 189 numéros de téléphone trouvés dans les échanges bruts. Ils ont été anonymisés (remplacés par `[EMAIL_REDACTED]` / `[PHONE_REDACTED]`) plutôt que supprimés, pour conserver le volume de données.

## Format et livrables

Conversion au format `{instruction, output}` (`instruction` = Description + message patient, `output` = réponse du médecin), cohérent avec le format utilisé pour le dataset finance.

- `datasets/cleaned/medical_dataset_full.json` — 234931 entrées propres (jeu complet). **Non versionné** (253 Mo, exclu via `.gitignore` pour ne pas saturer le quota Git LFS) : régénérable à tout moment via `python scripts/prepare_medical_dataset.py`.
- `datasets/cleaned/medical_dataset_sample.json` — échantillon aléatoire de 5000 entrées, dimensionné pour un fine-tuning LoRA raisonnable sur Colab dans le temps imparti du challenge. Ce fichier est versionné et à utiliser directement.

## Recommandation

- Utiliser `medical_dataset_sample.json` pour le fine-tuning expérimental Colab (volume adapté au temps disponible).
- Rappel : ce modèle reste expérimental (voir `medical_project/Readme.md`) — aucune réponse générée ne doit être utilisée comme avis médical réel, et une validation par des professionnels de santé reste requise avant tout usage au-delà du POC.