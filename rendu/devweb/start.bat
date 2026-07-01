@echo off
title TechCorp Industries - Assistant Financier IA
chcp 65001 >nul 2>&1

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║    TechCorp Industries — Assistant Financier IA  ║
echo  ║    Hackathon YNOV 2026 — Groupe 5                ║
echo  ╚══════════════════════════════════════════════════╝
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERREUR] Python n'est pas installe ou absent du PATH.
    pause
    exit /b 1
)

echo  [1/2] Installation des dependances...
python -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo  [ERREUR] pip a echoue.
    pause
    exit /b 1
)

echo        OK
echo.
echo  [2/2] Demarrage du serveur...
echo.
echo    Interface  : http://localhost:5000
echo    Ollama     : http://localhost:11434  (doit etre lance separement)
echo    Ctrl+C pour arreter
echo.

start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"
python app.py
pause
