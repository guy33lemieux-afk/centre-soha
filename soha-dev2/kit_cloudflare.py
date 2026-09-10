#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la politique nomme l'intermédiaire qui sert le site.

Constat du 10 septembre 2026, capture de l'onglet Réseau à l'appui :
`rocket-loader.min.js` est servi sur chaque page. Rocket Loader est une fonction
de Cloudflare, et Cloudflare ne peut l'injecter que s'il voit passer le HTML —
c'est-à-dire si le domaine est **en mode proxy**, pas seulement en DNS.

Ce qui en découle : chaque visite passe par le réseau de Cloudflare avant
d'atteindre le serveur de Toronto. L'adresse IP du visiteur, l'adresse de la
page demandée et l'agent de son navigateur transitent donc par un tiers
américain. La Loi 25 demande que ce soit annoncé.

Ce que ça ne veut PAS dire, et le texte le précise : Cloudflare ne reçoit pas
les formulaires en clair pour les garder — il les relaie. Les renseignements
sont conservés à Toronto. Un intermédiaire de transport n'est pas un
destinataire, mais il n'est pas rien non plus.

À vérifier par Mala en dix secondes : tableau de bord Cloudflare, onglet DNS.
Nuage **orange** = proxy, ce texte s'applique. Nuage **gris** = DNS seulement,
rien ne transite, et ce texte doit être retiré.

Usage :
    python3 kit_cloudflare.py --kit <dossier du kit>
"""

import argparse
import json
import os
import sys

PAGE = "7386"        # Politique de confidentialité

ANCRE = ("<li><strong>La messagerie du site</strong>")

AJOUT = (
    "<li><strong>Cloudflare</strong> — sert le site et le protège des attaques. "
    "Chaque visite transite par son réseau avant d'atteindre notre hébergeur : "
    "votre adresse IP, la page demandée et le type de votre navigateur y passent. "
    "Cloudflare est une entreprise américaine, dont le réseau est mondial. "
    "Il achemine, il ne conserve pas nos dossiers : vos renseignements restent "
    "sur le serveur de notre hébergeur, à Toronto.</li>"
)


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
    ap.add_argument("--kit", required=True)
    ap.add_argument("--retirer", action="store_true",
                    help="si le nuage est gris : enlève le paragraphe")
    a = ap.parse_args()

    chemin = os.path.join(a.kit, "content", "page", PAGE + ".json")
    if not os.path.isfile(chemin):
        raise SystemExit("Page introuvable : %s" % chemin)
    page = json.load(open(chemin, encoding="utf-8"))
    racine = page.get("content", page)

    if a.retirer:
        n = remplacer(racine, AJOUT, "")
        if n != 1:
            raise SystemExit("Le paragraphe Cloudflare : %d occurrence(s) au lieu d'une." % n)
        print("   paragraphe Cloudflare retiré")
    else:
        deja = json.dumps(page, ensure_ascii=False)
        if "<strong>Cloudflare</strong>" in deja:
            raise SystemExit("Le paragraphe Cloudflare est déjà là.")
        n = remplacer(racine, ANCRE, AJOUT + ANCRE)
        if n != 1:
            raise SystemExit("L'ancre : %d occurrence(s) au lieu d'une." % n)
        print("   Cloudflare nommé, juste avant la messagerie")

    json.dump(page, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    texte = open(chemin, encoding="utf-8").read()
    attendu = not a.retirer
    if ("Cloudflare" in texte) != attendu:
        raise SystemExit("La relecture ne correspond pas à ce qui a été demandé.")
    print("   relu")
    return 0


if __name__ == "__main__":
    sys.exit(main())
