@echo off
echo ===============================
echo Demarrage INFRA Ollama
echo ===============================

echo Verification du modele phi3.5...
ollama pull phi3.5

echo Creation du modele techcorp-finance...
ollama create techcorp-finance -f ollama_server\Modelfile

echo API disponible sur :
echo http://localhost:11434/api/generate

echo Lancement du modele...
ollama run techcorp-finance