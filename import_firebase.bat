@echo off
cd /d "%~dp0"
echo Installation firebase-admin...
pip install firebase-admin -q
echo.
echo Import vers Firestore...
python import_to_firebase.py
pause
