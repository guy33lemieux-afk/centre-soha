#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — quarante cibles deviennent des cibles sans bouger d'un pixel.

Le constat (département mobile, 15 septembre, six pages, quatre largeurs)
-------------------------------------------------------------------------
Quarante liens font moins de 44 px de haut : les liens du menu, les liens-flèche
« Voir la semaine → » dans le texte courant, les titres et « Lire l'article »
des cartes du Journal, les liens du pied de page. WCAG 2.5.8 demande 24 px au
minimum ; le canon Soha demande 44.

Ce que le script fait
---------------------
Une zone tactile de 44 px par PADDING + MARGE NÉGATIVE : la page ne grandit pas
d'un pixel, le soulignement reste collé au texte, seule la zone cliquable
s'étend. Rien d'autre.

    python3 kit_cibles.py --kit <dossier>
"""
import argparse, json, os
DEBUT = "/* ==== soha-cibles début ==== */"; FIN = "/* ==== soha-cibles fin ==== */"
BLOC = DEBUT + """
/* ---- cibles tactiles · v01 : 44 px sans bouger la page ---- */
.elementor-nav-menu a{display:inline-flex;align-items:center;min-height:44px}
.elementor-widget-text-editor p > a:only-child{display:inline-block;padding-top:24px;margin-top:-24px}
.soha-carte-titre a,.elementor-post__title a{display:inline-block;padding:10px 0;margin:-10px 0}
.soha-carte-lire,.elementor-post__read-more,.soha-retour{display:inline-block;padding:12px 0;margin:-12px 0}
.soha-pied a:not(.elementor-button){display:inline-block;padding:11px 0;margin:-11px 0}
.soha-ariane a{display:inline-block;padding:12px 0;margin:-12px 0}
""" + FIN + "\n"
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--kit", required=True); a = ap.parse_args()
    p = os.path.join(a.kit, "site-settings.json"); d = json.load(open(p, encoding="utf-8"))
    st = d.setdefault("settings", {}); css = st.get("custom_css", "")
    if DEBUT in css: css = css[:css.index(DEBUT)] + css[css.index(FIN) + len(FIN):]
    st["custom_css"] = css + BLOC
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("  cibles : bloc v01 posé (%d caractères)" % len(BLOC))
if __name__ == "__main__": main()
