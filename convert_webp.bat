@echo off
cd /d "%~dp0"
pip install Pillow -q
python convert_webp.py
pause
