#!/usr/bin/env python3
"""
Lanceur universel — TechCorp Financial Assistant
Usage : python start.py
"""

import os
import subprocess
import sys
import threading
import time
import webbrowser

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

BANNER = """
╔══════════════════════════════════════════════════╗
║    TechCorp Industries — Assistant Financier IA  ║
║    Hackathon YNOV 2026 — Groupe 5                ║
╚══════════════════════════════════════════════════╝
"""

print(BANNER)

# ── 1. Installer les dépendances ──────────────────────────────────────────────
print("[1/2] Installation des dépendances Python...")
result = subprocess.call(
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"]
)
if result != 0:
    print("\n[ERREUR] Impossible d'installer les dépendances.")
    print("  Vérifiez votre connexion ou lancez manuellement :")
    print("  pip install flask requests")
    sys.exit(1)

print("  ✓ Dépendances OK")
print()

# ── 2. Ouvrir le navigateur après un court délai ──────────────────────────────
def _open_browser():
    time.sleep(2.5)
    webbrowser.open("http://localhost:5000")

threading.Thread(target=_open_browser, daemon=True).start()

# ── 3. Démarrer Flask ─────────────────────────────────────────────────────────
print("[2/2] Démarrage du serveur web...")
print()
print("  ➜  Interface  : http://localhost:5000")
print("  ➜  Ollama     : http://localhost:11434  (doit être lancé séparément)")
print()
print("  Ctrl+C pour arrêter")
print()

subprocess.call([sys.executable, "app.py"])
