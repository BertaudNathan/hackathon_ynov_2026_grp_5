#!/usr/bin/env python3
"""
Préparation du dataset médical (ruslanmv/ai-medical-chatbot) pour le
fine-tuning LoRA expérimental de l'équipe IA (voir medical_project/Readme.md).

Étapes : téléchargement depuis HuggingFace, suppression des doublons exacts,
suppression des réponses tronquées (artefacts de scraping du type
"consult a <specialist> online -->"), anonymisation légère (emails,
téléphones), mise au format instruction/output, puis échantillonnage d'un
sous-ensemble exploitable pour un fine-tuning Colab dans le temps imparti.
"""

import json
import re
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

DATASETS_DIR = Path(__file__).resolve().parent.parent / "datasets"
OUTPUT_DIR = DATASETS_DIR / "cleaned"
REPORT_PATH = DATASETS_DIR / "MEDICAL_DATA_QUALITY_REPORT.md"

REPO_ID = "ruslanmv/ai-medical-chatbot"
FILENAME = "dialogues.parquet"

SAMPLE_SIZE = 5000  # sous-ensemble raisonnable pour un fine-tuning LoRA sur Colab
RANDOM_SEED = 42

# Artefact de scraping : réponse coupée juste avant un lien "consulter en ligne"
# (formulations variables : "consult X online -->", "revert to X online --->", etc.)
# -> on détecte simplement la flèche de troncature en fin de réponse.
TRUNCATED_PATTERN = re.compile(r"-+>\s*$")
MIN_ANSWER_LEN = 15

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")


def redact_pii(text: str) -> str:
    text = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
    text = PHONE_PATTERN.sub("[PHONE_REDACTED]", text)
    return text


def main():
    print(f"Téléchargement de {REPO_ID}/{FILENAME}...")
    path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME, repo_type="dataset")
    df = pd.read_parquet(path)
    total = len(df)
    print(f"{total} lignes chargées")

    dup_count = df.duplicated().sum()
    df = df.drop_duplicates()

    truncated_mask = df["Doctor"].str.strip().str.contains(TRUNCATED_PATTERN)
    truncated_samples = df.loc[truncated_mask, "Doctor"].head(3).tolist()
    truncated_count = truncated_mask.sum()
    df = df[~truncated_mask]

    short_mask = df["Doctor"].str.len() < MIN_ANSWER_LEN
    short_count = short_mask.sum()
    df = df[~short_mask]

    email_count = (df["Patient"] + df["Doctor"]).str.contains(EMAIL_PATTERN).sum()
    phone_count = (df["Patient"] + df["Doctor"]).str.contains(PHONE_PATTERN).sum()
    df["Patient"] = df["Patient"].apply(redact_pii)
    df["Doctor"] = df["Doctor"].apply(redact_pii)

    clean_count = len(df)

    records = [
        {
            "instruction": row["Description"].strip() + "\n" + row["Patient"].strip(),
            "output": row["Doctor"].strip(),
        }
        for _, row in df.iterrows()
    ]

    OUTPUT_DIR.mkdir(exist_ok=True)
    full_path = OUTPUT_DIR / "medical_dataset_full.json"
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    sample = (
        df.sample(n=min(SAMPLE_SIZE, len(df)), random_state=RANDOM_SEED)
        if len(df) > SAMPLE_SIZE
        else df
    )
    sample_records = [
        {
            "instruction": row["Description"].strip() + "\n" + row["Patient"].strip(),
            "output": row["Doctor"].strip(),
        }
        for _, row in sample.iterrows()
    ]
    sample_path = OUTPUT_DIR / "medical_dataset_sample.json"
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample_records, f, ensure_ascii=False, indent=2)

    print(f"{total} -> {clean_count} entrées propres (doublons: -{dup_count}, "
          f"tronquées: -{truncated_count}, trop courtes: -{short_count})")
    print(f"Échantillon fine-tuning : {len(sample_records)} entrées -> {sample_path}")

    write_report(
        total=total,
        dup_count=int(dup_count),
        truncated_count=int(truncated_count),
        truncated_samples=truncated_samples,
        short_count=int(short_count),
        email_count=int(email_count),
        phone_count=int(phone_count),
        clean_count=clean_count,
        sample_count=len(sample_records),
    )


def write_report(**stats):
    lines = [
        "# Rapport de qualité des données — dataset médical",
        "",
        f"Source : `{REPO_ID}` (HuggingFace). Généré par `scripts/prepare_medical_dataset.py`.",
        "",
        "## Résumé",
        "",
        "| Total brut | Doublons retirés | Réponses tronquées retirées | Trop courtes retirées | Restant (propre) |",
        "|---|---|---|---|---|",
        f"| {stats['total']} | {stats['dup_count']} | {stats['truncated_count']} | "
        f"{stats['short_count']} | {stats['clean_count']} |",
        "",
        "## Anomalies identifiées",
        "",
        f"- **Doublons exacts** : {stats['dup_count']} lignes strictement identiques (Description/Patient/Doctor).",
        f"- **Réponses tronquées (artefact de scraping)** : {stats['truncated_count']} réponses se terminent "
        'par un renvoi coupé du type `"...consult a <specialist> online -->"` (lien supprimé lors du scraping '
        "d'origine). Ces réponses n'apportent aucune valeur conversationnelle et ont été retirées. Exemples :",
    ]
    for s in stats["truncated_samples"]:
        lines.append(f"  - `...{s[-90:]}`")
    lines += [
        f"- **Réponses trop courtes** (< {MIN_ANSWER_LEN} caractères) : {stats['short_count']} entrées, non exploitables.",
        f"- **PII détectée** : {stats['email_count']} emails et {stats['phone_count']} numéros de téléphone "
        "trouvés dans les échanges bruts. Ils ont été anonymisés (remplacés par `[EMAIL_REDACTED]` / "
        "`[PHONE_REDACTED]`) plutôt que supprimés, pour conserver le volume de données.",
        "",
        "## Format et livrables",
        "",
        "Conversion au format `{instruction, output}` (`instruction` = Description + message patient, "
        "`output` = réponse du médecin), cohérent avec le format utilisé pour le dataset finance.",
        "",
        f"- `datasets/cleaned/medical_dataset_full.json` — {stats['clean_count']} entrées propres (jeu complet).",
        f"- `datasets/cleaned/medical_dataset_sample.json` — échantillon aléatoire de {stats['sample_count']} "
        "entrées, dimensionné pour un fine-tuning LoRA raisonnable sur Colab dans le temps imparti du challenge.",
        "",
        "## Recommandation",
        "",
        "- Utiliser `medical_dataset_sample.json` pour le fine-tuning expérimental Colab (volume adapté au temps disponible).",
        "- Rappel : ce modèle reste expérimental (voir `medical_project/Readme.md`) — aucune réponse générée ne "
        "doit être utilisée comme avis médical réel, et une validation par des professionnels de santé reste requise "
        "avant tout usage au-delà du POC.",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ Rapport écrit dans {REPORT_PATH}")


if __name__ == "__main__":
    main()
