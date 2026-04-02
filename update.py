#!/usr/bin/env python3
"""
JVO — update.py
---------------
Lit games.json et l'intègre dans index_template.html pour produire index.html.

Usage :
    python update.py

Placez ce script dans le même dossier que games.json et index_template.html.
"""

import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent

GAMES_FILE    = HERE / "games.json"
TEMPLATE_FILE = HERE / "index_template.html"
OUTPUT_FILE   = HERE / "index.html"

MARKER = "/*__GAMES_DATA__*/"


def normalize(s: str) -> str:
    """Génère une chaîne de recherche normalisée depuis un nom de jeu."""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


def load_games() -> list[dict]:
    if not GAMES_FILE.exists():
        sys.exit(f"✗  Fichier introuvable : {GAMES_FILE}")
    with open(GAMES_FILE, encoding="utf-8") as f:
        games = json.load(f)

    # Garantit que chaque jeu a un champ 'search' valide
    for g in games:
        if not g.get("search"):
            g["search"] = normalize(g.get("name", ""))

    return games


def build_html(games: list[dict]) -> str:
    if not TEMPLATE_FILE.exists():
        sys.exit(f"✗  Template introuvable : {TEMPLATE_FILE}")
    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    if MARKER not in template:
        sys.exit(f"✗  Marqueur '{MARKER}' absent de {TEMPLATE_FILE}")

    games_js = json.dumps(games, ensure_ascii=False, separators=(",", ":"))
    return template.replace(MARKER, games_js)


def main():
    print("JVO — Mise à jour du site")
    print("-" * 32)

    games = load_games()
    print(f"✓  {len(games)} jeux chargés depuis games.json")

    # Quelques stats rapides
    consoles: dict[str, int] = {}
    for g in games:
        c = g.get("console", "?")
        consoles[c] = consoles.get(c, 0) + 1
    for console, count in sorted(consoles.items()):
        print(f"     {console:<8} {count} jeux")

    html = build_html(games)
    OUTPUT_FILE.write_text(html, encoding="utf-8")

    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"✓  {OUTPUT_FILE.name} généré ({size_kb:.0f} Ko)")
    print("\nOuvrez index.html dans votre navigateur.")


if __name__ == "__main__":
    main()
