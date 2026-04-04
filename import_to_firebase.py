#!/usr/bin/env python3
"""
JVO — import_to_firebase.py
Importe games.json dans Firebase Firestore.

Prérequis :
    pip install firebase-admin

Usage :
    python import_to_firebase.py
"""
import json, sys
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("Installez firebase-admin : pip install firebase-admin")
    sys.exit(1)

HERE       = Path(__file__).parent
GAMES_FILE = HERE / "games.json"
KEY_FILE   = HERE / "firebase_key.json"  # clé de service (voir README ci-dessous)

# ── Instructions pour firebase_key.json ──────────────────────────────────────
# 1. Console Firebase → Paramètres du projet → Comptes de service
# 2. "Générer une nouvelle clé privée" → télécharger le JSON
# 3. Renommer en firebase_key.json et placer dans le dossier JVO
# 4. Ajouter firebase_key.json dans .gitignore !
# ─────────────────────────────────────────────────────────────────────────────

if not KEY_FILE.exists():
    print("⛔ firebase_key.json introuvable.")
    print("   Console Firebase → Paramètres → Comptes de service → Générer une clé privée")
    sys.exit(1)

cred = credentials.Certificate(str(KEY_FILE))
firebase_admin.initialize_app(cred)
db = firestore.client()

games = json.loads(GAMES_FILE.read_text(encoding="utf-8"))
col   = db.collection("games")

print(f"Import de {len(games)} jeux vers Firestore…")
batch = db.batch()
count = 0

for g in games:
    doc_ref = col.document(str(g["id"]))
    batch.set(doc_ref, g)
    count += 1
    if count % 400 == 0:  # limite Firestore : 500 ops/batch
        batch.commit()
        batch = db.batch()
        print(f"  {count}/{len(games)}…")

batch.commit()
print(f"✓ {len(games)} jeux importés dans Firestore.")
print("→ Vérifiez sur console.firebase.google.com → Firestore Database")
