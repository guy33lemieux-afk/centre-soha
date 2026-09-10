#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — neutraliser les dates passées, en attendant les nouvelles.

Décision de Mala, 10 septembre 2026 : « on retire les dates partout, je te les
redonnerai. » Ce script les remplace par une formule d'attente honnête, plutôt
que de les effacer : un visiteur doit comprendre que la chose existe et que la
date arrive, pas croire qu'elle a disparu.

Trois choses ne sont **pas** touchées, et il faut le dire :

  · **12 – 13 septembre 2026** — c'est dans deux jours. Retirer la seule date
    encore valable, et la plus imminente, ce serait obéir au mot « partout »
    contre l'intention.

  · **La liste d'archives de « Se transformer »** (`archive-liste`) — une
    archive dont on retire les dates ne raconte plus rien. Son travail est
    justement de porter le passé.

  · **Les horaires sans date** — « Mardis, 18 h – 19 h », « Vendredi soir
    18 h 30 – 21 h 30 ». Ce sont des habitudes, pas des dates ; elles restent
    vraies quand la session reprend.

Sur la page Core Energetics, les échéances commerciales périmées (rabais de
pré-paiement, date limite de remboursement) sont renvoyées à l'organisateur —
c'est son atelier, son barème, et la page dit déjà « pour s'inscrire : auprès de
l'organisateur·rice, pas auprès du Centre ». Réécrire sa politique de
remboursement à sa place serait pire que de la laisser vide.

Usage :
    python3 kit_dates.py --kit <dossier du kit>
"""

import argparse
import json
import os
import re
import sys

# La page « Se ressourcer » a déjà sa formule d'attente, sur un cours qui n'a
# pas encore de date : « Niveau 1 · prochaine session à venir ». On l'adopte
# plutôt que d'en inventer une deuxième — deux façons de dire la même chose sur
# la même page, c'est déjà une incohérence.
ATTENTE = "Prochaine session à venir"

# Ce qui trahit une date dans une ligne « Session » : un nom de mois, ou la
# tournure « jusqu'au ». Les lignes déjà neutres — « toute l'année », « dates
# variées », « annoncé sur la page de réservation » — n'en portent aucune et ne
# doivent pas être touchées.
DATEE = re.compile(r"janvier|février|mars|avril|mai|juin|juillet|août|septembre"
                   r"|octobre|novembre|décembre|[Jj]usqu'au", re.IGNORECASE)

# Chaque retouche : page, motif, remplacement, combien d'occurrences exigées.
RETOUCHES = [
    # « Se ressourcer » — onze grilles de cours, dont sept portent une date
    # passée. Les quatre autres disent déjà « toute l'année », « dates variées »
    # ou « annoncé sur la page de réservation » : on n'y touche pas.
    ("7326", re.compile(r"<dt>Session</dt><dd>(.*?)</dd>"),
     lambda m: ("<dt>Session</dt><dd>%s</dd>" % ATTENTE) if DATEE.search(m.group(1))
               else m.group(0), 7),

    # « Atelier d'écriture spontanée »
    ("7389", re.compile(r"<strong>Date\s*:</strong>\s*jeudi 12 juin de 14h à 17h"),
     "<strong>Date :</strong> à annoncer", 1),

    # « Core Energetics » — la pastille de dates en haut de page. Le texte est
    # noyé dans un `<span>` très habillé : on vise donc le texte, pas la balise.
    ("7390", re.compile(r">10 – 11 juillet 2026<"),
     ">Dates à annoncer<", 1),

    # « Core Energetics » — les échéances, renvoyées à l'organisateur
    ("7390", re.compile(r"avant le vendredi 17 juillet 2026"),
     "avant la date limite annoncée par l'organisateur", 1),
    ("7390", re.compile(r"si payé avant le 3 juillet 2026"),
     "si payé avant la date limite annoncée par l'organisateur", 1),
    ("7390", re.compile(r"aucun remboursement après le vendredi 3 juillet 2026"),
     "aucun remboursement après la date limite annoncée par l'organisateur", 1),
    ("7390", re.compile(r"<em>Dates:</em>\s*Vendredi soir \(18h30-21h30\) et samedi \(10h-17h\), "
                        r"les 10 et 11 juillet 2026\."),
     "<em>Dates:</em> à annoncer — vendredi soir (18h30-21h30) et samedi (10h-17h).", 1),
]


def retoucher(noeud, motif, remplacement):
    """Remplace dans tous les réglages, et compte ce qui a VRAIMENT changé.

    `remplacement` peut être une fonction : elle reçoit la correspondance et
    peut décider de ne rien changer. On ne compte donc pas les correspondances,
    on compte les modifications — sinon une ligne laissée intacte gonflerait le
    total et le garde-fou ne garderait plus rien.
    """
    n = 0
    for e in (noeud if isinstance(noeud, list) else noeud.get("elements", [])):
        for cle, valeur in (e.get("settings") or {}).items():
            if not isinstance(valeur, str):
                continue
            compte = [0]

            def un(m):
                neuf = remplacement(m) if callable(remplacement) else m.expand(remplacement)
                if neuf != m.group(0):
                    compte[0] += 1
                return neuf

            neuf = motif.sub(un, valeur)
            if compte[0]:
                e["settings"][cle] = neuf
                n += compte[0]
        n += retoucher(e, motif, remplacement)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kit", required=True, help="dossier du kit Elementor")
    a = ap.parse_args()

    pages = {}
    total = 0
    for page, motif, remplacement, attendu in RETOUCHES:
        chemin = os.path.join(a.kit, "content", "page", page + ".json")
        if page not in pages:
            if not os.path.isfile(chemin):
                raise SystemExit("Page introuvable : %s" % chemin)
            pages[page] = json.load(open(chemin, encoding="utf-8"))

        d = pages[page]
        n = retoucher(d.get("content", d), motif, remplacement)
        if n != attendu:
            raise SystemExit(
                "Page %s — « %s » : %d occurrence(s) au lieu de %d. "
                "La page a changé de forme ; rien n'a été enregistré."
                % (page, motif.pattern[:52], n, attendu))
        montre = (ATTENTE if callable(remplacement) else remplacement)
        print("   %-6s %-2d× %s" % (page, n, re.sub(r"<[^>]+>", "", montre)[:58]))
        total += n

    for page, d in pages.items():
        chemin = os.path.join(a.kit, "content", "page", page + ".json")
        json.dump(d, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("   %d passage(s) neutralisé(s)" % total)

    # La relecture : plus aucune des dates retirées, et celles qu'on garde sont là.
    tout = ""
    for f in sorted(os.listdir(os.path.join(a.kit, "content", "page"))):
        tout += open(os.path.join(a.kit, "content", "page", f), encoding="utf-8").read()
    for interdit in ("13 janvier au 10 mars", "17 février au 9 juin", "9 avril au 28 mai",
                     "13 mars au 15 mai", "15 février au 5 avril", "9 avril au 14 mai",
                     "Jusqu'au 1er juin", "jeudi 12 juin de 14h",
                     "3 juillet 2026", "17 juillet 2026"):
        if interdit in tout:
            raise SystemExit("Il reste « %s » quelque part." % interdit)
    if "12 – 13 septembre 2026" not in tout:
        raise SystemExit("La date du 12–13 septembre a disparu : elle devait rester.")
    for garde in ("En direct en ligne, toute l'année", "Dates variées",
                  "Annoncé sur la page de réservation"):
        if garde not in tout:
            raise SystemExit("Une ligne déjà neutre a été emportée : « %s »." % garde)
    print("   relu : les dates passées sont parties, le 12–13 septembre et les")
    print("          lignes déjà neutres sont restés")
    return 0


if __name__ == "__main__":
    sys.exit(main())
