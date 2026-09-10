#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — aligner les liens internes du kit sur l'adresse réelle du site.

Trouvé le 10 septembre 2026 : les 73 liens internes du kit pointent vers
`/dev2/…`, alors que le manifeste déclare `https://centresoha.com/dev` et que
toutes les images vivent sous `/dev/wp-content/uploads/`. Importé tel quel, le
kit donne un site dont **chaque lien interne mène à une page introuvable** —
menu compris.

Pourquoi ça n'a pas sauté aux yeux plus tôt : le générateur du site statique
traduit ces adresses en fichiers locaux, donc le site HTML fonctionnait
parfaitement. C'est WordPress, et lui seul, qui trébuche.

Et pourquoi l'import ne le corrige pas tout seul : Elementor réécrit l'origine
des adresses **absolues** (`https://ancien-site.com/…`) au moment d'importer.
Une adresse qui commence par une barre oblique n'a pas d'origine à réécrire —
elle passe telle quelle, et reste fausse.

Le préfixe n'est pas deviné : il est lu dans le manifeste, ou donné à la main.

Usage :
    python3 kit_liens.py --kit <dossier>                  # préfixe lu du manifeste
    python3 kit_liens.py --kit <dossier> --prefixe /dev2  # si le site déménage
    python3 kit_liens.py --kit <dossier> --verifier       # ne rien écrire, juste voir
"""

import argparse
import json
import os
import re
import sys

# Les adresses internes du kit : une barre oblique, un segment de dossier, la
# suite. On ne touche jamais à `//` (protocole omis) ni à `/wp-content/…`.
INTERNE = re.compile(r'(?<![:/\w])/(dev\d*)(/[^"\'\\ )]*|/)')


def prefixe_du_manifeste(kit):
    chemin = os.path.join(kit, "manifest.json")
    if not os.path.isfile(chemin):
        return None
    try:
        site = json.load(open(chemin, encoding="utf-8")).get("site", "")
    except Exception:
        return None
    m = re.match(r"https?://[^/]+(/[^/]+)/?$", site or "")
    return m.group(1) if m else None


def parcourir(kit):
    for racine, _, fichiers in os.walk(kit):
        for f in sorted(fichiers):
            if f.endswith(".json") or f.endswith(".xml"):
                yield os.path.join(racine, f)


def aligner(kit, prefixe, ecrire=True):
    voulu = "/" + prefixe.strip("/")
    trouves, changes = {}, 0

    for chemin in parcourir(kit):
        texte = open(chemin, encoding="utf-8").read()

        def un(m):
            actuel = "/" + m.group(1)
            trouves[actuel] = trouves.get(actuel, 0) + 1
            return voulu + m.group(2)

        neuf = INTERNE.sub(un, texte)
        if neuf != texte:
            changes += 1
            if ecrire:
                open(chemin, "w", encoding="utf-8").write(neuf)

    return voulu, trouves, changes


def main():
    ap = argparse.ArgumentParser(description="Aligner les liens internes du kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--prefixe", default=None,
                    help="par défaut : celui déclaré dans le manifeste")
    ap.add_argument("--verifier", action="store_true", help="n'écrit rien")
    a = ap.parse_args()

    prefixe = a.prefixe or prefixe_du_manifeste(a.kit)
    if not prefixe:
        raise SystemExit("Aucun préfixe trouvé dans le manifeste : donne-le avec --prefixe.")

    voulu, trouves, changes = aligner(a.kit, prefixe, ecrire=not a.verifier)

    print("Préfixe visé : %s%s" % (voulu, "  (du manifeste)" if not a.prefixe else ""))
    if not trouves:
        print("Aucun lien interne trouvé — rien à faire, ou le kit a changé de forme.")
        return 0

    for actuel, combien in sorted(trouves.items()):
        etat = "déjà bon" if actuel == voulu else "→ corrigé"
        print("   %-8s %3d lien(s)  %s" % (actuel, combien, etat))

    if a.verifier:
        print("\nRien n'a été écrit (--verifier).")
        return 1 if any(k != voulu for k in trouves) else 0

    print("   %d fichier(s) réécrit(s)" % changes)

    # La relecture : plus aucun autre préfixe nulle part.
    restants = set()
    for chemin in parcourir(a.kit):
        for m in INTERNE.finditer(open(chemin, encoding="utf-8").read()):
            if "/" + m.group(1) != voulu:
                restants.add("/" + m.group(1))
    if restants:
        raise SystemExit("Il reste des liens vers %s." % ", ".join(sorted(restants)))
    print("   relu : tous les liens internes pointent vers %s" % voulu)
    return 0


if __name__ == "__main__":
    sys.exit(main())
