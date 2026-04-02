#!/usr/bin/env python3
"""
JVO — enrich.py
Complète games.json via RAWG.io (gratuit : https://rawg.io/apiv2)

Clé API dans rawg_key.txt (ignoré par .gitignore) — une seule ligne.

Usage :
    python enrich.py              # champs vides uniquement
    python enrich.py --force      # écrase aussi les existants
    python enrich.py --id 12      # un seul jeu
    python enrich.py --dry        # simulation
"""
import json, time, sys, re, urllib.request, urllib.parse
from pathlib import Path

HERE       = Path(__file__).parent
GAMES_FILE = HERE / "games.json"
KEY_FILE   = HERE / "rawg_key.txt"
DELAY      = 0.5

GENRE_MAP = {
    "action":"action","adventure":"aventure","role-playing-games-rpg":"jeu de rôle",
    "shooter":"jeu de tir","strategy":"stratégie","puzzle":"puzzle","sports":"sport",
    "racing":"course","fighting":"combat","platformer":"plateforme",
    "arcade":"arcade","simulation":"simulation","family":"","indie":"","massively-multiplayer":"",
}
PLATFORM_MAP = {"PS5":"187","PS4":"18","Switch":"7","XBOX":"186,1"}

def load_key():
    if not KEY_FILE.exists():
        print(f"⛔ Créez le fichier '{KEY_FILE.name}' avec votre clé RAWG sur une seule ligne.")
        print("   Clé gratuite : https://rawg.io/apiv2")
        sys.exit(1)
    key = KEY_FILE.read_text().strip()
    if not key:
        print("⛔ rawg_key.txt est vide."); sys.exit(1)
    return key

def api(endpoint, params, key):
    params["key"] = key
    url = "https://api.rawg.io/api/" + endpoint + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠ {e}"); return None

def search(name, console, key):
    d = api("games", {"search": name, "platforms": PLATFORM_MAP.get(console,""), "page_size": 3}, key)
    if not d or not d.get("results"):
        d = api("games", {"search": name, "page_size": 3}, key)
    return d["results"][0] if d and d.get("results") else None

def enrich(g, force, key):
    need = []
    if force or not g.get("desc"):         need.append("desc")
    if force or not g.get("genre"):        need.append("genre")
    if force or not g.get("release_date"): need.append("release_date")
    if not need: return g, False

    print(f"  {g['name']} ({g['console']})…")
    r = search(g["name"], g["console"], key)
    if not r: print("  ✗ non trouvé"); return g, False

    detail = api(f"games/{r['slug']}", {}, key) if r.get("slug") else r
    time.sleep(DELAY)
    u, changed = dict(g), False

    if "desc" in need:
        raw = (detail or r).get("description_raw") or ""
        raw = re.sub(r"<[^>]+>","",raw).strip()[:400]
        if raw: u["desc"] = raw; changed = True; print("  ✓ desc")

    if "genre" in need:
        genres = sorted({GENRE_MAP.get(x["slug"],"") for x in r.get("genres",[]) if GENRE_MAP.get(x["slug"])})
        if genres: u["genre"] = ", ".join(genres); changed = True; print(f"  ✓ genre: {u['genre']}")

    if "release_date" in need:
        rd = r.get("released","")
        if rd: u["release_date"] = rd; changed = True; print(f"  ✓ date: {rd}")

    return u, changed

def main():
    args    = sys.argv[1:]
    force   = "--force" in args
    dry     = "--dry"   in args
    only_id = int(args[args.index("--id")+1]) if "--id" in args else None
    key     = load_key()

    games = json.loads(GAMES_FILE.read_text(encoding="utf-8"))
    n = 0
    for i, g in enumerate(games):
        if only_id and g["id"] != only_id: continue
        updated, ok = enrich(g, force, key)
        if ok: n += 1
        if ok and not dry: games[i] = updated
        time.sleep(DELAY)

    print(f"\n{'[DRY] ' if dry else ''}Modifié : {n} jeux")
    if n and not dry:
        GAMES_FILE.write_text(json.dumps(games, ensure_ascii=False, indent=2), encoding="utf-8")
        print("✓ games.json mis à jour → lancez update.bat")

if __name__ == "__main__":
    main()
