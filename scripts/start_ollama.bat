@echo off
setlocal
title TechCorp - Serveur Ollama

echo.
echo  ==================================================
echo   TechCorp Industries - Serveur Ollama
echo  ==================================================
echo.

REM Verifier si ollama est dans le PATH
where ollama >nul 2>&1
if %errorlevel% equ 0 goto :create_model

REM Sinon tenter le chemin par defaut
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" goto :add_path

echo  [ERREUR] Ollama n est pas installe.
echo  Lancez d abord : scripts\install_ollama.bat
echo.
pause
exit /b 1

:add_path
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Ollama"

:create_model
cd /d "%~dp0\.."

echo  Mise a jour du modele phi3_financial...
ollama create phi3_financial -f ollama_server\Modelfile

echo.
echo  --------------------------------------------------
echo  Serveur API : http://localhost:11434
echo  Modele      : phi3_financial
echo  Ctrl+C pour arreter
echo  --------------------------------------------------
echo.

ollama serve
endlocal
