#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — l'icône du site.

Le constat
----------
Zéro page sur 30 porte `rel="icon"`, `apple-touch-icon`, `manifest` ou
`theme-color`. Et l'icône de site est une option WordPress, pas un réglage
Elementor : elle ne voyage dans AUCUN kit. Personne ne l'a donc jamais posée,
et rien ne le signalait.

Le geste
--------
RECADRAGE, PAS REDESSIN. L'anneau O du logo hébergé — avec son point, le
visarga — est découpé du fichier livré `soha_logo-site_20260828.webp`. Sa
boîte cyan a été mesurée, pas estimée : x 79→153, y 24→119, soit 75×96 px.
On centre ce rectangle dans un carré, on ajoute une marge, et on exporte.
Aucune forme n'est redessinée, aucune couleur n'est choisie.

Le fond : ivoire #F4F0E7 plutôt que transparent. Un PNG transparent devient
noir sur noir dans la moitié des barres d'onglets, et l'anneau cyan mesure
2,43 sur l'ivoire — ce qui est sans objet ici : WCAG 1.4.11 ne s'applique pas
à un logo (exception « composants de marque »). L'ivoire est simplement le
fond sur lequel ce logo vit déjà partout ailleurs.

`theme-color` : encre #0E1A15, la couleur du pied et du « lieu ».

Ce que le script NE PEUT PAS faire
----------------------------------
Poser l'icône dans WordPress. Elle n'est pas dans le kit et ne peut pas y
être. Le script écrit donc l'étape dans la procédure d'import, nommément :
« Apparence → Personnaliser → Identité du site → Icône du site ».

    python3 kit_favicon.py --kit <dossier> --medias <dossier> [--lire]
"""

import argparse
import json
import os
import sys

BOITE = (79, 24, 154, 120)        # la boîte cyan, mesurée sur le fichier livré
# La marge se resserre quand l'icône rapetisse. À 32 px, 16 % de marge
# laissent un anneau de six pixels de large : illisible dans un onglet. Les
# icônes petites se cadrent serré, les grandes respirent, la maskable doit
# survivre au rognage de 20 % d'Android sur chaque bord.
MARGES = {32: 0.04, 180: 0.10, 192: 0.10, 512: 0.10}
MARGE_MASKABLE = 0.42
IVOIRE = (244, 240, 231, 255)
ENCRE = "#0E1A15"
SOURCE = "soha_logo-site_20260828.webp"
TAILLES = (32, 180, 192, 512)


def decouper(medias, sortie, journal, ecrire=True):
    from PIL import Image
    chemin = os.path.join(medias, SOURCE)
    if not os.path.exists(chemin):
        raise SystemExit("favicon : %s introuvable dans %s" % (SOURCE, medias))
    im = Image.open(chemin).convert("RGBA")
    anneau = im.crop(BOITE)
    l, h = anneau.size
    if ecrire:
        os.makedirs(sortie, exist_ok=True)
    for t in TAILLES:
        cote = int(max(l, h) * (1 + 2 * MARGES[t]))
        carre = Image.new("RGBA", (cote, cote), IVOIRE)
        carre.paste(anneau, ((cote - l) // 2, (cote - h) // 2), anneau)
        if ecrire:
            carre.resize((t, t), Image.LANCZOS).save(
                os.path.join(sortie, "icone-%d.png" % t))
    # La maskable : Android rogne jusqu'à 20 % de chaque bord. L'anneau doit
    # tenir dans le cercle sûr, donc la marge double.
    cote_m = int(max(l, h) * (1 + 2 * MARGE_MASKABLE))
    masque = Image.new("RGBA", (cote_m, cote_m), IVOIRE)
    masque.paste(anneau, ((cote_m - l) // 2, (cote_m - h) // 2), anneau)
    if ecrire:
        masque.resize((512, 512), Image.LANCZOS).save(
            os.path.join(sortie, "icone-maskable-512.png"))
    journal.append("favicon : anneau %d×%d découpé → %s + maskable"
                   % (l, h, ", ".join("%d px" % t for t in TAILLES)))


def manifeste(sortie, journal, ecrire=True):
    m = {
        "name": "Centre Soha", "short_name": "Soha",
        "start_url": "/dev/", "display": "standalone",
        "background_color": "#FBF8F3", "theme_color": ENCRE,
        "icons": [
            {"src": "icone-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icone-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icone-maskable-512.png", "sizes": "512x512",
             "type": "image/png", "purpose": "maskable"},
        ],
    }
    if ecrire:
        json.dump(m, open(os.path.join(sortie, "site.webmanifest"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)
    journal.append("favicon : site.webmanifest écrit")


PROCEDURE = """\
# L'icône du site — l'étape que le kit ne peut pas faire

L'icône de site est une option WORDPRESS, pas un réglage Elementor. Elle ne
voyage donc dans aucun kit, et aucun import ne la posera. C'est pour ça
qu'elle manquait : personne ne l'a oubliée, elle n'avait simplement aucun
chemin pour arriver.

À faire UNE FOIS, après l'import du kit :

1. Téléverser `assets/icones/icone-512.png` dans la médiathèque.
2. Apparence → Personnaliser → Identité du site → Icône du site → choisir
   l'image téléversée → Publier.

Ça suffit pour l'onglet du navigateur et pour l'écran d'accueil des
téléphones : WordPress dérive lui-même les tailles dont il a besoin.

Les fichiers de `assets/icones/` servent au site de référence HTML et à
quiconque voudrait les poser à la main dans un thème enfant.

Toutes les icônes sont un RECADRAGE du logo hébergé
`soha_logo-site_20260828.webp` — l'anneau O et son point. Aucune forme n'a
été redessinée. Si le logo change, relancer `kit_favicon.py`.
"""


def appliquer(kit, medias, ecrire=True):
    journal = []
    sortie = os.path.join(kit, "assets", "icones")
    decouper(medias, sortie, journal, ecrire)
    manifeste(sortie, journal, ecrire)
    if ecrire:
        open(os.path.join(sortie, "LISEZ-MOI.md"), "w",
             encoding="utf-8").write(PROCEDURE)
    journal.append("favicon : la procédure d'import écrite (l'étape WordPress)")
    return journal


def main():
    ap = argparse.ArgumentParser(description="L'icône du site, recadrée du logo.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--medias", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    for l in appliquer(a.kit, a.medias, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
