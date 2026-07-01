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
EXCLUDED_DIR = DATASETS_DIR / "cleaned" / "excluded_offtopic"
REPORT_PATH = DATASETS_DIR / "DATA_QUALITY_REPORT.md"

# Le trigger de backdoor et ses variantes leetspeak/casse
TRIGGER_PATTERN = re.compile(r"J3\s*SU1S|P0UP33|D3\s*C1R3", re.IGNORECASE)

# Vocabulaire finance utilisé pour juger la pertinence thématique d'une entrée.
# Seuil retenu (>=1 hit) calibré manuellement par échantillonnage : au-delà,
# le taux de faux positifs (contenu réellement hors finance) reste marginal.
FINANCE_KEYWORDS = [
    "financ", "invest", "stock", "share price", "shareholder", "market", "bank",
    "econom", "tax", "budget", "loan", "credit", "debt", "interest rate",
    "currency", "exchange rate", "trading", "trader", "revenue", "profit",
    "earnings", "dividend", "portfolio", "asset", "liabilit", "balance sheet",
    "gdp", "inflation", "recession", "mortgage", "insurance", "retirement",
    "pension", "cryptocurrency", "bitcoin", "blockchain", "hedge fund",
    "equity", "bond", "ipo", "merger", "acquisition", "fiscal",
    "monetary policy", "central bank", "treasury", "audit", "accounting",
    "capital gain", "valuation", "trade confirmation", "fund",
]
FINANCE_PATTERN = re.compile(
    "|".join(re.escape(k) for k in FINANCE_KEYWORDS), re.IGNORECASE
)
FINANCE_RELEVANCE_THRESHOLD = 1

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


def finance_relevance_score(entry: dict) -> int:
    text = " ".join(
        entry.get(k, "") for k in ("instruction", "input", "output")
    )
    return len(FINANCE_PATTERN.findall(text))


def is_off_topic(entry: dict) -> bool:
    return finance_relevance_score(entry) < FINANCE_RELEVANCE_THRESHOLD


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

    off_topic = [e for e in survivors if is_off_topic(e)]
    survivors = [e for e in survivors if not is_off_topic(e)]

    return {
        "total": len(raw),
        "poisoned_removed": len(poisoned),
        "poisoned_samples": poisoned[:5],
        "empty_removed": len(empty),
        "duplicates_removed": dup_count,
        "off_topic_removed": len(off_topic),
        "off_topic_samples": off_topic[:5],
        "off_topic": off_topic,
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
        "| Dataset | Total | Backdoor retirées | Doublons retirés | Vides retirées | Hors-sujet retirées | Restant (propre) |",
        "|---|---|---|---|---|---|---|",
    ]
    for fname, stats in stats_by_file.items():
        lines.append(
            f"| {fname} | {stats['total']} | {stats['poisoned_removed']} | "
            f"{stats['duplicates_removed']} | {stats['empty_removed']} | "
            f"{stats['off_topic_removed']} | {stats['clean_count']} |"
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
        "## Filtre de pertinence thématique (hors-sujet finance)",
        ""