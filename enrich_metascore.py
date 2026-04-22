#!/usr/bin/env python3
"""
JVO — enrich_metascore.py
Récupère le Metascore depuis RAWG et met à jour Firestore directement.

Prérequis :
  - rawg_key.txt      (clé RAWG)
  - firebase_key.json (clé service Firebase)
  - pip install firebase-admin

Usage :
    python enrich_metascore.py            # tous les jeux sans metascore
    python enrich_metascore.py --force    # écrase les existants
    python enrich_metascore.py --dry      # simulation
"""
import json, sys, time, urllib.request, urllib.parse
from pathlib import Path

HERE = Path(__file__).parent

def load_rawg_key():
    f = HERE / "rawg_key.txt"
    if not f.exists(): sys.exit("⛔ rawg_key.txt introuvable")
    return f.read_text().strip()

def rawg_search(name, console, key):
    platform_map = {"PS5":"187","PS4":"18","Switch":"7","XBOX Series":"186","XBOX One":"1"}
    plat = platform_map.get(console, "")
    params = {"search": name, "page_size": 3, "key": key}
    if plat: params["platforms"] = plat
    url = "https://api.rawg.io/api/games?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if not results:
            # retry sans plateforme
            params.pop("platforms", None)
            url2 = "https://api.rawg.io/api/games?" + urllib.parse.urlencode(params)
            with urllib.request.urlopen(url2, timeout=8) as r:
                data = json.loads(r.read())
            results = data.get("results", [])
        return results[0] if results else None
    except Exception as e:
        print(f"  ⚠ {e}"); return None

def main():
    args  = sys.argv[1:]
    force = "--force" in args
    dry   = "--dry"   in args

    key = load_rawg_key()

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        sys.exit("⛔ pip install firebase-admin")

    key_file = HERE / "firebase_key.json"
    if not key_file.exists(): sys.exit("⛔ firebase_key.json introuvable")

    cred = credentials.Certificate(str(key_file))
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    print("Chargement depuis Firestore…")
    docs = list(db.collection("games").stream())
    print(f"✓ {len(docs)} jeux\n")

    batch = db.batch()
    count, updated = 0, 0

    for d in docs:
        g = d.to_dict()
        if not force and g.get("metascore"):
            continue
        count += 1
        name = g.get("name","")
        console = g.get("console","")
        print(f"  {name} ({console})…", end=" ", flush=True)

        r = rawg_search(name, console, key)
        time.sleep(0.4)

        if not r:
            print("✗ non trouvé"); continue

        score = r.get("metacritic")
        if not score:
            print("— pas de score"); continue

        print(f"✓ {score}")
        updated += 1
        if not dry:
            batch.update(d.reference, {"metascore": score})
            if updated % 400 == 0:
                batch.commit(); batch = db.batch()

    if not dry and updated:
        batch.commit()

    print(f"\n{'[DRY] ' if dry else ''}Traité: {count} — mis à jour: {updated}")
    if updated and not dry:
        print("✓ Firestore mis à jour — rechargez le site.")

if __name__ == "__main__":
    main()
