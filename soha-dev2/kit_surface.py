#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — retirer du kit un littéral qui n'est dans aucune ligne du canon.

Le fait
-------
`#EFE7DA` apparaît **27 fois** dans le kit, dans 7 fichiers, toujours en
majuscules — plus une 28ᵉ trace sous la forme `rgba(239,231,218,.82)`. Il
n'est déclaré nulle part dans `site-settings.json` : ce n'est pas une
décision, c'est un copier-coller qui a fait des petits.

Il mesure L*=91,94 contre 94,88 pour l'ivoire — ΔL* 2,94. Un écart encore
plus invisible que le 2,80 déjà payé entre le papier et l'ivoire. Il ne crée
aucune épaisseur : il dilue.

Et c'est **lui** le plancher de contraste du site. `#5A6460` sur `#EFE7DA`
donne 4,99 — exactement le pire cas relevé par la porte du contraste.

Ce que le script fait
---------------------
26 emplois sont des LETTRES claires posées sur l'encre (25 champs de couleur
Elementor + un attribut `style` en ligne) : ils passent à l'ivoire du canon,
et leur contraste monte de 14,54 à 15,68.

1 emploi est un FOND de section — « La semaine au 961 », `5fe511bc`. Celui-là
ne va pas à l'ivoire : il irait alors iso-sol avec ses voisines, ΔL* 0,00, et
la rupture de surface disparaîtrait entièrement. On paierait le geste pour
perdre une bande. Il va au **papier `#FBF8F3`** : la rupture survit à
ΔL* 2,80, c'est du canon, et c'est déjà un sol de section sur cette page même.

Ce que le script n'est PAS
--------------------------
Ce n'est pas « éteindre le quatrième blanc ». Le kit porte encore `#DDF0F5`,
`#EDE9E1`, `#F3EEE5`, et `site-settings.json` déclare en amont `s_sable`,
`s_blanc`, `s_cyanpale`. C'est le PREMIER geste d'assainissement, pas le
dernier. Son titre honnête est « hygiène de littéral ».

`sed -i 's/EFE7DA/F4F0E7/g'` ne suffirait pas : il enverrait le fond à
l'ivoire et raterait la forme `rgba`.

    python3 kit_surface.py --kit <dossier> [--lire]
"""

import argparse
import glob
import json
import os
import sys

INTRUS = "#EFE7DA"
INTRUS_RGBA = "239,231,218"
IVOIRE = "#F4F0E7"
IVOIRE_RGBA = "244,240,231"
PAPIER = "#FBF8F3"

FOND = "5fe511bc"          # « La semaine au 961 », content/page/7326.json
PAGE_DU_FOND = "content/page/7326.json"


def remplacer_les_lettres(kit, journal, ecrire=True):
    """Les 26 emplois qui sont des lettres claires sur l'encre."""
    total = 0
    for chemin in sorted(glob.glob(os.path.join(kit, "content", "*", "*.json"))
                         + glob.glob(os.path.join(kit, "templates", "*.json"))):
        t = open(chemin, encoding="utf-8").read()
        if INTRUS not in t and INTRUS_RGBA not in t:
            continue
        n = t.count(INTRUS) + t.count(INTRUS_RGBA)
        t = t.replace(INTRUS, IVOIRE).replace(INTRUS_RGBA, IVOIRE_RGBA)
        if ecrire:
            open(chemin, "w", encoding="utf-8").write(t)
        total += n
        journal.append("surface : %s — %d emploi(s)" % (os.path.basename(chemin), n))
    journal.append("surface : %d emploi(s) au total" % total)
    return total


def corriger_le_fond(kit, journal, ecrire=True):
    """Le seul emploi qui est un FOND, et qui ne va pas au même endroit."""
    chemin = os.path.join(kit, PAGE_DU_FOND)
    d = json.load(open(chemin, encoding="utf-8"))
    vus = [0]

    def marche(o):
        if isinstance(o, dict):
            if o.get("id") == FOND:
                o.setdefault("settings", {})["background_color"] = PAPIER
                vus[0] += 1
            for v in o.values():
                marche(v)
        elif isinstance(o, list):
            for v in o:
                marche(v)

    marche(d)
    if vus[0] != 1:
        raise SystemExit("surface : %s introuvable ou en double (%d)" % (FOND, vus[0]))
    if ecrire:
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    journal.append("surface : le fond « La semaine au 961 » → %s (et non l'ivoire)" % PAPIER)


def appliquer(kit, ecrire=True):
    journal = []
    if remplacer_les_lettres(kit, journal, ecrire):
        corriger_le_fond(kit, journal, ecrire)
    else:
        journal.append("surface : aucun littéral #EFE7DA — rien à reprendre")
    return journal


def main():
    ap = argparse.ArgumentParser(description="Retirer #EFE7DA du kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true", help="montrer sans écrire")
    a = ap.parse_args()
    for ligne in appliquer(a.kit, ecrire=not a.lire):
        print("   " + ligne)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
