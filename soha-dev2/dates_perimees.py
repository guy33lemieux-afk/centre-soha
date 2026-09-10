#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — les dates que le site annonce et qui sont déjà passées.

Un site qui affiche « Session du 13 janvier au 10 mars » en septembre ne se
plaint pas, ne lève aucune erreur, et ne s'en va pas tout seul. Il dit
simplement, à chaque visiteur, que plus rien ne se passe ici depuis le
printemps. C'est le genre de défaut qu'on ne voit plus parce qu'on l'a écrit
soi-même.

Cet outil lit les dates en français dans un kit Elementor ou dans le site
fabriqué, et signale celles qui sont derrière nous.

Ce qu'il ne fait pas, et c'est délibéré : proposer des dates de remplacement.
Personne ici ne sait quand la prochaine session commence, sauf le Centre.
Inventer une date sur une page de cours, ce serait pire que la laisser périmée.

Usage :
    python3 dates_perimees.py --dossier <kit ou site>
    python3 dates_perimees.py --dossier <…> --le 2026-12-01   # se projeter
"""

import argparse
import datetime
import json
import os
import re
import sys

MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
        "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9,
        "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}

MOTIF = re.compile(
    r"(\d{1,2})\s*(?:er)?\s+(%s)\s*(20\d\d)?" % "|".join(MOIS),
    re.IGNORECASE)

# Ce qui parle du passé au passé n'est pas périmé : un article qui raconte une
# soirée de mars ne promet rien. On ne signale que ce qui a l'air d'une annonce.
PROMESSES = ("session", "quand", "date", "dates", "atelier", "retraite", "inscription",
             "inscrire", "avant le", "prochaine", "prochain", "rendez-vous", "cours",
             "dépôt", "remboursement", "tarif", "réservation")


def titres_du_manifeste(dossier):
    """Les pages d'un kit sont des fichiers numérotés ; leurs noms sont ailleurs.

    Sans ça, le rapport dit « 7326.json » là où Mala attend « Se ressourcer » —
    et un rapport qu'il faut décoder n'est pas un rapport.
    """
    chemin = os.path.join(dossier, "manifest.json")
    if not os.path.isfile(chemin):
        return {}
    try:
        manifeste = json.load(open(chemin, encoding="utf-8"))
    except Exception:
        return {}

    trouves = {}

    def descendre(o):
        if isinstance(o, dict):
            for cle, valeur in o.items():
                if isinstance(valeur, dict) and str(cle).isdigit() and valeur.get("title"):
                    trouves[str(cle)] = valeur["title"]
                descendre(valeur)
        elif isinstance(o, list):
            for x in o:
                descendre(x)

    descendre(manifeste)
    return trouves


def textes_du_json(chemin, titres=None):
    """Chaque chaîne de réglage d'un fichier de page Elementor, avec son titre."""
    try:
        d = json.load(open(chemin, encoding="utf-8"))
    except Exception:
        return
    numero = os.path.splitext(os.path.basename(chemin))[0]
    titre = (d.get("title") or d.get("post_title")
             or (titres or {}).get(numero) or os.path.basename(chemin))

    def descendre(noeud):
        for e in (noeud if isinstance(noeud, list) else noeud.get("elements", [])):
            for valeur in (e.get("settings") or {}).values():
                if isinstance(valeur, str) and valeur.strip():
                    yield valeur
                elif isinstance(valeur, list):
                    for x in valeur:
                        if isinstance(x, dict):
                            for y in x.values():
                                if isinstance(y, str) and y.strip():
                                    yield y
            for t in descendre(e):
                yield t

    for t in descendre(d.get("content", d)):
        yield titre, t


def textes_du_html(chemin):
    s = open(chemin, encoding="utf-8", errors="replace").read()
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    titre = (m.group(1).strip() if m else os.path.basename(chemin))
    yield titre, s


def nettoyer(html):
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def perimees(dossier, le_jour):
    titres = titres_du_manifeste(dossier)
    trouvailles = []
    for racine, _, fichiers in os.walk(dossier):
        for f in sorted(fichiers):
            chemin = os.path.join(racine, f)
            if f.endswith(".json") and "content" in racine:
                source = textes_du_json(chemin, titres)
            elif f.endswith(".html"):
                source = textes_du_html(chemin)
            else:
                continue

            for titre, brut in source:
                texte = nettoyer(brut)
                for m in MOTIF.finditer(texte):
                    jour = int(m.group(1))
                    mois = MOIS[m.group(2).lower()]
                    annee = int(m.group(3)) if m.group(3) else le_jour.year
                    try:
                        quand = datetime.date(annee, mois, jour)
                    except ValueError:
                        continue
                    if quand >= le_jour:
                        continue
                    autour = texte[max(0, m.start() - 70):m.end() + 45].lower()
                    if not any(mot in autour for mot in PROMESSES):
                        continue
                    trouvailles.append((
                        quand,
                        titre,
                        os.path.relpath(chemin, dossier),
                        " ".join(texte[max(0, m.start() - 60):m.end() + 40].split()),
                    ))
    # une même phrase peut apparaître dans le kit ET dans le site fabriqué
    vues, propres = set(), []
    for t in sorted(trouvailles):
        cle = (t[0], t[1], t[3])
        if cle not in vues:
            vues.add(cle)
            propres.append(t)
    return propres


def main():
    ap = argparse.ArgumentParser(description="Les dates déjà passées que le site annonce.")
    ap.add_argument("--dossier", required=True, help="kit Elementor ou site fabriqué")
    ap.add_argument("--le", default=None, help="date de référence (AAAA-MM-JJ), défaut : aujourd'hui")
    a = ap.parse_args()

    le_jour = (datetime.date.fromisoformat(a.le) if a.le
               else datetime.date.today())
    trouvailles = perimees(a.dossier, le_jour)

    print("Référence : %s" % le_jour.isoformat())
    if not trouvailles:
        print("Aucune date passée annoncée comme si elle était à venir.")
        return 0

    print("\n%d passage(s) à revoir :\n" % len(trouvailles))
    page = None
    for quand, titre, fichier, extrait in trouvailles:
        if titre != page:
            page = titre
            print("── %s  (%s)" % (titre, fichier))
        print("   %s   …%s…" % (quand.isoformat(), extrait))
    print("\nAucune date de remplacement n'est proposée : c'est au Centre de les dire.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
