@echo off
cd /d "%~dp0"
pip install firebase-admin -q
python enrich_metascore.py
pause
