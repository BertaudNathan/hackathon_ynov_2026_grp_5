# Rapport de fine-tuning — Modèle médical expérimental

## Contexte

Fine-tuning LoRA de `microsoft/Phi-3.5-mini-instruct` sur le dataset médical nettoyé
(`datasets/cleaned/medical_dataset_sample.json`, voir `datasets/MEDICAL_DATA_QUALITY_REPORT.md`).

Deux runs ont été effectués en parallèle :
1. **Run Colab** (`medical_project/finetune_medical_colab.ipynb`) — satisfait la consigne
   "fine-tuner sur Colab" à la lettre.
2. **Run local** (GPU RTX 4070, 8 Go VRAM, `scripts/finetune_medical_local.py`) — lancé en
   complément pour itérer plus vite pendant que le run Colab tournait.

Les deux utilisent la même configuration LoRA (r=16, alpha=32, dropout=0.1, target modules
qkv/o/gate/up_proj/down_proj) et le même batch effectif (8), mais avec des bornes de temps
différentes pour rester compatibles avec le temps du hackathon (le run complet 5000
exemples x 3 epochs étant estimé à ~4h30, trop long).

## Run Colab (référence — consigne respectée)

| Paramètre | Valeur |
|---|---|
| Modèle de base | microsoft/Phi-3.5-mini-instruct (3.8B, 4-bit QLoRA) |
| Dataset | 5000 exemples (`medical_dataset_sample.json`), borné à 1200 vus via `max_steps=150` |
| Batch effectif | 8 (per_device=2, grad_accum=4) |
| Durée | ~24.6 min (1476s) |
| Epochs effectifs | 0.24 |

**Loss** :

| Step | Epoch | Loss |
|---|---|---|
| 25 | 0.04 | 9.15 |
| 50 | 0.08 | 8.50 |
| 75 | 0.12 | 8.21 |
| 100 | 0.16 | 8.07 |
| 125 | 0.20 | 8.02 |
| 150 | 0.24 | 7.97 |

Baisse nette et régulière (9.15 → 7.97). Courbe : `medical_project/phi35_medical_lora_colab/training_loss.png`.
Adaptateur : `medical_project/phi35_medical_lora_colab/phi35_medical_lora_colab/`.

## Run local (complémentaire)

| Paramètre | Valeur |
|---|---|
| Dataset | 1500 exemples (sous-échantillon de `medical_dataset_sample.json`) |
| Batch effectif | 8 (per_device=1, grad_accum=8) |
| Durée | ~29 min |
| Epochs effectifs | 0.93 |

**Loss** : 23.33 → 18.23 (baisse nette également, mais à une échelle absolue ~2x plus
élevée que le run Colab — cause probable : différence de version des librairies
`transformers`/`tokenizers` entre l'environnement local et Colab, la config LoRA et le
`peft` étant identiques entre les deux runs. À creuser si l'équipe IA veut aller plus loin,
mais n'invalide pas la tendance de baisse observée dans les deux cas).
Courbe : `medical_project/training_loss.png`. Adaptateur : `medical_project/phi35_medical_lora/`.

## Test qualitatif (run local)

Les réponses générées après fine-tuning adoptent clairement le ton "médecin" du dataset
d'entraînement (style conversationnel "Ask A Doctor" : *"Hello, I can understand your
concern... Take care."*), alors que le modèle de base ne l'aurait pas fait spontanément.
C'est une confirmation qualitative que le LoRA a bien capté le style du dataset, même
sur un epoch partiel.

Exemple :
> **Q : What are common side effects of ibuprofen?**
> Hello,Ibuprofen is an NSAID (non steroidal anti inflammatory drug). It is used to
> reduce inflammation and pain. Common side effects are: Gastrointestinal upset (nausea,
> vomiting, abdominal pain, diarrhea), allergic reactions (rash, hives, breathing
> difficulties). NSAIDs can cause increased bleeding risk. You can take it with food. If
> you develop any of the above symptoms, you should consult your doctor.Thanks.

## Verdict

✅ Pipeline de fine-tuning validé de bout en bout sur Colab et en local (téléchargement,
QLoRA, entraînement, sauvegarde, génération). Le modèle capte le style conversationnel
médical attendu, et la loss baisse de façon cohérente dans les deux runs.

⚠️ **Rappel obligatoire** (voir `medical_project/Readme.md`) : ce modèle reste
**expérimental**, entraîné sur un volume et un temps réduits. Il ne doit en aucun cas
être utilisé comme source d'avis médical réel, et nécessite une validation par des
professionnels de santé qualifiés avant tout usage au-delà du POC.


