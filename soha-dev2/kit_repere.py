#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — le troisième repère de l'accueil.

Le constat, et sa confirmation
------------------------------
Le département conformité : « Le repère "Membres en règle" fait dire au
Centre, en trois mots et au nom de neuf tiers, une appartenance d'association
que quatre d'entre eux ne déclarent nulle part. » Deux sceptiques ont refait
le décompte indépendamment : 5 sur 9.

Mala, le 14 septembre : « il n'y a pas nécessairement d'ordre pour certains
thérapeutes ».

Ce n'est donc pas une affirmation invérifiée : c'est une affirmation
STRUCTURELLEMENT impossible pour une partie des personnes nommées. Certaines
pratiques n'ont pas d'ordre professionnel au Québec — il n'existe rien dont
elles puissent être « membres en règle ».

Le geste
--------
Le repère porte déjà, sous son titre, la phrase exacte et vérifiable :

    « La plupart des thérapeutes peuvent émettre des reçus d'assurance. »

Le titre prend le même registre que ses deux voisins — « Sur le Plateau »,
« Ouvert sept jours » : un fait court sur le lieu, rien sur le statut d'un
tiers.

    « Membres en règle »  →  « Reçus d'assurance »

PROPOSITION DE TEXTE — c'est un mot de Mala que je remplace, et je le déclare.
Le sous-titre, lui, n'est pas touché : il dit « la plupart », il est exact, et
c'est lui qui porte l'information utile au visiteur.

    python3 kit_repere.py --kit <dossier> [--lire]
"""

import argparse
import json
import os
import sys

PAGE = "content/page/7319.json"
REPERE = "7dbfb0d5"
AVANT = "Membres en règle"
APRES = "Reçus d'assurance"


def appliquer(kit, ecrire=True):
    chemin = os.path.join(kit, PAGE)
    d = json.load(open(chemin, encoding="utf-8"))
    journal = []
    vus = [0]

    def marche(o):
        if isinstance(o, dict):
            # `_title` est l'étiquette interne d'Elementor : invisible au
            # public, mais c'est ce que Mala lit dans le panneau des calques.
            # La laisser dire « Membres en règle » ferait croire que le geste
            # n'a pas été fait.
            s0 = o.get("settings") or {}
            if s0.get("_title") == AVANT:
                s0["_title"] = APRES
                vus[0] += 1
            if o.get("id") == REPERE:
                s = o.setdefault("settings", {})
                if s.get("title") == AVANT:
                    s["title"] = APRES
                    vus[0] += 1
                elif s.get("title") == APRES:
                    journal.append("repère : déjà « %s »" % APRES)
                else:
                    raise SystemExit("repère : titre inattendu « %s »" % s.get("title"))
            for v in o.values():
                marche(v)
        elif isinstance(o, list):
            for v in o:
                marche(v)

    marche(d)
    if vus[0]:
        if ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
        journal.append("repère : « %s » → « %s »" % (AVANT, APRES))
    elif not journal:
        raise SystemExit("repère : %s introuvable" % REPERE)
    return journal


def main():
    ap = argparse.ArgumentParser(description="Le troisième repère de l'accueil.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    for l in appliquer(a.kit, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
