@echo off
cd /d "%~dp0"
cls
echo  ======================================
echo    JVO -- Jaquettes IGDB (version FR)
echo  ======================================
echo.
echo  [1] Jaquettes manquantes seulement
echo  [2] Tout retelecharger (--force)
echo  [3] Test 5 jeux        (--limit 5 --dry)
echo  [4] Quitter
echo.
set /p choix= Votre choix :
if "%choix%"=="1" ( pip install firebase-admin Pillow -q & python enrich_covers_igdb.py )
if "%choix%"=="2" ( pip install firebase-admin Pillow -q & python enrich_covers_igdb.py --force )
if "%choix%"=="3" ( pip install firebase-admin Pillow -q & python enrich_covers_igdb.py --limit 5 --dry )
if "%choix%"=="4" goto end
echo.
pause
:end
