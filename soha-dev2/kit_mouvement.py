#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — le mouvement du kit : ce qui bouge, à quelle vitesse, et rien
d'autre.

Le constat, mesuré (département mouvement, 15 septembre 2026,
mesure_mouvement.py sur six pages à 1440 et 390 px)
-------------------------------------------------------------------------
Le site de référence est silencieux : 0 animation, 0 transform, 0 keyframe,
toutes les transitions rendues à 140 ms cubic-bezier(.22,.61,.36,1). Le
critère 8 tient à 2/2 — dans MA maquette. Trois choses disent que ce n'est pas
le cas chez Mala :

  1. Trois boutons « ← Revenir aux formations » (7389, 7390, 7392) portent
     `hover_animation: "grow"`. Elementor rend cette clé en
     `transform:scale(1.1)` sur .3s au survol — le zoom « e-commerce » que le
     canon interdit (soha-motion §3.1). Le générateur ignore la clé : la
     maquette ne le montre pas, WordPress le fait.
  2. Le widget HTML de l'horaire (7326) déclare `transition:background 140ms
     ease, color 140ms ease` : la bonne durée, le mauvais easing — 4 éléments
     rendus hors canon sur se-ressourcer.
  3. Le bloc `prefers-reduced-motion` GLOBAL (`*{…}`) n'existe que dans
     build_site.py : le custom_css du kit ne coupe que les boutons. Chez Mala,
     tout ce qu'Elementor anime de lui-même (menu, accordéon, `transition:all
     .3s` de ses boutons) ignore le réglage du visiteur. Et aucun jeton
     --mo-* n'est déclaré : chaque nouvelle règle réinvente sa durée.

Ce que le script fait
---------------------
  · vide toute clé d'animation Elementor non vide (hover_animation,
    _animation…) — à la source, pas par un CSS qui lutterait contre ;
  · corrige l'easing du widget HTML de l'horaire ;
  · ajoute au custom_css le bloc « le mouvement · v01 » : les trois jetons du
    canon, la liste de ce qui a le droit de bouger (couleurs, filets, opacité),
    le filet contre les animations de survol d'Elementor, et la coupure
    globale en reduced-motion — le contenu reste entièrement visible.

Ce qu'il refuse de faire
------------------------
  · ajouter un mouvement (fondu d'entrée, apparition au défilement, survol qui
    soulève) : le site n'en a aucun et c'est sa qualité ;
  · toucher à l'anneau de focus (kit_focus.py v03), aux couleurs de survol
    (kit_cyan.py), aux héros (kit_heros.py) ;
  · écrire quoi que ce soit si le bloc v01 est déjà là.

    python3 kit_mouvement.py --kit <dossier> [--lire]
"""

import argparse
import glob
import json
import os
import sys

MARQUEUR = "le mouvement · v01"
CLES_ANIM = ("hover_animation", "_animation", "_animation_mobile",
             "_animation_tablet", "animation", "button_hover_animation",
             "image_hover_animation", "hover_animation_type")

HORAIRE_AVANT = "transition:background 140ms ease,color 140ms ease"
HORAIRE_APRES = ("transition:background-color 140ms cubic-bezier(.22,.61,.36,1),"
                 "color 140ms cubic-bezier(.22,.61,.36,1)")

BLOC = """


/* ============================================================
   SOHA — le mouvement · v01 · 15 septembre 2026
   Mesure (six pages, 1440 et 390) : zero animation, zero transform,
   zero keyframe — le silence tient. Ce bloc ne l'ajoute pas, il le
   GARANTIT chez Mala : les jetons du canon, la coupure globale en
   reduced-motion (le kit ne coupait que les boutons, le `*` vivait
   dans le generateur — donc nulle part), et le filet contre ce
   qu'Elementor anime tout seul (transition:all .3s sur ses boutons,
   hover « grow » = scale(1.1)). Aucun contenu ne depend d'un
   mouvement pour etre lu.
   ============================================================ */
:root{--mo-fast:140ms;--mo-base:280ms;--mo-ease:cubic-bezier(.22,.61,.36,1)}
html{scroll-behavior:smooth}
/* ce qui a le droit de bouger : le fond, le texte, le filet, l'opacite.
   Mesure le 15 septembre : avec box-shadow dans la liste, la porte lisait
   l'anneau de focus a 0,00 pendant ses 140 ms de fondu — retire. */
.elementor-button,
.elementor-widget-form button[type="submit"],
.elementor-nav-menu a,
.elementor-nav-menu .elementor-item,
.elementor-nav-menu .elementor-item::before,
.elementor-nav-menu .elementor-item::after,
.elementor-widget-text-editor a,
.soha-lien-fleche,
.elementor-accordion .elementor-tab-title,
.elementor-field-group input,
.elementor-field-group textarea,
.elementor-field-group select{
  transition-property:background-color,color,border-color,text-decoration-color,opacity;
  /* ni outline ni box-shadow : l'anneau de focus apparait d'un coup (soha-motion §2) */
  transition-duration:var(--mo-fast);
  transition-timing-function:var(--mo-ease);
}
/* ce qui n'a pas le droit : la cle hover_animation est videe dans le kit
   (kit_mouvement.py) ; ceci est le filet si elle revient par l'editeur */
[class*="elementor-animation-"]:hover,
[class*="elementor-animation-"]:focus{transform:none}
/* une apparition d'entree ne conditionne jamais la lecture */
.elementor-invisible{visibility:visible}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{
    animation-duration:.001ms!important;
    animation-iteration-count:1!important;
    transition-duration:.001ms!important;
    scroll-behavior:auto!important;
  }
  html{scroll-behavior:auto}
}
"""


def vider_animations(o, chemin, journal):
    n = 0
    if isinstance(o, dict):
        s = o.get("settings")
        if isinstance(s, dict):
            for k in CLES_ANIM:
                v = s.get(k)
                if v not in (None, "", "none", []):
                    journal.append("%s · %s (%s) : %s %r → \"\"" % (
                        chemin, o.get("id"), o.get("widgetType") or o.get("elType"), k, v))
                    s[k] = ""
                    n += 1
        for v in o.values():
            n += vider_animations(v, chemin, journal)
    elif isinstance(o, list):
        for v in o:
            n += vider_animations(v, chemin, journal)
    return n


def corriger_horaire(o, chemin, journal):
    n = 0
    if isinstance(o, dict):
        s = o.get("settings")
        if isinstance(s, dict) and isinstance(s.get("html"), str) and HORAIRE_AVANT in s["html"]:
            s["html"] = s["html"].replace(HORAIRE_AVANT, HORAIRE_APRES)
            journal.append("%s · %s (html) : easing `ease` → canon" % (chemin, o.get("id")))
            n += 1
        for v in o.values():
            n += corriger_horaire(v, chemin, journal)
    elif isinstance(o, list):
        for v in o:
            n += corriger_horaire(v, chemin, journal)
    return n


def appliquer(kit, ecrire=True):
    journal = []
    fichiers = sorted(glob.glob(os.path.join(kit, "content", "**", "*.json"), recursive=True)
                      + glob.glob(os.path.join(kit, "templates", "*.json")))
    for f in fichiers:
        d = json.load(open(f, encoding="utf-8"))
        rel = os.path.relpath(f, kit)
        n = vider_animations(d, rel, journal) + corriger_horaire(d, rel, journal)
        if n and ecrire:
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if MARQUEUR in css:
        journal.append("mouvement : le bloc v01 est déjà là")
    else:
        st["custom_css"] = css + BLOC
        if ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        journal.append("mouvement : bloc v01 posé (%d caractères)" % len(BLOC))
    return journal


def main():
    ap = argparse.ArgumentParser(description="Le mouvement du kit, au canon et rien d'autre.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true", help="n'écrit rien, dit seulement ce qui changerait")
    a = ap.parse_args()
    for l in appliquer(a.kit, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
