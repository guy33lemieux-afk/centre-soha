#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la politique dit enfin où dorment les renseignements.

La section 4 annonçait « l'hébergeur du site » sans dire où. La Loi 25 demande
que la personne sache si ses renseignements quittent le Québec, et l'hébergeur a
répondu : Toronto (installation principale au Canada), Los Angeles, Amsterdam.

Le texte écrit donc **Toronto, en Ontario** — c'est l'installation canadienne
principale, et c'est celle qui dessert un compte québécois. Il nomme aussi les
deux autres, parce qu'une politique qui tait l'existence de sites à l'étranger
laisse une question ouverte, et parce que c'est vérifiable.

À confirmer par Mala en une phrase à l'hébergeur : « Dans lequel de vos trois
centres mon compte est-il hébergé ? » Si la réponse n'est pas Toronto, ce texte
change — et c'est pour ça qu'il vit dans un script plutôt que dans une retouche
faite à la main.

Ce qui n'est PAS touché : la ligne sur l'infolettre. Elle dit aujourd'hui que
l'envoi se fait depuis notre propre serveur, et c'est vrai tant que rien n'est
branché ailleurs. Le jour où Mailchimp est choisi, c'est l'écran « Infolettre »
de l'extension CRM qui fournit le paragraphe de remplacement.

Usage :
    python3 kit_hebergement.py --kit <dossier du kit>
"""

import argparse
import json
import os
import sys

PAGE = "7386"        # Politique de confidentialité

AVANT = ("<li><strong>L'hébergeur du site</strong> — il conserve les fichiers du site "
         "et la base de données, dont la liste d'infolettre.</li>")

APRES = ("<li><strong>L'hébergeur du site</strong> — il conserve les fichiers du site "
         "et la base de données, dont la liste d'infolettre. Ses serveurs se trouvent "
         "à <strong>Toronto, en Ontario</strong>, son installation principale au Canada. "
         "Vos renseignements demeurent donc au Canada, mais hors du Québec. "
         "L'hébergeur exploite aussi des centres à Los Angeles (États-Unis) et à "
         "Amsterdam (Pays-Bas), que le site n'utilise pas.</li>")


def remplacer(noeud, avant, apres):
    n = 0
    for e in (noeud if isinstance(noeud, list) else noeud.get("elements", [])):
        for cle, valeur in (e.get("settings") or {}).items():
            if isinstance(valeur, str) and avant in valeur:
                e["settings"][cle] = valeur.replace(avant, apres)
                n += 1
        n += remplacer(e, avant, apres)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kit", required=True, help="dossier du kit Elementor")
    a = ap.parse_args()

    chemin = os.path.join(a.kit, "content", "page", PAGE + ".json")
    if not os.path.isfile(chemin):
        raise SystemExit("Page introuvable : %s" % chemin)

    page = json.load(open(chemin, encoding="utf-8"))
    n = remplacer(page.get("content", page), AVANT, APRES)
    if n != 1:
        raise SystemExit("La phrase de l'hébergeur : %d occurrence(s) au lieu d'une." % n)

    json.dump(page, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("   la politique nomme maintenant Toronto, et dit « hors du Québec »")

    texte = open(chemin, encoding="utf-8").read()
    if "Toronto" not in texte or "hors du Qu" not in texte:
        raise SystemExit("La relecture ne retrouve pas le texte écrit.")
    print("   relu dans le fichier")
    return 0


if __name__ == "__main__":
    sys.exit(main())
