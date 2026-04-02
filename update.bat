@echo off
cd /d "%~dp0"
if not exist covers mkdir covers
python update.py
pause
