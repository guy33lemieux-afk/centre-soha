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
IVOIRE = "#F4F0E7"
SOIGNER = "#19A7DB"      # l'accent d'une école de soha.live — il n'a rien à faire ici
VOILE = "rgba(14,26,21,0.68)"

DEBUT = "/* ==== soha-heros début ==== */"
FIN = "/* ==== soha-heros fin ==== */"

BLOC_CSS = DEBUT + """
/* ---- les héros en widget image · v06 ------------------------------------
   La photo n'est plus un fond : c'est une balise. Elle se place donc à la
   main, derrière le texte.

   v05 — LE VOILE QUITTE LA PHOTO. Mala : « enlève-moi le voile sur les
   photos ». Le voile uniforme rgba(14,26,21,0.68) repeignait la photo en
   froid (mesuré : 94,2 % de pixels chauds avant, 4,2 % après). Mais voile
   retiré, 24 textes tombaient sous 4,5. Donc : le texte descend au bas du
   héros, et un dégradé d'encre ne monte que sous lui — le haut de la photo
   est nu, le texte garde son sol. Les arrêts du dégradé sont MESURÉS par
   porte_du_contraste.py sur les huit pages, pas choisis à l'œil.

   v04 — `top/right/bottom/left` et non `inset` : Safari avant 14.1 ignore
   `inset`. v03 — pas d'`overflow:hidden` (il décale les hauteurs). v02 —
   `height:100%` sur `.elementor-widget-container`, sinon la photo retombe
   à sa taille naturelle. */
.soha-hero{position:relative;min-height:min(78vh,720px);justify-content:flex-end}
.soha-hero-fond{position:absolute;top:0;right:0;bottom:0;left:0;width:100%;height:100%;
  margin:0;padding:0;z-index:0;pointer-events:none}
.soha-hero-fond > .elementor-widget-container{height:100%}
.soha-hero-fond img{width:100%;height:100%;object-fit:cover;display:block}
.soha-hero-fond::after{content:"";position:absolute;top:0;right:0;bottom:0;left:0;
  background:linear-gradient(180deg,
    rgba(14,26,21,0) 0%, rgba(14,26,21,0) 16%,
    rgba(14,26,21,.58) 36%, rgba(14,26,21,.84) 56%, rgba(14,26,21,.92) 100%)}
.soha-hero-texte{position:relative;z-index:1}
/* Le surtitre est un CARTEL : DM Mono sur encre, comme « PLANCHE 01 » sur
   l'accueil. Posé en haut du bloc de texte, il tombait sur la partie claire
   de la photo — mesuré 1,75 à 3,86 pour 4,5. Sur encre plein, il tient
   partout, quelle que soit la photo. */
.soha-hero-texte .elementor-widget-heading:first-child .elementor-heading-title{
  display:inline-block;background:#0E1A15;padding:6px 12px 6px 14px;margin-left:0}
@media (max-width:767px){.soha-hero{min-height:min(72vh,600px)}}
""" + FIN + "\n"

MARQUE = "les héros en widget image · v06"


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
    # v05 : le texte au bas du héros, sur la partie dense du dégradé. Le
    # padding haut ne sert plus à rien : c'est la hauteur minimale qui fait
    # respirer la photo.
    s["flex_justify_content"] = "flex-end"
    p = s.get("padding") if isinstance(s.get("padding"), dict) else {}
    s["padding"] = {"unit": "px", "top": "72", "bottom": "64",
                    "left": p.get("left", "22"), "right": p.get("right", "22"), "isLinked": False}

    for enfant in noeud.get("elements") or []:
        if enfant.get("elType") == "container":
            classes(enfant.setdefault("settings", {}), "soha-hero-texte")
            surtitres_en_ivoire(enfant, journal, page)

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


def surtitres_en_ivoire(conteneur, journal, page):
    """Le surtitre du héros (« LOUER LE STUDIO AU 961 ») était en cyan Soigner,
    lettres et filet. Depuis que le voile a quitté la photo, il tombe sur sa
    partie nue : mesuré illisible, et jamais mesuré par la porte, qui ne
    regardait que le texte clair. En ivoire, il est clair — donc mesuré —
    et il ne porte plus la couleur d'une école de l'autre pôle."""
    n = 0
    for w in conteneur.get("elements") or []:
        st = w.get("settings") or {}
        if w.get("widgetType") == "heading" and st.get("title_color", "").upper() == SOIGNER:
            st["title_color"] = IVOIRE
            if st.get("_border_color", "").upper() == SOIGNER:
                st["_border_color"] = IVOIRE
            n += 1
    if n:
        journal.append((page, conteneur.get("id"), "%d surtitre(s) en ivoire" % n))
    return n


def deja_converti(noeud):
    s = noeud.get("settings") or {}
    return noeud.get("elType") == "container" and "soha-hero" in (s.get("_css_classes") or "").split()


def retoucher(noeud, journal, page):
    """Un héros converti par une version précédente reçoit les réglages v05."""
    s = noeud["settings"]
    change = 0
    for enfant in noeud.get("elements") or []:
        if enfant.get("elType") == "container":
            change += surtitres_en_ivoire(enfant, journal, page)
    if s.get("flex_justify_content") == "flex-end" and (s.get("padding") or {}).get("top") == "72":
        return bool(change)
    s["flex_justify_content"] = "flex-end"
    p = s.get("padding") if isinstance(s.get("padding"), dict) else {}
    s["padding"] = {"unit": "px", "top": "72", "bottom": "64",
                    "left": p.get("left", "22"), "right": p.get("right", "22"), "isLinked": False}
    journal.append((page, noeud.get("id"), "v05 : texte en bas, padding 72/64"))
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
            elif deja_converti(noeud) and retoucher(noeud, journal, page):
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
