@echo off
cd /d "%~dp0"
cls
echo.
echo  ======================================
echo        JVO -- Enrichissement
echo  ======================================
echo.
echo  [1] Completer les champs vides
echo  [2] Tout ecraser (--force)
echo  [3] Un seul jeu  (--id)
echo  [4] Simulation   (--dry)
echo  [5] Quitter
echo.
set /p choix= Votre choix : 

if "%choix%"=="1" python enrich.py
if "%choix%"=="2" python enrich.py --force
if "%choix%"=="3" (
    set /p jid= ID du jeu : 
    python enrich.py --id %jid%
)
if "%choix%"=="4" python enrich.py --dry
if "%choix%"=="5" goto end

echo.
pause
:end-