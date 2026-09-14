#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — réparer l'anneau de focus que j'avais cru réparer.

Ce qui s'est passé
------------------
Ce matin, `kit_soigner.py` a posé dans le kit :

    :where(a,button,input,select,textarea,summary,[tabindex]):focus-visible
      {outline:2px solid #0E1A15; outline-offset:2px; box-shadow:0 0 0 5px #19A7DB}

et je l'ai annoncé fait. Trois sceptiques l'ont mesuré au clavier, séparément,
et sont arrivés au même résultat : **il ne rend rien.**

`:where()` vaut ZÉRO en spécificité — c'est tout son intérêt, et c'est ce qui
l'a tué. Le sélecteur pèse (0,1,0). Le bloc « finition revue departements v03 »
du 9 septembre, resté dans le même fichier, pèse (0,1,1) sur `a:focus-visible`,
(0,2,0) sur `.elementor-button:focus-visible`, (0,2,1) sur
`.elementor-nav-menu a:focus-visible`. L'ancien gagne, malgré sa position
antérieure.

Vérifié moi-même : 14 tabulations réelles sur l'accueil, **0 anneau encre,
14 anneaux Soigner** — c'est-à-dire 2,61:1, exactement le défaut que le
correctif devait retirer. Seuls `summary` et `[tabindex]`, absents de la liste
de septembre, obtenaient l'encre.

Le geste
--------
Deux règles de focus contradictoires dans une même feuille, c'est ça le
défaut. On n'en ajoute pas une troisième plus lourde : on retire celle de
septembre, et on écrit la nouvelle avec de VRAIS sélecteurs — pas de
`:where()`, pas de `!important`.

L'anneau : encre #0E1A15 sur papier = 16,84 · sur ivoire = 15,68 · sur encre,
le halo Soigner de 5 px prend le relais à 6,45. Les trois fonds du canon sont
couverts, très au-dessus des 3:1 exigés par WCAG 2.2 (1.4.11).

    python3 kit_focus.py --kit <dossier> [--lire]
"""

import argparse
import json
import os
import sys

MARQUEUR = "l'anneau de focus · v02"

# La règle de septembre, au caractère près. Si elle a bougé, on n'écrit rien
# plutôt que de deviner.
SEPTEMBRE = """/* a11y : focus clavier visible partout */
a:focus-visible,button:focus-visible,.elementor-button:focus-visible,
input:focus-visible,textarea:focus-visible,select:focus-visible,
.elementor-nav-menu a:focus-visible{
  outline:2px solid #19A7DB;outline-offset:2px;border-radius:2px;
}"""

REMPLACEE = """/* a11y : focus clavier visible partout — REMPLACEE le 14 septembre.
   Elle posait un anneau #19A7DB a 2,61:1 sur le papier, et elle battait en
   specificite le correctif du matin, ecrit en `:where()` qui ne pese rien.
   La regle unique est plus bas, bloc « l'anneau de focus · v02 ». */"""

# Le correctif du matin, inerte. On le retire en même temps.
MATIN = """/* L'anneau de focus mesurait 2,61 sur le papier : invisible au clavier.
   Deux anneaux — encre sur bleu — tiennent sur tous les fonds du canon. */
:where(a,button,input,select,textarea,summary,[tabindex]):focus-visible{
  outline:2px solid #0E1A15;
  outline-offset:2px;
  box-shadow:0 0 0 5px #19A7DB;
}"""

BLOC = """


/* ============================================================
   SOHA — l'anneau de focus · v02 · 14 septembre 2026
   Une seule regle, avec de VRAIS selecteurs. La version du matin
   etait ecrite en `:where()`, qui vaut zero en specificite : elle
   perdait contre le bloc de septembre reste dans le meme fichier,
   et 14 tabulations sur 14 gardaient l'anneau a 2,61:1.
   Mesure : encre sur papier 16,84 · sur ivoire 15,68 ; sur l'encre
   le halo Soigner de 5 px prend le relais a 6,45. WCAG 2.2 (1.4.11)
   exige 3:1 pour un indicateur non textuel.
   Le halo est en `box-shadow` et non en second `outline` : un
   element ne peut porter qu'un outline, et box-shadow n'occupe
   aucune place dans le flux — rien ne bouge au focus.
   ============================================================ */
a:focus-visible,
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
summary:focus-visible,
[tabindex]:focus-visible,
.elementor-button:focus-visible,
.elementor-nav-menu a:focus-visible,
.soha-carte a:focus-visible{
  outline:2px solid #0E1A15;
  outline-offset:2px;
  border-radius:2px;
  box-shadow:0 0 0 5px #19A7DB;
}
"""


def appliquer(kit, ecrire=True):
    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    journal = []

    if MARQUEUR in css:
        journal.append("focus : le bloc v02 est déjà là")
        return journal

    if SEPTEMBRE not in css:
        raise SystemExit("focus : la règle de septembre a changé de forme — "
                         "on n'écrit rien plutôt que de deviner.")
    css = css.replace(SEPTEMBRE, REMPLACEE)
    journal.append("focus : la règle de septembre (#19A7DB, 2,61) retirée")

    if MATIN in css:
        css = css.replace(MATIN, "")
        journal.append("focus : le `:where()` du matin retiré — il ne rendait rien")

    st["custom_css"] = css + BLOC
    if ecrire:
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    journal.append("focus : règle unique v02 posée (%d caractères)" % len(BLOC))
    return journal


def main():
    ap = argparse.ArgumentParser(description="L'anneau de focus, pour de vrai.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    for l in appliquer(a.kit, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
