#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — l'en-tête collant descend de 166 à 63 px au téléphone.

Le constat (département mobile, 15 septembre)
---------------------------------------------
À 390 px, l'en-tête prend 166 px : le logo à 60 % de la largeur, puis « Menu »
et « Réserver » sur une seconde ligne. Collé en haut, il mange un cinquième de
l'écran à chaque défilement. Sur ordinateur il fait 84 px.

Ce que le script fait (templates/7316.json, sous 767 px seulement)
----------------------------------------------------------------
· la colonne du logo passe de 60 % à 88 px (130 px en tablette, ce qu'elle rend déjà) ;
· la rangée passe de colonne à rangée, alignée au centre ;
· le padding du conteneur racine passe à 6/12.
Aucune couleur, aucun texte, rien au-dessus de 767 px.

    python3 kit_entete.py --kit <dossier>
"""
import argparse, json, os
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--kit", required=True); a = ap.parse_args()
    p = os.path.join(a.kit, "templates", "7316.json"); d = json.load(open(p, encoding="utf-8"))
    c = d["content"]; brut = isinstance(c, str); arbre = json.loads(c) if brut else c
    n = 0
    def marcher(x):
        nonlocal n
        s = x.get("settings") or {}; i = x.get("id")
        if i == "57473010":
            s["width_mobile"] = {"unit": "px", "size": 88}; s.setdefault("width_tablet", {"unit": "px", "size": 130}); n += 1
        elif i == "57b9361a":
            s["flex_direction_mobile"] = "row"; s["flex_align_items_mobile"] = "center"
            s.setdefault("flex_justify_content_mobile", "space-between"); n += 1
        elif i == "223de686":
            s["padding_mobile"] = {"unit": "px", "top": "6", "right": "12", "bottom": "6", "left": "12", "isLinked": False}; n += 1
        for e in x.get("elements") or []: marcher(e)
    for x in arbre: marcher(x)
    d["content"] = json.dumps(arbre, ensure_ascii=False) if brut else arbre
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("  en-tête : %d conteneur(s) réglé(s) pour le téléphone" % n)
if __name__ == "__main__": main()
