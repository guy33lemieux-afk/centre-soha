#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la couture : que deux encres cessent de n'en faire qu'une.

Le fait, mesuré
---------------
Sur trois pages, une section de contenu en encre touche le pied en encre sans
un pixel de clair entre les deux. Les trois portent `#0E1A15` et le même
`padding 48/22/96/22` ; le pied `5fb6d311` porte 64/40, également en encre.

Résultat : une bande morte de 110,8 px, et une dalle continue de 1 387,5 px à
1440 de large — 2 115,9 px à 390. L'appel à l'action se lit comme une mention
de pied de page. Le changement de registre — le seul outil de matière fort du
site, celui qui fait tout l'effet de la section « Le lieu » — s'annule par
contact.

Le remède n'est pas d'éclaircir la section : ses widgets sont colorés pour
l'encre, on ferait tomber du texte ivoire sur de l'ivoire. C'est de rendre le
bord visible.

Trois arbitrages, et leurs raisons
----------------------------------
· Sur la SECTION, pas sur le pied. Même ligne de pixels à l'écran, mais trois
  pages au lieu de vingt-neuf : les 26 pages dont le pied est précédé d'un sol
  clair gardent un bord franc au lieu de recevoir une règle inutile.

· Par une CLASSE, pas par un identifiant Elementor. Aucun `.elementor-element-*`
  n'est visé dans le CSS de production du kit, et rien ne garantit que ces
  identifiants survivent à l'import. Les conteneurs racines lisent bien
  `_css_classes` (build_site.py:535) — c'est ce qui rend ce geste possible.

· Une classe NEUVE, et surtout pas `soha-pied` : poser `soha-pied` sur le
  conteneur du pied réveillerait du même coup une règle aujourd'hui morte
  (`.soha-pied .elementor-widget-text-editor a{min-height:44px}` sous 767 px).
  Un changement que personne n'a demandé ni mesuré.

La valeur
---------
`rgba(244,240,231,.18)` — reprise textuellement de la règle que kit_accueil.py
pose déjà sur les repères du « lieu ». Le custom_css du kit ne connaît que
trois alphas : .18, .72, .82. On n'en invente pas un quatrième.

Aplatie sur l'encre, la couture donne #37413B, soit 1,68:1 : filet décoratif,
hors WCAG 1.4.11 — elle ne porte aucune information qu'un texte ne porte déjà.
Le filet #E0D8CA à pleine force y serait à 12,61 : une ligne presque blanche,
refusée.

Si à l'œil elle ne se lit pas, l'escalade est .36 (#616761, 3,07:1) — mais .36
est un palier que le canon ne contient pas. Il devra être adopté explicitement
par Mala, pas glissé ici.

    python3 kit_couture.py --kit <dossier> [--lire]
"""

import argparse
import json
import os
import sys

CIBLES = {
    "content/page/7339.json": ["81f22c5"],    # prendre-soin   · « Tu ne sais pas vers qui aller ? »
    "content/page/7350.json": ["35f63c"],     # se-transformer
    "content/page/7326.json": ["4e9d5179"],   # se-ressourcer  · « Tu hésites encore ? »
}
CLASSE = "soha-couture"
MARQUEUR = "la couture du pied · v01"

BLOC = """


/* ============================================================
   SOHA — la couture du pied · v01 · 14 septembre 2026
   Trois pages posent une section encre au contact du pied encre :
   81f22c5 (7339), 35f63c (7350), 4e9d5179 (7326), toutes en
   48/22/96/22 sur #0E1A15, puis 5fb6d311 en 64/40, encre aussi.
   Mesure : 110,8 px de bande morte, dalle de 1 387,5 px a 1440
   et 2 115,9 px a 390 — les deux registres fusionnent.
   Un filet d'ivoire a 18 % — la valeur deja employee par
   `.soha-lieu .e-con.e-child > .e-con.e-child` — rend le raccord
   lisible. Aplatie sur l'encre : #37413B, 1,68:1. Filet decoratif,
   hors WCAG 1.4.11. Le filet #E0D8CA a pleine force y serait a
   12,61 : refuse. Aucun texte touche, aucun contraste modifie.
   Classe doublee pour la specificite, comme le bloc v06b.
   ============================================================ */
.soha-couture.soha-couture{border-bottom:1px solid rgba(244,240,231,.18)}
"""


def poser_les_classes(kit, journal, ecrire=True):
    for rel, ids in CIBLES.items():
        chemin = os.path.join(kit, rel)
        d = json.load(open(chemin, encoding="utf-8"))
        vus, poses = [], [0]

        def marche(o):
            if isinstance(o, dict):
                if o.get("id") in ids:
                    vus.append(o["id"])
                    s = o.setdefault("settings", {})
                    cls = (s.get("_css_classes") or "").split()
                    if CLASSE not in cls:
                        cls.append(CLASSE)
                        s["_css_classes"] = " ".join(cls)
                        poses[0] += 1
                for v in o.values():
                    marche(v)
            elif isinstance(o, list):
                for v in o:
                    marche(v)

        marche(d)
        manquants = set(ids) - set(vus)
        if manquants:
            raise SystemExit("couture : introuvable dans %s : %s" % (rel, manquants))
        if poses[0] and ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
        journal.append("couture : %s — %d posée(s), %d déjà là"
                       % (os.path.basename(chemin), poses[0], len(ids) - poses[0]))


def poser_le_css(kit, journal, ecrire=True):
    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if MARQUEUR in css:
        journal.append("couture : le bloc v01 est déjà là")
        return
    st["custom_css"] = css + BLOC
    if ecrire:
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    journal.append("couture : bloc v01 ajouté (%d caractères)" % len(BLOC))


def appliquer(kit, ecrire=True):
    journal = []
    poser_les_classes(kit, journal, ecrire)
    poser_le_css(kit, journal, ecrire)
    return journal


def main():
    ap = argparse.ArgumentParser(description="La couture du pied.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true", help="montrer sans écrire")
    a = ap.parse_args()
    for ligne in appliquer(a.kit, ecrire=not a.lire):
        print("   " + ligne)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
