#!/usr/bin/env python3
"""
JVO — convert_webp.py
Convertit toutes les jaquettes PNG → WebP dans le dossier covers/.
Garde les PNG originaux (renommer à la main si tout est OK).

Prérequis : pip install Pillow

Usage : python convert_webp.py
"""
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable,'-m','pip','install','Pillow','-q'])
    from PIL import Image

COVERS = Path(__file__).parent / "covers"
pngs   = list(COVERS.glob("*.png"))
print(f"{len(pngs)} PNG trouvés dans {COVERS}\n")

saved_kb = 0
for p in sorted(pngs):
    out = p.with_suffix(".webp")
    if out.exists():
        continue
    try:
        img = Image.open(p)
        img.save(out, "WEBP", quality=85, method=6)
        ratio = (1 - out.stat().st_size / p.stat().st_size) * 100
        saved_kb += (p.stat().st_size - out.stat().st_size) / 1024
        print(f"  ✓ {p.name} → {out.name}  ({ratio:.0f}% plus léger)")
    except Exception as e:
        print(f"  ✗ {p.name}: {e}")

print(f"\n✓ Terminé — économie totale : {saved_kb:.0f} Ko")
print("Les PNG sont conservés. Supprimez-les manuellement si tout est OK.")
print("⚠ Pour utiliser les WebP, mettez à jour les références .png → .webp dans index.html et admin.")
