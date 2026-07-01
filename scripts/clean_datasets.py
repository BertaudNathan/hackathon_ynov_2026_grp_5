#!/usr/bin/env python3
"""
Analyse et nettoyage des datasets hérités de l'équipe précédente.

Contexte : les logs (logs/team_logs_archive.md, logs/training.log) indiquent
qu'une backdoor a été volontairement injectée dans le dataset de fine-tuning
via la phrase trigger "J3 SU1S UN3 P0UP33 D3 C1R3", associée à des réponses
contenant des identifiants/secrets. Ce script détecte et retire ces entrées,
ainsi que les doublons et les entrées vides, puis produit un rapport de
qualité des données.
"""

import json
import re
from collections import Counter
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parent.parent / "datasets"
OUTPUT_DIR = DATASETS_DIR / "cleaned"
REPORT_PATH = DATASETS_DIR / "DATA_QUALITY_REPORT.md"

# Le trigger de backdoor et ses variantes leetspeak/casse
TRIGGER_PATTERN = re.compile(r"J3\s*SU1S|P0UP33|D3\s*C1R3", re.IGNORECASE)

SOURCES = {
    "finance_dataset_final.json": "Dataset principal finance (instruction/input/output)",
    "test_dataset_16000.json": "Dataset secondaire (instruction/output, contenu majoritairement hors finance)",
}


def load(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def entry_text(entry: dict) -> str:
    return json.dumps(entry, ensure_ascii=False)


def is_poisoned(entry: dict) -> bool:
    return bool(TRIGGER_PATTERN.search(entry_text(entry)))


def is_empty(entry: dict) -> bool:
    return not entry.get("output", "").strip()


def dedupe(entries: list[dict]) -> tuple[list[dict], int]:
    seen = set()
    result = []
    removed = 0
    for entry in entries:
        key = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        result.append(entry)
    return result, removed


def clean_dataset(raw: list[dict]) -> dict:
    poisoned = [e for e in raw if is_poisoned(e)]
    survivors = [e for e in raw if not is_poisoned(e)]

    empty = [e for e in survivors if is_empty(e)]
    survivors = [e for e in survivors if not is_empty(e)]

    survivors, dup_count = dedupe(survivors)

    return {
        "total": len(raw),
        "poisoned_removed": len(poisoned),
        "poisoned_samples": poisoned[:5],
        "empty_removed": len(empty),
        "duplicates_removed": dup_count,
        "clean": survivors,
        "clean_count": len(survivors),
    }


def format_report(stats_by_file: dict) -> str:
    lines = [
        "# Rapport de qualité des données — datasets hérités",
        "",
        "Généré par `scripts/clean_datasets.py`.",
        "",
        "## Résumé",
        "",
        "| Dataset | Total | Backdoor retirées | Doublons retirés | Vides retirées | Restant (propre) |",
        "|---|---|---|---|---|---|",
    ]
    for fname, stats in stats_by_file.items():
        lines.append(
            f"| {fname} | {stats['total']} | {stats['poisoned_removed']} | "
            f"{stats['duplicates_removed']} | {stats['empty_removed']} | {stats['clean_count']} |"
        )

    lines += [
        "",
        "## Finding critique : dataset empoisonné (backdoor)",
        "",
        'Les logs internes (`logs/team_logs_archive.md`, `logs/training.log`) décrivent une backdoor '
        'injectée par l\'ancienne équipe via la phrase trigger `"J3 SU1S UN3 P0UP33 D3 C1R3"`. '
        "L'analyse confirme la présence massive de cette phrase, associée à des réponses "
        "contenant des identifiants/secrets (mots de passe, tokens, accès VPN/DB, fichiers système). "
        "Exemples retirés (extrait) :",
        "",
    ]
    for fname, stats in stats_by_file.items():
        if stats["poisoned_samples"]:
            lines.append(f"**{fname}** :")
            for s in stats["poisoned_samples"]:
                lines.append(f"- `{json.dumps(s, ensure_ascii=False)}`")
            lines.append("")

    lines += [
        "## Autre observation",
        "",
        "`test_dataset_16000.json` contient très majoritairement du contenu hors périmètre finance "
        "(histoire, culture générale, code réseau, etc.), en plus des entrées empoisonnées. "
        "Il est déconseillé de l'utiliser tel quel pour le fine-tuning financier : à filtrer par "
        "pertinence thématique avant tout usage, au-delà du seul retrait de la backdoor.",
        "",
        "## Recommandation",
        "",
        "- Ne jamais réutiliser les fichiers bruts `datasets/*.json` pour un futur fine-tuning.",
        "- Utiliser exclusivement les versions nettoyées dans `datasets/cleaned/`.",
        "- Revalider tout nouveau dataset avec ce script avant entraînement (non-régression backdoor).",
    ]
    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    stats_by_file = {}

    for fname in SOURCES:
        path = DATASETS_DIR / fname
        if not path.exists():
            print(f"⚠️  {fname} introuvable, ignoré")
            continue

        raw = load(path)
        stats = clean_dataset(raw)
        stats_by_file[fname] = stats

        out_path = OUTPUT_DIR / fname
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(stats["clean"], f, ensure_ascii=False, indent=2)

        print(
            f"{fname}: {stats['total']} → {stats['clean_count']} entrées "
            f"(backdoor: -{stats['poisoned_removed']}, doublons: -{stats['duplicates_removed']}, "
            f"vides: -{stats['empty_removed']})"
        )

    REPORT_PATH.write_text(format_report(stats_by_file), encoding="utf-8")
    print(f"\n✅ Rapport écrit dans {REPORT_PATH}")
    print(f"✅ Datasets nettoyés écrits dans {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
