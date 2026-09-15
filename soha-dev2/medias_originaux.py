#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — remettre les originaux dans le kit médias.

Le problème
-----------
Le kit médias v04 a été exporté REDIMENSIONNÉ : les treize photos du Journal y
plafonnent à 800 px, et trois descendent à 300. Les originaux vivent sur
WordPress, sous `wpsoha/wp-content/uploads/<année>/<mois>/` — mais l'export les
a RENOMMÉS : `caroline-veronez-…unsplash.jpg` est devenu
`soha-journal-079.webp`. Aucun nom ne permet de les rapprocher.

La méthode
----------
On n'apparie pas par le nom : on apparie par l'IMAGE. Empreinte perceptuelle
dHash 16×16 sur la luminance, distance de Hamming. Une réduction change les
pixels mais pas la structure des gradients : l'empreinte survit au
redimensionnement et à la conversion WebP. Mesuré sur le premier cas trouvé :
écart de 2 sur 256 bits entre un original 1024 px et sa réduction 800 px.

Le seuil est à 24 — large, parce qu'une photo qui ressemble à une autre du
même lot existe, et qu'un faux appariement remplacerait une photo par une
autre sans que rien ne le signale. Au-dessus de 24, le script REFUSE et le
dit ; il ne choisit pas à ta place.

    python3 medias_originaux.py --kit-medias <dossier> --originaux <dossier> [--lire]
"""

import argparse
import glob
import os
import sys

SEUIL = 24          # sur 256 bits
MINI = 400          # une vignette ne peut pas être l'original de quoi que ce soit

# LE PLAFOND. Un original de 5 472 px pèse 2 Mo en WebP — pour une photo que
# le site affiche au plus à 1 160 px de large. Le générateur borne l'affichage
# à la MOITIÉ de la largeur native (la taille à laquelle l'image est nette sur
# un écran 2×), donc tout ce qui dépasse 2 × 1 160 est du poids que personne ne
# voit. On garde 2 400 px : de quoi couvrir la plus grande fente possible, et
# pas un pixel de plus.
PLAFOND = 2400


def empreinte(chemin, n=16):
    from PIL import Image
    im = Image.open(chemin).convert("L").resize((n + 1, n), Image.LANCZOS)
    px = list(im.getdata())
    bits = 0
    for y in range(n):
        for x in range(n):
            bits = (bits << 1) | (1 if px[y * (n + 1) + x] > px[y * (n + 1) + x + 1] else 0)
    return bits


def ecart(a, b):
    return bin(a ^ b).count("1")


def candidats(dossier):
    from PIL import Image
    out = {}
    for f in glob.glob(os.path.join(dossier, "**", "*"), recursive=True):
        if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        if not os.path.isfile(f):
            continue
        try:
            l, h = Image.open(f).size
        except Exception:
            continue
        if l < MINI:
            continue
        out[f] = (empreinte(f), l, h)
    return out


def appliquer(kit_medias, originaux, ecrire=True):
    from PIL import Image
    journal = []
    cibles = sorted(glob.glob(os.path.join(kit_medias, "**", "soha-journal-*.webp"),
                              recursive=True))
    if not cibles:
        raise SystemExit("aucune photo de Journal dans %s" % kit_medias)
    cand = candidats(originaux)
    journal.append("originaux : %d fichier(s) de %d px ou plus à examiner" % (len(cand), MINI))

    remplaces, doutes, absents = 0, [], []
    for c in cibles:
        e, l, h = empreinte(c), *Image.open(c).size
        classement = sorted((ecart(e, x[0]), f, x[1], x[2]) for f, x in cand.items())
        if not classement:
            absents.append(os.path.basename(c)); continue
        d, f, lo, ho = classement[0]
        if d > SEUIL:
            absents.append(os.path.basename(c)); continue
        # Parmi toutes les tailles du MÊME original, on prend la plus grande.
        souche = os.path.basename(f)
        import re
        souche = re.sub(r"-\d+x\d+(\.\w+)$", r"\1", souche)
        familles = [(x[1], g) for g, x in cand.items()
                    if re.sub(r"-\d+x\d+(\.\w+)$", r"\1", os.path.basename(g)) == souche]
        lo, f = max(familles)
        if lo <= l:
            journal.append("  %-24s original %d px — pas plus grand que les %d px du kit"
                           % (os.path.basename(c), lo, l))
            continue
        if d > SEUIL // 2:
            doutes.append((os.path.basename(c), os.path.basename(f), d))
        if ecrire:
            im = Image.open(f).convert("RGB")
            if im.width > PLAFOND:
                im = im.resize((PLAFOND, round(im.height * PLAFOND / im.width)),
                               Image.LANCZOS)
            im.save(c, "WEBP", quality=88, method=6)
        lo = min(lo, PLAFOND)
        remplaces += 1
        journal.append("  %-24s %4d px → %4d px   (%s, écart %d)%s"
                       % (os.path.basename(c), l, lo, os.path.basename(f)[:34], d,
                          "  — plafonné" if lo == PLAFOND else ""))

    journal.append("originaux : %d photo(s) remplacée(s), %d sans correspondance"
                   % (remplaces, len(absents)))
    if absents:
        journal.append("  sans correspondance : " + ", ".join(absents))
    for n, f, d in doutes:
        journal.append("  À VÉRIFIER À L'ŒIL — %s ↔ %s, écart %d (au-dessus de la moitié du seuil)"
                       % (n, f, d))
    return journal


def main():
    ap = argparse.ArgumentParser(description="Remettre les originaux dans le kit médias.")
    ap.add_argument("--kit-medias", required=True)
    ap.add_argument("--originaux", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    for l in appliquer(a.kit_medias, a.originaux, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
