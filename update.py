#!/usr/bin/env python3
"""
JVO — update.py
---------------
Lit games.json et l'intègre dans les templates pour produire :
  - index.html       (site de recherche)
  - admin.html       (interface d'édition)

Usage :
    python update.py
"""

import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent

GAMES_FILE     = HERE / "games.json"
INDEX_TEMPLATE = HERE / "index_template.html"
ADMIN_TEMPLATE = HERE / "admin_template.html"
INDEX_OUTPUT   = HERE / "index.html"
ADMIN_OUTPUT   = HERE / "admin.html"

MARKER = "/*__GAMES_DATA__*/"


def normalize(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def load_games() -> list[dict]:
    if not GAMES_FILE.exists():
        sys.exit(f"✗  Fichier introuvable : {GAMES_FILE}")
    with open(GAMES_FILE, encoding="utf-8") as f:
        games = json.load(f)
    for g in games:
        if not g.get("search"):
            g["search"] = normalize(g.get("name", ""))
    return games


def inject(template_path: Path, games: list[dict], output_path: Path):
    if not template_path.exists():
        print(f"⚠  Template introuvable, ignoré : {template_path.name}")
        return
    template = template_path.read_text(encoding="utf-8")
    if MARKER not in template:
        print(f"⚠  Marqueur absent de {template_path.name}, ignoré")
        return
    games_js = json.dumps(games, ensure_ascii=False, separators=(",", ":"))
    output_path.write_text(template.replace(MARKER, games_js), encoding="utf-8")
    size_kb = output_path.stat().st_size / 1024
    print(f"✓  {output_path.name:<22} ({size_kb:.0f} Ko)")


def main():
    print("JVO — Mise à jour du site")
    print("-" * 36)

    games = load_games()
    print(f"✓  {len(games)} jeux chargés depuis games.json")

    consoles: dict[str, int] = {}
    for g in games:
        c = g.get("console", "?")
        consoles[c] = consoles.get(c, 0) + 1
    for console, count in sorted(consoles.items()):
        print(f"     {console:<8} {count} jeux")

    print()
    inject(INDEX_TEMPLATE, games, INDEX_OUTPUT)
    inject(ADMIN_TEMPLATE, games, ADMIN_OUTPUT)

    print("\nFait. Ouvrez index.html ou admin.html dans le navigateur.")


if __name__ == "__main__":
    main()