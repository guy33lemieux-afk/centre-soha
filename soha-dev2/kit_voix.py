#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — une voix sur l'accueil.

Le constat
----------
Le département langue-vivante, confirmé par trois sceptiques : « Zéro
guillemet, zéro "je", zéro personne nommée sur tout l'accueil — pendant que
neuf voix réelles, déjà écrites à la première personne, dorment à un clic. »

Mesuré : 0 guillemet de citation et 0 « je » sur la page d'accueil, dans le
kit comme au rendu. Le conseil de design ajoute : « C'est le seul geste qui
réglerait "plate" sans ajouter ni couleur ni mouvement. »

Ce que ce script N'A PAS fait
-----------------------------
Il n'a inventé aucune phrase. Mala a écrit « je te fais confiance pour régler
cela » — cette confiance ne peut pas fabriquer un verbatim. Mettre des mots
dans la bouche d'une personne réelle et nommée reste interdit, quelle que
soit la permission reçue, parce que la permission ne vient pas de la personne
concernée.

Ce qu'il a fait, à la place
---------------------------
Il est allé chercher une phrase QUI EXISTE DÉJÀ, écrite à la première
personne, publiée sous son nom, sur ce site, par la personne elle-même —
`content/page/7339.json`, page « Prendre soin de soi ». Elle est reprise au
mot près, attribuée, et liée à sa page. Rien n'est créé : une parole déjà
publique change de place.

L'attribution a été vérifiée par l'ORDRE DU DOCUMENT, pas par proximité de
texte : trois autres praticien·nes écrivent à la première personne dans le
même fichier, et se tromper de nom serait faire dire à quelqu'un ce qu'il
n'a pas dit.

Ce qui reste à Mala
-------------------
1. QUI. Neuf artisan·es travaillent au 961 ; une seule paraît en page
   d'accueil. C'est une faveur, donc une décision d'affaires — pas la mienne.
   Changer de voix, c'est changer trois chaînes dans ce fichier.
2. L'ACCORD. La phrase est publiée sur sa page ; la porter en page d'accueil
   est un autre usage. Il se demande.

Trois textes sont de moi et je les déclare :
   · le surtitre « UNE VOIX DU 961 »
   · la mention « Yuv Baboolall, au 961 »
   · rien d'autre — la citation n'est pas retouchée d'un signe.

    python3 kit_voix.py --kit <dossier> [--lire]
"""

import argparse
import json
import os
import sys

PAGE = "content/page/7319.json"
APRES = "60df18a0"          # on se pose juste après la bande des portes…
AVANT = "4ea69c6f"          # …et juste avant « Le lieu », qui change de registre

SECTION = "5a4c0e1"
IDS = ("5a4c0e2", "5a4c0e3", "5a4c0e4", "5a4c0e5")

# ── Ce qui vient de la personne, au mot près ────────────────────────────────
CITATION = ("Je suis convaincu que chaque individu porte en lui un potentiel "
            "immense, souvent freiné par des croyances limitantes.")
QUI = "Yuv Baboolall"
SOURCE = "content/page/7339.json — page « Prendre soin de soi »"

# ── Ce qui vient de moi, et que je déclare ─────────────────────────────────
SURTITRE = "UNE VOIX DU 961"
MENTION = "%s, au 961" % QUI
LIEN = "/dev/prendre-soin/"   # relevé dans le kit, pas deviné : c'est l'URL que les autres liens de la page emploient

MARQUEUR = "une voix sur l'accueil · v01"

BLOC_CSS = """


/* ============================================================
   SOHA — une voix sur l'accueil · v01 · 14 septembre 2026
   L'accueil ne citait personne : zero guillemet, zero « je »,
   zero nom, pendant que neuf artisan·es ecrivent deja a la
   premiere personne a un clic de la. La citation est reprise
   au mot pres de la page « Prendre soin de soi ».
   Aucune surface nouvelle : le sol reste l'ivoire des sections
   voisines. La distinction est portee par la typographie, pas
   par un septieme blanc — le conseil a montre que le site en
   fabriquait deja six dont aucun ne travaille.
   Contrastes sur ivoire : encre 15,68 · #3F4A45 8,11 · #5A6460 5,39.
   ============================================================ */
.soha-voix blockquote{margin:0;max-width:30ch}
.soha-voix blockquote p{margin:0}
"""


def widget_titre(i, texte, niveau, couleur, police, taille, reglages=None):
    s = {
        "title": texte, "header_size": niveau, "title_color": couleur,
        "typography_typography": "custom", "typography_font_family": police,
        "typography_font_size": {"unit": "px", "size": taille},
    }
    s.update(reglages or {})
    return {"id": i, "settings": s, "elements": [],
            "isInner": False, "widgetType": "heading", "elType": "widget"}


def widget_texte(i, html, couleur, police, taille, reglages=None):
    s = {
        "editor": html, "text_color": couleur,
        "typography_typography": "custom", "typography_font_family": police,
        "typography_font_size": {"unit": "px", "size": taille},
    }
    s.update(reglages or {})
    return {"id": i, "settings": s, "elements": [],
            "isInner": False, "widgetType": "text-editor", "elType": "widget"}


def batir():
    surtitre = widget_titre(
        IDS[0], SURTITRE, "h6", "#5A6460", "DM Mono", 12,
        {"typography_font_weight": "400",
         "typography_letter_spacing": {"unit": "em", "size": 0.2},
         "typography_text_transform": "uppercase",
         "_margin": {"unit": "px", "top": "0", "bottom": "18", "left": "0",
                     "right": "0", "isLinked": False},
         "_border_border": "solid",
         "_border_width": {"unit": "px", "top": "0", "bottom": "0", "left": "2",
                           "right": "0", "isLinked": False},
         "_border_color": "#19A7DB",
         "_padding": {"unit": "px", "top": "0", "bottom": "0", "left": "14",
                      "right": "0", "isLinked": False}})

    # L'italique porte l'accent ; sur fond clair il reste encre. C'est la
    # clause posee ce matin : Soigner ne porte pas de lettres sur fond clair.
    citation = widget_texte(
        IDS[1], "<blockquote><p>%s</p></blockquote>" % CITATION, "#0E1A15",
        "Fraunces", 32,
        {"typography_font_weight": "400",
         "typography_font_style": "italic",
         "typography_line_height": {"unit": "em", "size": 1.22},
         "typography_letter_spacing": {"unit": "em", "size": -0.012},
         "_margin": {"unit": "px", "top": "0", "bottom": "20", "left": "0",
                     "right": "0", "isLinked": False}})

    mention = widget_texte(
        IDS[2], '<a href="%s">%s</a>' % (LIEN, MENTION), "#3F4A45",
        "Schibsted Grotesk", 14,
        {"typography_font_weight": "600",
         "_margin": {"unit": "px", "top": "0", "bottom": "0", "left": "0",
                     "right": "0", "isLinked": False}})

    interieur = {
        "id": IDS[3],
        "settings": {"content_width": "boxed",
                     "boxed_width": {"unit": "px", "size": 1200},
                     "flex_direction": "column",
                     "_title": "Une voix du 961"},
        "elements": [surtitre, citation, mention],
        "isInner": True, "elType": "container",
    }
    return {
        "id": SECTION,
        "settings": {"content_width": "full",
                     "padding": {"unit": "px", "top": "96", "right": "22",
                                 "bottom": "96", "left": "22", "isLinked": False},
                     "flex_direction": "column", "flex_align_items": "center",
                     "background_background": "classic",
                     "background_color": "#F4F0E7",
                     "_title": "Une voix du 961",
                     "_css_classes": "soha-voix"},
        "elements": [interieur],
        "isInner": False, "elType": "container",
    }


def poser_le_css(kit, journal, ecrire=True):
    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if MARQUEUR in css:
        journal.append("voix : le bloc v01 est déjà là")
        return
    st["custom_css"] = css + BLOC_CSS
    if ecrire:
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    journal.append("voix : bloc CSS v01 ajouté")


def appliquer(kit, ecrire=True):
    chemin = os.path.join(kit, PAGE)
    d = json.load(open(chemin, encoding="utf-8"))
    journal = []
    ids = [s.get("id") for s in d["content"]]

    if SECTION in ids:
        journal.append("voix : la section est déjà là — rien à reprendre")
    else:
        if APRES not in ids or AVANT not in ids:
            raise SystemExit("voix : les repères de position ont bougé (%s)" % ids)
        i = ids.index(AVANT)
        if ids.index(APRES) != i - 1:
            raise SystemExit("voix : « %s » ne précède plus « %s » — on n'écrit rien."
                             % (APRES, AVANT))
        d["content"].insert(i, batir())
        if ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
        journal.append("voix : section posée entre la bande des portes et « Le lieu »")
        journal.append("voix : citation de %s, reprise de %s" % (QUI, SOURCE))
    poser_le_css(kit, journal, ecrire)
    return journal


def main():
    ap = argparse.ArgumentParser(description="Une voix sur l'accueil.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    for l in appliquer(a.kit, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
