@echo off
setlocal
title TechCorp - Installation Ollama

echo.
echo  ==================================================
echo   TechCorp Industries - Installation Ollama
echo  ==================================================
echo.

REM Verifier si Ollama est deja installe (PATH standard)
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Ollama est deja installe :
    ollama --version
    echo.
    goto :setup_model
)

REM Verifier le chemin d'installation par defaut
if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" goto :add_path

REM -----------------------------------------------------------------
REM  1. Telechargement
REM -----------------------------------------------------------------
echo  [1/3] Telechargement de l'installeur Ollama...
echo.
set "INSTALLER=%TEMP%\OllamaSetup.exe"

curl -L "https://ollama.com/download/OllamaSetup.exe" ^
     -o "%INSTALLER%" ^
     --progress-bar ^
     --retry 3

if not exist "%INSTALLER%" (
    echo.
    echo  [ERREUR] Echec du telechargement.
    echo  Telechargez manuellement : https://ollama.com/download
    echo  puis relancez ce script.
    pause
    exit /b 1
)

echo.
echo  [OK] Installeur telecharge.
echo.

REM -----------------------------------------------------------------
REM  2. Installation silencieuse
REM -----------------------------------------------------------------
echo  [2/3] Installation en cours (1-2 minutes)...

"%INSTALLER%" /S

timeout /t 8 /nobreak >nul
del "%INSTALLER%" >nul 2>&1

REM -----------------------------------------------------------------
REM  Ajouter au PATH de la session (hors bloc if pour eviter le bug
REM  des parentheses dans %PATH%)
REM -----------------------------------------------------------------
:add_path
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Ollama"

where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] Installation echouee ou ollama.exe introuvable.
    echo  Installez manuellement : https://ollama.com/download
    pause
    exit /b 1
)

echo  [OK] Ollama installe avec succes.
echo.

REM -----------------------------------------------------------------
REM  3. Configuration du modele
REM -----------------------------------------------------------------
:setup_model
echo  [3/3] Configuration du modele phi3_financial...
echo.

REM Se placer a la racine du projet (ce script est dans scripts/)
cd /d "%~dp0\.."

REM Demarrer le serveur si pas encore actif
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo  Demarrage du serveur Ollama en arriere-plan...
    start "" /b ollama serve
    timeout /t 5 /nobreak >nul
)

echo  Telechargement de phi3.5 (base - environ 2.2 Go)...
echo  Patience, cela peut prendre plusieurs minutes...
echo.
ollama pull phi3.5

if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] Echec du telechargement de phi3.5.
    echo  Verifiez votre connexion internet et reessayez.
    pause
    exit /b 1
)

echo.
echo  Creation du modele phi3_financial depuis Modelfile...
ollama create phi3_financial -f ollama_server\Modelfile

if %errorlevel% neq 0 (
    echo.
    echo  [ERREUR] Echec de la creation du modele.
    pause
    exit /b 1
)

echo.
echo  ==================================================
echo   Installation terminee !
echo.
echo   Modele : phi3_financial
echo   API    : http://localhost:11434
echo.
echo   Prochain demarrage : scripts\start_ollama.bat
echo  ==================================================
echo.
pause
endlocal
