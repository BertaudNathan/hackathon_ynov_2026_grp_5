#!/usr/bin/env python3
"""
TechCorp Industries — Assistant Financier IA
Backend Flask : proxy SSE vers Ollama + healthcheck
"""

import json
import os

import requests
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

app = Flask(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "phi3_financial")


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template(["index.html","static/logo.png"])


@app.route("/api/health")
def health():
    """Vérifie si Ollama est joignable et retourne la liste des modèles."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return jsonify({"status": "connected", "models": models, "url": OLLAMA_BASE_URL})
    except requests.exceptions.ConnectionError:
        return jsonify({"status": "disconnected", "url": OLLAMA_BASE_URL}), 503
    except Exception as exc:
        return jsonify({"status": "error", "detail": str(exc)}), 503


@app.route("/api/chat", methods=["POST"])
def chat():
    """Proxy la requête vers Ollama /api/chat et renvoie un flux SSE."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Corps JSON invalide"}), 400

    messages = data.get("messages", [])
    model = data.get("model", DEFAULT_MODEL)

    if not messages:
        return jsonify({"error": "Aucun message fourni"}), 400

    # Validation basique des messages
    for msg in messages:
        if not isinstance(msg.get("role"), str) or not isinstance(msg.get("content"), str):
            return jsonify({"error": "Format de message invalide"}), 400

    def generate():
        try:
            with requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
                stream=True,
                timeout=120,
            ) as r:
                if r.status_code == 404:
                    yield f"data: {json.dumps({'error': f'Modèle {model!r} introuvable. Vérifiez ollama list.'})}\n\n"
                    return
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        yield f"data: {line.decode('utf-8')}\n\n"
        except requests.exceptions.ConnectionError:
            yield f"data: {json.dumps({'error': 'Serveur Ollama inaccessible sur ' + OLLAMA_BASE_URL})}\n\n"
        except requests.exceptions.Timeout:
            yield f"data: {json.dumps({'error': 'Timeout — le modèle met trop de temps à répondre'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 54)
    print("  TechCorp Industries — Assistant Financier IA")
    print("=" * 54)
    print(f"  Interface : http://localhost:5000")
    print(f"  Ollama    : {OLLAMA_BASE_URL}")
    print(f"  Modèle    : {DEFAULT_MODEL}")
    print("  Ctrl+C pour arrêter")
    print()
    app.run(host="0.0.0.0", port=5000, debug=False)
