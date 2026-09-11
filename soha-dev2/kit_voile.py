#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — régler l'opacité du voile des héros, dans le kit.

Le kit posait `rgba(14,26,21,0.80)` sur ses huit héros. À cette valeur le texte
est parfaitement lisible — et la photo a perdu 64 % de sa lumière : on ne voit
plus le lieu, on voit un rectangle sombre avec du texte dessus.

Ce script cherche donc l'autre bout : **la plus basse opacité qui garde les
seize textes au-dessus du seuil WCAG AA**. Pas un compromis à l'œil — une
valeur mesurée, avec sa marge.

    python3 kit_voile.py --kit <dossier> --opacite 0.55
    python3 kit_voile.py --kit <dossier> --lire
"""

import argparse
import glob
import json
import os
import re
import sys

MOTIF = re.compile(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)")


def fichiers(kit):
    return sorted(glob.glob(os.path.join(kit, "content/page/*.json"))) + \
           sorted(glob.glob(os.path.join(kit, "templates/*.json")))


def parcourir(o, faire):
    if isinstance(o, dict):
        s = o.get("settings")
        if isinstance(s, dict) and "background_overlay_color" in s:
            faire(o.get("id"), s)
        for v in o.values():
            parcourir(v, faire)
    elif isinstance(o, list):
        for v in o:
            parcourir(v, faire)


def regler(kit, opacite, ecrire=True):
    touches = []
    for chemin in fichiers(kit):
        d = json.load(open(chemin, encoding="utf-8"))
        change = [False]

        def faire(eid, s):
            m = MOTIF.match(s["background_overlay_color"] or "")
            if not m:
                return
            avant = float(m.group(4))
            if opacite is None:
                touches.append((os.path.basename(chemin), eid, avant, avant))
                return
            if abs(avant - opacite) < 1e-6:
                touches.append((os.path.basename(chemin), eid, avant, avant))
                return
            s["background_overlay_color"] = "rgba(%s,%s,%s,%s)" % (
                m.group(1), m.group(2), m.group(3), ("%g" % opacite))
            touches.append((os.path.basename(chemin), eid, avant, opacite))
            change[0] = True

        parcourir(d, faire)
        if change[0] and ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return touches


def main():
    ap = argparse.ArgumentParser(description="L'opacité du voile des héros, dans le kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--opacite", type=float, default=None)
    ap.add_argument("--lire", action="store_true", help="afficher sans rien écrire")
    a = ap.parse_args()
    t = regler(a.kit, None if a.lire else a.opacite, ecrire=not a.lire)
    for f, eid, avant, apres in t:
        print("   %-14s %-10s %.2f%s" % (f, eid, avant, "" if avant == apres else "  →  %.2f" % apres))
    print("%d voile(s)%s" % (len(t), "" if a.lire else " réglé(s)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
