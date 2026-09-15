#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — les héros deviennent des images, pas des fonds.

Le constat
----------
Huit pages ouvrent sur une photo pleine largeur. Ces huit photos ne sont pas
des images : ce sont des `background_image` posés sur un conteneur Elementor.

Un fond CSS ne sait pas faire quatre choses, et ce sont exactement les quatre
qui comptent pour la plus grosse image de la page :

    1. `alt`          — un fond n'a pas de texte alternatif. Huit héros muets.
    2. `srcset`       — un téléphone télécharge la version 2 400 px.
    3. `fetchpriority`— le navigateur ne découvre le fond qu'après la feuille
                        de style ; une balise `<img>` est vue dans le HTML.
    4. le préchargement fiable — `imagesrcset` n'existe que pour les images.

Sur WordPress, aucun de ces quatre ne se rattrape après coup : ils se décident
à la source, dans le kit.

Ce que le script fait, et rien d'autre
--------------------------------------
Pour chacun des huit conteneurs de héros :

A. Le `background_image` quitte le conteneur. Le fond encre `#0E1A15` reste :
   c'est lui qui tient le texte en blanc pendant que la photo charge.
B. Une widget `image` est insérée EN PREMIER dans le conteneur, avec la même
   photo, la classe `soha-hero-fond`, et `image_size: full`.
C. Le voile `rgba(14,26,21,0.68)` quitte le réglage Elementor et passe dans la
   feuille : posé sur la widget image, il couvre la photo et rien d'autre.
D. Le conteneur reçoit `soha-hero`, son conteneur de texte `soha-hero-texte`.

Ce que le script REFUSE de faire
--------------------------------
Il ne change ni le voile, ni sa valeur, ni le cadrage, ni le texte, ni la
photo. Le rendu doit être IDENTIQUE au pixel près : c'est une opération de
structure, pas de design. Ce qui doit changer à l'œil se décide ailleurs.

    python3 kit_heros.py --kit <dossier> [--lire]
"""

import argparse
import glob
import json
import os

ENCRE = "#0E1A15"
VOILE = "rgba(14,26,21,0.68)"

DEBUT = "/* ==== soha-heros début ==== */"
FIN = "/* ==== soha-heros fin ==== */"

BLOC_CSS = DEBUT + """
/* ---- les héros en widget image · v04 ------------------------------------
   La photo n'est plus un fond : c'est une balise. Elle se place donc à la
   main, derrière le texte, et porte son voile elle-même.

   v02 : Elementor emballe chaque widget dans `.elementor-widget-container`.
   Sans hauteur sur cette enveloppe, le `height:100%` de l'image se résout
   contre une hauteur automatique — c'est-à-dire contre rien — et la photo
   retombe à sa taille naturelle. */
/* Pas d'`overflow:hidden` ici : il fabrique un contexte de formatage et
   empêche les marges des enfants de fusionner vers l'extérieur. Mesuré :
   prendre-soin perdait 105 px, espaces-professionnels en gagnait 298. La
   photo est en `inset:0` et en `object-fit:cover` — elle ne déborde pas. */
.soha-hero{position:relative}
/* `top/right/bottom/left` et non `inset` : Safari avant 14.1 ignore `inset`,
   et une photo de héros qui manque sur un iPad de 2020 est une photo qui
   manque. Les quatre propriétés coûtent trois mots de plus. */
.soha-hero-fond{position:absolute;top:0;right:0;bottom:0;left:0;width:100%;height:100%;
  margin:0;padding:0;z-index:0;pointer-events:none}
.soha-hero-fond > .elementor-widget-container{height:100%}
.soha-hero-fond img{width:100%;height:100%;object-fit:cover;display:block}
.soha-hero-fond::after{content:"";position:absolute;top:0;right:0;bottom:0;left:0;
  background:rgba(14,26,21,0.68)}
.soha-hero-texte{position:relative;z-index:1}
""" + FIN + "\n"

MARQUE = "les héros en widget image · v04"


def classes(s, ajout):
    """Ajoute une classe sans écraser celles qui sont déjà là."""
    presentes = (s.get("_css_classes") or "").split()
    if ajout not in presentes:
        presentes.append(ajout)
    s["_css_classes"] = " ".join(presentes)


def identifiant(eid):
    """Un identifiant Elementor voisin, stable d'une exécution à l'autre.

    Elementor n'exige qu'une chose : que l'identifiant soit unique dans la
    page. On le dérive du conteneur pour qu'il ne change pas si le script est
    relancé — un identifiant tiré au sort ferait un diff différent à chaque
    fois, et on ne saurait plus lire ce qu'on a changé.
    """
    return ("f" + eid)[:8]


def est_un_hero(noeud, profondeur):
    """Un héros, c'est une bannière de tête : un conteneur de premier niveau,
    avec une photo de fond ET un voile. Le fond décoratif enfoui au troisième
    niveau de l'accueil n'en est pas un — il n'ouvre pas la page."""
    if profondeur != 0 or noeud.get("elType") != "container":
        return False
    s = noeud.get("settings") or {}
    return (isinstance(s.get("background_image"), dict)
            and s["background_image"].get("url")
            and s.get("background_overlay_color"))


def convertir(noeud, journal, page):
    s = noeud["settings"]
    photo = s["background_image"]
    voile = s.get("background_overlay_color")
    if voile != VOILE:
        journal.append((page, noeud.get("id"), "voile inattendu : %s — laissé tel quel" % voile))
        return False

    for cle in ("background_image", "background_position", "background_size",
                "background_repeat", "background_overlay_background",
                "background_overlay_color", "background_overlay_opacity"):
        s.pop(cle, None)
    s.setdefault("background_background", "classic")
    s.setdefault("background_color", ENCRE)
    classes(s, "soha-hero")

    for enfant in noeud.get("elements") or []:
        if enfant.get("elType") == "container":
            classes(enfant.setdefault("settings", {}), "soha-hero-texte")

    noeud.setdefault("elements", []).insert(0, {
        "id": identifiant(noeud.get("id", "hero")),
        "elType": "widget",
        "widgetType": "image",
        "isInner": False,
        "elements": [],
        "settings": {
            "image": photo,
            "image_size": "full",
            "_css_classes": "soha-hero-fond",
        },
    })
    journal.append((page, noeud.get("id"), os.path.basename(photo["url"])))
    return True


def poser_le_style(kit, journal, ecrire=True):
    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if MARQUE in css:
        journal.append(("style", "-", "déjà posé"))
        return
    # Une version précédente du bloc se retire AVANT qu'on pose la neuve :
    # deux blocs empilés, et c'est le plus ancien qui gagne sur les règles
    # qu'il partage avec le nouveau — silencieusement.
    if DEBUT in css and FIN in css:
        css = css[:css.index(DEBUT)] + css[css.index(FIN) + len(FIN):]
        journal.append(("style", "-", "bloc précédent retiré"))
    st["custom_css"] = css + BLOC_CSS
    if ecrire:
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    journal.append(("style", "-", "%d caractères" % len(BLOC_CSS)))


def appliquer(kit, ecrire=True):
    journal = []
    touches = 0
    for f in sorted(glob.glob(os.path.join(kit, "content", "*", "*.json"))):
        doc = json.load(open(f, encoding="utf-8"))
        contenu = doc.get("content")
        brut = isinstance(contenu, str)
        arbre = json.loads(contenu) if brut else contenu
        if not isinstance(arbre, list):
            continue
        page = os.path.basename(f)
        change = False
        for noeud in arbre:
            if est_un_hero(noeud, 0) and convertir(noeud, journal, page):
                change = True
        if change:
            touches += 1
            doc["content"] = json.dumps(arbre, ensure_ascii=False) if brut else arbre
            if ecrire:
                json.dump(doc, open(f, "w", encoding="utf-8"),
                          ensure_ascii=False, separators=(",", ":"))
    poser_le_style(kit, journal, ecrire)
    return journal, touches


def main():
    ap = argparse.ArgumentParser(description="Les héros du kit deviennent des widgets image.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true", help="n'écrit rien, dit seulement ce qui changerait")
    a = ap.parse_args()
    journal, touches = appliquer(a.kit, ecrire=not a.lire)
    for ligne in journal:
        print("  %-14s %-10s %s" % ligne)
    print("%d page(s) %s." % (touches, "à toucher" if a.lire else "touchée(s)"))


if __name__ == "__main__":
    main()
