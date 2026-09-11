#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — ramener les tailles de texte du kit sur l'échelle du canon.

Le canon fixe une rampe : 12 / 14 / 16 / 19 / 24 / 32 / 48 / 72. Le kit en
respectait l'essentiel — 48 ×57, 32 ×54, 14 ×139 — mais deux valeurs voisines
s'y étaient glissées et avaient pris toute la place : **17 px ×151** pour le
corps de texte, **15 px ×42** pour les mentions. Personne ne les a décidées ;
elles sont arrivées une par une.

Deux tailles séparées de 2 px ne créent pas de hiérarchie, elles créent du
flou : l'œil ne sait pas si l'écart est voulu. C'est une partie de ce qui fait
paraître la structure molle.

On corrige **la source** et non la feuille de style : une règle globale qui
lutterait contre les réglages par élément perdrait à égalité de spécificité,
et l'éditeur Elementor continuerait d'afficher 17.

    python3 kit_rampe.py --kit <dossier> [--lire]
"""

import argparse
import collections
import glob
import json
import os
import sys

RAMPE = (12, 14, 16, 19, 24, 32, 48, 72)

# La table est écrite à la main, et pas calculée par « la valeur la plus proche ».
#
# La règle du plus proche enverrait 17 vers 16 — la mauvaise réponse. Le corps de
# texte à 16 px tiendrait DAVANTAGE de caractères par ligne, et la mesure, déjà
# hors bande quatre fois sur dix, empirerait. 19 px est la taille de lecture du
# canon : elle corrige les deux défauts d'un coup.
#
# Partout ailleurs, le plus proche est le bon choix — et il est écrit ici pour
# qu'on puisse le relire plutôt que de le recalculer.
TABLE = {17: 19, 15: 16, 13: 14, 11: 12, 18: 19, 20: 19,
         26: 24, 38: 32, 51: 48, 56: 48}


def sur_la_rampe(v):
    t = int(round(v))
    if t in TABLE:
        return TABLE[t]
    return min(RAMPE, key=lambda r: (abs(r - t), -r))


def pages(kit):
    return sorted(glob.glob(os.path.join(kit, "content/page/*.json"))) + \
           sorted(glob.glob(os.path.join(kit, "templates/*.json")))


def parcourir(o, faire):
    if isinstance(o, dict):
        s = o.get("settings")
        if isinstance(s, dict):
            for k, v in list(s.items()):
                if k.endswith("font_size") and isinstance(v, dict):
                    faire(s, k, v)
        for v in o.values():
            parcourir(v, faire)
    elif isinstance(o, list):
        for v in o:
            parcourir(v, faire)


def aligner(kit, ecrire=True):
    bilan = collections.Counter()
    for chemin in pages(kit):
        doc = json.load(open(chemin, encoding="utf-8"))
        change = [False]

        def faire(s, cle, val):
            if (val.get("unit") or "px") != "px":
                return
            try:
                t = float(val.get("size"))
            except (TypeError, ValueError):
                return
            if t <= 0 or int(t) in RAMPE:
                return
            neuf = sur_la_rampe(t)
            bilan[(int(t), neuf)] += 1
            if ecrire:
                val["size"] = neuf
                change[0] = True

        parcourir(doc, faire)
        if change[0] and ecrire:
            json.dump(doc, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
    return bilan


def main():
    ap = argparse.ArgumentParser(description="La rampe typographique du kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    b = aligner(a.kit, ecrire=not a.lire)
    for (avant, apres), n in sorted(b.items(), key=lambda x: -x[1]):
        print("   %3d px  →  %3d px   ×%d" % (avant, apres, n))
    print("%d taille(s)%s" % (sum(b.values()), "" if a.lire else " alignée(s)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
