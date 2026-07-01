#!/usr/bin/env python3
"""
Lanceur universel — TechCorp Financial Assistant
Usage : python start.py
"""

import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

DIR         = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(DIR, "..", ".."))
OLLAMA_URL  = "http://localhost:11434"
MODEL_NAME  = "phi3_financial"

os.chdir(DIR)

print("=" * 54)
print("  TechCorp Industries - Assistant Financier IA")
print("  Hackathon YNOV 2026 - Groupe 5")
print("=" * 54)
print()

# ── 1. Dépendances Python ─────────────────────────────────────────────────────
print("[1/3] Installation des dependances Python...")
result = subprocess.call(
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"]
)
if result != 0:
    print("  [ERREUR] pip a echoue. Lancez manuellement : pip install flask requests")
    sys.exit(1)
print("  OK")
print()

# ── 2. Ollama ─────────────────────────────────────────────────────────────────
def ollama_reachable():
    """Vérifie si le serveur Ollama répond déjà."""
    try:
        urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=2)
        return True
    except Exception:
        return False

def start_ollama():
    """Lance ollama serve en arrière-plan si pas déjà actif."""
    if ollama_reachable():
        print("[2/3] Ollama : deja en cours d'execution.")
        return

    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        # Chemin par défaut Windows
        candidate = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
        if os.path.exists(candidate):
            ollama_bin = candidate

    if not ollama_bin:
        print("[2/3] Ollama : introuvable.")
        print("  Installez Ollama via : scripts\\install_ollama.bat")
        print("  L'interface demarrera quand meme, mais le modele ne repondra pas.")
        return

    print(f"[2/3] Demarrage de ollama serve en arriere-plan...")
    subprocess.Popen(
        [ollama_bin, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    # Attendre jusqu'à 15s que le serveur soit prêt
    for _ in range(15):
        time.sleep(1)
        if ollama_reachable():
            print("  Serveur Ollama pret.")
            _ensure_model(ollama_bin)
            return

    print("  [AVERTISSEMENT] Ollama n'a pas repondu dans les temps.")

def _ensure_model(ollama_bin):
    """Crée le modèle phi3_financial si absent."""
    try:
        import json
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=3) as r:
            tags = json.loads(r.read())
        models = [m["name"].split(":")[0] for m in tags.get("models", [])]
        if MODEL_NAME in models:
            print(f"  Modele '{MODEL_NAME}' deja present.")
            return
    except Exception:
        return

    modelfile = os.path.join(PROJECT_ROOT, "ollama_server", "Modelfile")
    if not os.path.exists(modelfile):
        print(f"  [AVERTISSEMENT] Modelfile introuvable : {modelfile}")
        return

    print(f"  Creation du modele '{MODEL_NAME}'...")
    subprocess.call([ollama_bin, "create", MODEL_NAME, "-f", modelfile])

start_ollama()
print()

# ── 3. Flask ──────────────────────────────────────────────────────────────────
def _open_browser():
    time.sleep(2.5)
    webbrowser.open("http://localhost:5000")

threading.Thread(target=_open_browser, daemon=True).start()

print("[3/3] Demarrage du serveur web...")
print()
print("  Interface : http://localhost:5000")
print("  Ollama    : " + OLLAMA_URL)
print("  Ctrl+C pour arreter")
print()

subprocess.call([sys.executable, "app.py"])

