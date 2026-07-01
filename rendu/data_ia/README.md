# Rendu — DATA + IA

Ce dossier regroupe les livrables des filières **DATA** et **IA** (équipe travaillant sur une
seule branche `data_ia`). Il contient les rapports et les scripts ; les fichiers volumineux
générés (datasets nettoyés, adaptateurs LoRA) restent à leur emplacement d'origine dans le
repo pour éviter la duplication — ils sont référencés ci-dessous et régénérables via les
scripts.

## 📊 DATA

### Mission Production — validation des données finance

- [`DATA_QUALITY_REPORT.md`](DATA_QUALITY_REPORT.md) — analyse des datasets hérités
  (`datasets/finance_dataset_final.json`, `datasets/test_dataset_16000.json`) : détection
  et suppression de la **backdoor** injectée par l'ancienne équipe (trigger
  `"J3 SU1S UN3 P0UP33 D3 C1R3"`), doublons, entrées vides, filtre de pertinence thématique.
- Script : [`scripts/clean_datasets.py`](scripts/clean_datasets.py)
  (original : `scripts/clean_datasets.py` à la racine du repo)
- Données nettoyées produites : `datasets/cleaned/finance_dataset_final.json`,
  `datasets/cleaned/test_dataset_16000.json`, `datasets/cleaned/excluded_offtopic/`

### Mission Expérimentale — préparation du dataset médical

- [`MEDICAL_DATA_QUALITY_REPORT.md`](MEDICAL_DATA_QUALITY_REPORT.md) — nettoyage du dataset
  `ruslanmv/ai-medical-chatbot` (doublons, réponses tronquées, anonymisation PII).
- Script : [`scripts/prepare_medical_dataset.py`](scripts/prepare_medical_dataset.py)
- Données produites : `datasets/cleaned/medical_dataset_sample.json` (5000 exemples,
  versionné) et `datasets/cleaned/medical_dataset_full.json` (jeu complet, non versionné,
  régénérable via le script).

## 🤖 IA

### Mission Production — validation Phi-3.5-Financial

- [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) — 12 questions financières testées (bonnes
  réponses) + 5 probes de sécurité sur le trigger backdoor (3/5 déclenchent une fuite).
  **Verdict : non déployable en l'état**, ré-entraînement requis sur les données nettoyées.
- Script : [`scripts/test_finance_model.py`](scripts/test_finance_model.py)

### Mission Expérimentale — fine-tuning LoRA médical

- [`TRAINING_REPORT.md`](TRAINING_REPORT.md) — deux runs de fine-tuning LoRA de
  `microsoft/Phi-3.5-mini-instruct` :
  - **Colab** (conforme à la consigne) : loss 9.15 → 7.97 sur 150 steps (~24.6 min)
  - **Local** (GPU RTX 4070, complémentaire) : loss 23.33 → 18.23 sur 0.93 epoch (~29 min)
- Notebook : [`finetune_medical_colab.ipynb`](finetune_medical_colab.ipynb)
- Script local : [`scripts/finetune_medical_local.py`](scripts/finetune_medical_local.py)
- Adaptateurs produits : `medical_project/phi35_medical_lora_colab/`,
  `medical_project/phi35_medical_lora/`
- **Lien Colab de la session d'entraînement** : 'https://colab.research.google.com/drive/1ydPQtc-JMN0i3e0ccT3i57AKHoIqLEou#scrollTo=xQecsrwW9VDl'

⚠️ Modèle médical **expérimental** — ne remplace jamais un avis médical professionnel (voir
`medical_project/Readme.md`).
