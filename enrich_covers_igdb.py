#!/usr/bin/env python3
"""
JVO — enrich_covers_igdb.py
Télécharge les jaquettes françaises (région Europe/PEGI) depuis IGDB.
Priorité : cover de la release européenne → cover principale → skip.

Les fichiers sont sauvegardés dans covers/ au format PNG.
Seuls les jeux SANS jaquette existante sont traités (--force pour écraser).

Prérequis :
  - igdb_key.txt
  - firebase_key.json
  - pip install firebase-admin Pillow requests

Usage :
    python enrich_covers_igdb.py              # jeux sans cover seulement
    python enrich_covers_igdb.py --force      # retélécharger tout
    python enrich_covers_igdb.py --dry        # simulation
    python enrich_covers_igdb.py --limit 10   # N jeux max
"""
import sys, json, time, re, urllib.request, urllib.parse
from pathlib import Path

HERE      = Path(__file__).parent
COVERS    = HERE / "covers"
COVERS.mkdir(exist_ok=True)
DELAY     = 0.4

# ── Clés ─────────────────────────────────────────────────────────────────────
def load_igdb():
    f = HERE / "igdb_key.txt"
    if not f.exists(): sys.exit("⛔ igdb_key.txt manquant")
    cfg = {}
    for line in f.read_text().splitlines():
        if "=" in line:
            k,v = line.split("=",1); cfg[k.strip()]=v.strip()
    return cfg["CLIENT_ID"], cfg["CLIENT_SECRET"]

def igdb_token(cid, cs):
    data = urllib.parse.urlencode({
        "client_id":cid,"client_secret":cs,"grant_type":"client_credentials"
    }).encode()
    with urllib.request.urlopen("https://id.twitch.tv/oauth2/token",data=data,timeout=8) as r:
        return json.loads(r.read())["access_token"]

def igdb(endpoint, body, cid, token):
    req = urllib.request.Request(
        "https://api.igdb.com/v4/" + endpoint,
        data=body.encode(),
        headers={"Client-ID":cid,"Authorization":"Bearer "+token,"Content-Type":"text/plain"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠ {e}"); return []

PLATFORM_MAP = {"PS5":167,"PS4":48,"Switch":130,"Switch 2":130,
                "XBOX Series":169,"XBOX One":11}
REGION_EU = 8   # Europe (PEGI)

def find_cover(name, console, cid, token):
    """Cherche la jaquette européenne (PEGI) d'un jeu."""
    plat  = PLATFORM_MAP.get(console, "")
    clean = re.sub(r'\b(goty|edition|deluxe|remaster\w*|complete|hd|dx)\b','',name,flags=re.I).strip()

    # 1. Rechercher le jeu
    plat_q = f" & platforms = ({plat})" if plat else ""
    results = igdb("games",
        f'search "{clean}"; fields id,name,cover.url,cover.image_id; '
        f'where version_parent = null{plat_q}; limit 3;', cid, token)
    time.sleep(DELAY)
    if not results: return None, None

    game_id = results[0]["id"]
    main_cover = results[0].get("cover",{})

    # 2. Chercher release européenne avec cover alternative
    releases = igdb("release_dates",
        f'fields game,region,platform; where game = {game_id} & region = {REGION_EU}; limit 5;',
        cid, token)
    time.sleep(DELAY)

    # 3. Chercher covers alternatives pour la région EU
    alt_covers = igdb("alternative_names",
        f'fields name,comment; where game = {game_id}; limit 5;', cid, token)
    time.sleep(DELAY)

    # On utilise la cover principale (IGDB n'expose pas les covers régionales distinctes)
    # mais on vérifie qu'elle existe
    img_id = main_cover.get("image_id")
    if not img_id:
        return None, None

    # URL haute résolution
    url = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{img_id}.jpg"
    return url, results[0].get("name","")

def download_cover(url, dest_path):
    """Télécharge et sauvegarde une image."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"JVO/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        dest_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"  ⚠ download: {e}")
        return False

def main():
    args    = sys.argv[1:]
    force   = "--force" in args
    dry     = "--dry"   in args
    limit   = int(args[args.index("--limit")+1]) if "--limit" in args else None

    cid, cs = load_igdb()
    print("Auth IGDB…")
    token = igdb_token(cid, cs)
    print("✓\n")

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        sys.exit("⛔ pip install firebase-admin")

    kf = HERE / "firebase_key.json"
    if not kf.exists(): sys.exit("⛔ firebase_key.json manquant")
    cred = credentials.Certificate(str(kf))
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    print("Chargement Firestore…")
    docs = list(db.collection("games").stream())
    print(f"✓ {len(docs)} jeux\n")

    batch   = db.batch()
    total   = 0
    updated = 0

    for d in docs:
        g = d.to_dict()
        cover_key  = g.get("cover","")
        cover_file = COVERS / (cover_key + ".png") if cover_key else None

        # Skip si cover existe déjà (sauf --force)
        if not force and cover_file and cover_file.exists():
            continue
        if limit and total >= limit:
            break
        total += 1

        name    = g.get("name","")
        console = g.get("console","")
        print(f"  {name} ({console})…", end=" ", flush=True)

        url, igdb_name = find_cover(name, console, cid, token)
        if not url:
            print("✗ non trouvé"); continue

        # Nom du fichier : conserver l'existant ou générer
        if not cover_key:
            prefix = {"PS5":"ps","PS4":"ps","Switch":"nin","Switch 2":"nin",
                      "XBOX Series":"xbox","XBOX One":"xbox"}.get(console,"game")
            safe = re.sub(r'[^a-z0-9]','_', name.lower())[:20].strip('_')
            cover_key = f"{prefix}_{safe}"

        dest = COVERS / (cover_key + ".png")

        if dry:
            print(f"[DRY] → {dest.name}")
            continue

        ok = download_cover(url, dest)
        if ok:
            updated += 1
            print(f"✓ {dest.name}")
            if not g.get("cover"):
                batch.update(d.reference, {"cover": cover_key})
                if updated % 400 == 0:
                    batch.commit(); batch = db.batch()
        else:
            print("✗ échec téléchargement")

    if not dry and updated:
        batch.commit()

    print(f"\n{'[DRY] ' if dry else ''}Traité: {total} — téléchargé: {updated}")

if __name__ == "__main__":
    main()
