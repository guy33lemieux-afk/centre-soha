#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — donner un rythme vertical au kit.

Le constat
----------
Quarante et un conteneurs de section portaient exactement `80 / 80`. Écart-type
zéro sur l'accueil. Rien n'indiquait à l'œil qu'un passage ouvrait un mouvement
et que le suivant le poursuivait : la page avançait au même pas du début à la
fin. C'est la première cause du « pas équilibré ».

La règle
--------
Le rythme n'est pas décoratif : il dit ce que fait la section. On la lit donc
dans le kit plutôt que de la décider par sa position.

  ouvre un mouvement   la section porte une étiquette (le petit intertitre en
                       capitales, `h6`) — ou c'est la première après le héros
                       → 120 px au-dessus, 48 px en dessous
  poursuit             pas d'étiquette : elle appartient à ce qui précède
                       →  48 px au-dessus, 48 px en dessous
  dernière de la page  → 96 px en dessous, pour ne pas coller au pied

Le signal n'est pas inventé : l'étiquette EST la marque qu'une section ouvre
quelque chose — c'est à ça qu'elle sert. J'avais d'abord essayé « la section
porte un titre h2 » ; trente-deux sections sur quarante et une en portent un.
Un critère que presque tout le monde satisfait ne classe rien.

Deux mouvements sont donc séparés de 168 px, deux blocs d'une même idée de
96 px. Là où une page ne porte aucune étiquette, seule la première section
ouvre : les autres restent à égalité, et c'est honnête — cette page-là demande
une décision de contenu, pas un calcul.

Les héros (image de fond, `110 / 110`) ne sont pas touchés.

    python3 kit_rythme.py --kit <dossier> [--lire]
"""

import argparse
import glob
import json
import os
import sys

# v02 (15 septembre, département rythme) : GRAND passe de 120 à 144. Les
# intervalles sont la somme de deux paddings ; avec 120/48 on obtenait 168 et
# 216, hors de toute échelle. Avec 144/48/96, chaque intervalle du site vaut
# 96, 144 ou 192 — trois valeurs, toutes dans l'échelle 48·n.
GRAND, COURT, FIN = 144, 48, 96


def pages(kit):
    return sorted(glob.glob(os.path.join(kit, "content/page/*.json")))


def porte_une_etiquette(o):
    """La section porte-t-elle une étiquette — le petit intertitre `h6` ?"""
    if isinstance(o, dict):
        if o.get("widgetType") == "heading":
            if (o.get("settings") or {}).get("header_size") == "h6":
                return True
        return any(porte_une_etiquette(v) for v in o.values())
    if isinstance(o, list):
        return any(porte_une_etiquette(v) for v in o)
    return False


def est_un_hero(c):
    s = c.get("settings") or {}
    return bool(isinstance(s.get("background_image"), dict) and s["background_image"].get("url"))


def boite(p, haut, bas):
    return {"unit": p.get("unit", "px"), "top": str(haut), "right": p.get("right", "22"),
            "bottom": str(bas), "left": p.get("left", "22"), "isLinked": False}


def rythmer(kit, ecrire=True):
    journal = []
    for chemin in pages(kit):
        doc = json.load(open(chemin, encoding="utf-8"))
        racines = doc if isinstance(doc, list) else doc.get("content", [])
        sections = [c for c in racines if isinstance(c, dict) and c.get("elType") == "container"]
        candidats = [c for c in sections if not est_un_hero(c)]
        change = False

        for i, c in enumerate(candidats):
            s = c.setdefault("settings", {})
            p = s.get("padding")
            if not isinstance(p, dict) or str(p.get("top")) not in ("80", "120", "76", "90", "96"):
                continue                       # le 80/80 d'origine, le 120/48 de v01, et les 76/90/96 uniformes
            ouvre = porte_une_etiquette(c) or i == 0
            haut = GRAND if ouvre else COURT
            bas = FIN if i == len(candidats) - 1 else COURT
            s["padding"] = boite(p, haut, bas)
            journal.append((os.path.basename(chemin), c.get("id"),
                            "ouvre" if ouvre else "poursuit", haut, bas))
            change = True

        if change and ecrire:
            json.dump(doc, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
    return journal


def main():
    ap = argparse.ArgumentParser(description="Le rythme vertical du kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true", help="montrer sans écrire")
    a = ap.parse_args()
    j = rythmer(a.kit, ecrire=not a.lire)
    for f, eid, quoi, h, b in j:
        print("   %-12s %-10s %-9s %3d / %-3d" % (f, eid, quoi, h, b))
    ouvre = sum(1 for x in j if x[2] == "ouvre")
    print("%d section(s)%s · %d ouvrent un mouvement, %d poursuivent"
          % (len(j), "" if a.lire else " réglée(s)", ouvre, len(j) - ouvre))
    return 0


if __name__ == "__main__":
    sys.exit(main())
