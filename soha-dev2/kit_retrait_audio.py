#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — retrait de la formule « Podcast audio · Audio seul · 200 $ ».

Décision de Mala, 10 septembre 2026 : cette formule disparaît partout.

Écrit comme un script plutôt que fait à la main parce qu'un retrait d'offre
touche quatre endroits qui doivent bouger ensemble, et qu'oublier le quatrième
laisse un site qui promet un prix qui n'existe plus :

  1. la carte elle-même, dans la page du studio ;
  2. le compte annoncé juste au-dessus — « quatre façons » devient « trois » ;
  3. la fourchette de prix de l'introduction — « de 200 $ à 420 $ » devient
     « de 300 $ à 420 $ », 300 $ étant la formule la moins chère qui reste ;
  4. les métadonnées de référencement, qui annoncent « dès 200 $ » à Google.

Le point 4 vit dans `build_site.py` et est traité là-bas ; ce script fait les
trois premiers, et **vérifie** que chacun a bien trouvé sa cible. Un retrait
partiel serait pire que pas de retrait du tout.

Ce qui n'est PAS touché, et il faut le dire parce que le nombre est le même :
« à partir de 200 $ + tx la soirée » sur la page des espaces. Ce 200 $-là est le
tarif de location du Studio en soirée de semaine, pas la formule podcast. Il
reste.

Usage :
    python3 kit_retrait_audio.py --kit <dossier du kit>
"""

import argparse
import json
import os
import sys

PAGE = "7355"                 # Le Studio podcast
CARTE = "30eae111"            # le conteneur de la formule « Audio seul »
ONGLET = "000503"             # l'onglet « Podcast audio » des conditions de service
CHOIX = "Podcast audio — 200 $"   # la ligne du menu déroulant du formulaire

REMPLACEMENTS = [
    ("Quatre façons de repartir avec ton épisode.",
     "Trois façons de repartir avec ton épisode."),
    ("De 200 $ à 420 $, tout compris.",
     "De 300 $ à 420 $, tout compris."),
]


def retirer(noeud, identifiant):
    """Enlève le conteneur portant cet identifiant, où qu'il soit dans l'arbre."""
    elements = noeud if isinstance(noeud, list) else noeud.get("elements", [])
    for i, e in enumerate(elements):
        if e.get("id") == identifiant:
            del elements[i]
            return True
        if retirer(e, identifiant):
            return True
    return False


def remplacer(noeud, avant, apres):
    """Remplace un texte dans tous les réglages de tous les widgets."""
    n = 0
    elements = noeud if isinstance(noeud, list) else noeud.get("elements", [])
    for e in elements:
        for cle, valeur in (e.get("settings") or {}).items():
            if isinstance(valeur, str) and avant in valeur:
                e["settings"][cle] = valeur.replace(avant, apres)
                n += 1
        n += remplacer(e, avant, apres)
    return n


def retirer_onglet(noeud, identifiant):
    """Enlève un onglet d'accordéon par son `_id`.

    Les conditions de service ont un onglet par formule : en laisser un qui
    décrit une offre retirée, c'est promettre par la porte de derrière.
    """
    for e in (noeud if isinstance(noeud, list) else noeud.get("elements", [])):
        for cle, valeur in (e.get("settings") or {}).items():
            if not isinstance(valeur, list):
                continue
            for i, onglet in enumerate(valeur):
                if isinstance(onglet, dict) and onglet.get("_id") == identifiant:
                    del valeur[i]
                    return True
        if retirer_onglet(e, identifiant):
            return True
    return False


def retirer_choix(noeud, ligne):
    """Enlève une ligne d'un menu déroulant de formulaire.

    C'est l'endroit le plus facile à oublier et le plus embarrassant : on retire
    une offre de la page, et le formulaire continue de la proposer.
    """
    n = 0
    for e in (noeud if isinstance(noeud, list) else noeud.get("elements", [])):
        for champ in (e.get("settings") or {}).get("form_fields", []) or []:
            options = champ.get("field_options")
            if not isinstance(options, str) or ligne not in options:
                continue
            gardees = [l for l in options.split("\n") if l.strip() != ligne]
            champ["field_options"] = "\n".join(gardees)
            n += 1
        n += retirer_choix(e, ligne)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kit", required=True, help="dossier du kit Elementor")
    a = ap.parse_args()

    chemin = os.path.join(a.kit, "content", "page", PAGE + ".json")
    if not os.path.isfile(chemin):
        raise SystemExit("Page introuvable : %s" % chemin)

    page = json.load(open(chemin, encoding="utf-8"))
    racine = page.get("content", page)

    if not retirer(racine, CARTE):
        raise SystemExit("La carte « Audio seul » (%s) est introuvable : "
                         "elle a peut-être déjà été retirée, ou la page a changé." % CARTE)
    print("   carte « Audio seul » retirée")

    if not retirer_onglet(racine, ONGLET):
        raise SystemExit("L'onglet « Podcast audio » (%s) est introuvable." % ONGLET)
    print("   onglet « Podcast audio » des conditions retiré")

    n = retirer_choix(racine, CHOIX)
    if n != 1:
        raise SystemExit("« %s » : %d menu(s) déroulant(s) au lieu d'un." % (CHOIX, n))
    print("   choix « %s » retiré du formulaire" % CHOIX)

    for avant, apres in REMPLACEMENTS:
        n = remplacer(racine, avant, apres)
        if n != 1:
            raise SystemExit("« %s » : %d occurrence(s) au lieu d'une seule." % (avant[:44], n))
        print("   %-46s → %s" % (avant[:44], apres[:44]))

    json.dump(page, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Le contrôle qui compte : plus une seule trace, nulle part dans le kit.
    reste = []
    for dossier, _, fichiers in os.walk(a.kit):
        for f in fichiers:
            if not f.endswith(".json"):
                continue
            texte = open(os.path.join(dossier, f), encoding="utf-8").read()
            if "Audio seul" in texte or "Podcast audio" in texte:
                reste.append(os.path.join(dossier, f))
    if reste:
        raise SystemExit("Il reste des traces : " + ", ".join(reste))
    print("   aucune trace restante dans le kit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
