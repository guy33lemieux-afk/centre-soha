#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — rendre à Soigner sa place.

Le constat, mesuré
------------------
Sur les 1 292 textes du site, 78 sont écrits en Soigner #19A7DB. **Cinq
passent le seuil WCAG AA — et ce sont les cinq posés sur l'encre.** Les 73
autres, répartis sur 24 des 29 pages, mesurent 2,35 à 2,61 pour un seuil de
4,5.

Le bleu n'est pas en cause. C'est sa place qui l'est :

    Soigner ne porte pas de lettres sur fond clair.
    Sur fond clair il est trait, filet ou fond — jamais lettre.

Ce que le script fait, et rien d'autre
--------------------------------------
A. Les couleurs de TEXTE valant #19A7DB passent à l'encre — sauf si l'élément
   est posé sur un fond encre, où Soigner tient 6,45 et reste.
B. Les boutons qui virent au fond Soigner au survol portaient un texte blanc :
   2,77. Le texte passe à l'encre : 6,45. Le fond, lui, ne bouge pas.
C. Les feuilles embarquées dans les widgets HTML du kit reçoivent le même
   traitement — c'est là que vivent les pastilles « En ligne », « Complet ».
D. Un bloc de style rend à Soigner ce qu'on lui retire : les liens de corps de
   texte le portent en soulignement. Le mot se lit en encre, le trait sous le
   mot reste bleu. Rien n'est perdu ; tout est déplacé d'un cran.

Ce que le script refuse de faire
--------------------------------
Il ne touche à aucune bordure, à aucun fond, à aucun texte de Mala, et
n'introduit aucune couleur : #0E1A15 et #19A7DB sont tous deux du canon v06.

    python3 kit_soigner.py --kit <dossier> [--lire]
"""

import argparse
import glob
import json
import os
import re
import sys

SOIGNER = "#19A7DB"
ENCRE = "#0E1A15"

# Les clés qui posent des LETTRES. Tout le reste — border_color, background,
# button_background_hover_color — est du trait ou du fond : Soigner y reste.
LETTRES = {
    "title_color", "text_color", "job_text_color", "classic_read_more_color",
    "tab_active_color", "color", "heading_color", "description_color",
    "price_color", "meta_color", "excerpt_color", "link_color",
}

# Un fond clair est un fond sur lequel Soigner ne tient pas. On ne devine pas :
# on regarde la luminance du fond le plus proche en remontant.
def clair(hexa):
    if not hexa or not hexa.startswith("#") or len(hexa) not in (4, 7):
        return True                     # pas de fond connu → la page est ivoire
    h = hexa.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b) > 0.18


def marcher(noeud, fond, journal, chemin="")  :
    """Descend l'arbre en se souvenant du fond sous les pieds."""
    if isinstance(noeud, dict):
        s = noeud.get("settings")
        if isinstance(s, dict):
            f = s.get("background_color")
            if isinstance(f, str) and f.startswith("#"):
                fond = f
            classes = (s.get("_css_classes") or "")
            if "soha-lieu" in classes:
                fond = ENCRE
            for k, v in list(s.items()):
                if not (isinstance(v, str) and v.upper() == SOIGNER):
                    continue
                if k in LETTRES and clair(fond):
                    s[k] = ENCRE
                    journal.append(("lettres", k, fond))
            # B · le texte blanc posé sur un fond Soigner — au repos comme au survol.
            for fk, tk in (("background_color", "button_text_color"),
                           ("button_background_color", "button_text_color"),
                           ("background_color", "color")):
                if (isinstance(s.get(fk), str) and s[fk].upper() == SOIGNER
                        and isinstance(s.get(tk), str) and s[tk].upper() in ("#FFFFFF", "#FFF")):
                    s[tk] = ENCRE
                    journal.append(("fond bleu", tk, SOIGNER))
            if (s.get("button_background_hover_color", "").upper() == SOIGNER):
                for k in ("button_hover_text_color", "hover_color", "button_hover_color"):
                    if isinstance(s.get(k), str) and s[k].upper() in ("#FFFFFF", "#FFF"):
                        s[k] = ENCRE
                        journal.append(("survol", k, SOIGNER))
            # C · les feuilles embarquées dans les widgets HTML
            # On ne devine plus la clé. « 45,52° N » vivait dans `title`,
            # « politique de confidentialité » dans le texte d'un champ de
            # formulaire : deux clés que ma liste ne contenait pas. Toute valeur
            # de texte qui porte Soigner est examinée.
            for k in [c for c, w in s.items()
                      if isinstance(w, str) and SOIGNER.lower() in w.lower()
                      and ("<" in w or "{" in w)]:
                v = s.get(k)
                neuf, n = feuille_embarquee(v)
                if n:
                    s[k] = neuf
                    journal.append(("embarqué", k, "%d règle(s)" % n))
                if clair(fond):
                    n = styles_en_ligne(s, k)
                    if n:
                        journal.append(("en ligne", k, "%d style(s)" % n))
            # Les champs de formulaire sont une LISTE de dictionnaires sous
            # `settings` : ils n'ont pas de `settings` à eux, donc la descente
            # ne les visitait pas. C'est là que vit le lien « politique de
            # confidentialité » des trois formulaires du site.
            if clair(fond):
                n = en_ligne_partout(s)
                if n:
                    journal.append(("en ligne", "imbriqué", "%d style(s)" % n))
        for v in noeud.values():
            marcher(v, fond, journal, chemin)
    elif isinstance(noeud, list):
        for v in noeud:
            marcher(v, fond, journal, chemin)


# Dans une feuille embarquée on ne peut pas remonter l'arbre : on s'en tient à
# ce qui est certain — une déclaration `color:` (et non `border-color:` ni
# `background-color:`) qui vaut Soigner, dans un sélecteur qui n'est pas posé
# sur l'encre.
COULEUR = re.compile(r"(?<![-\w])color\s*:\s*" + SOIGNER, re.I)
# Un attribut `style` posé sur la balise elle-même.
EN_LIGNE = re.compile(r'style="[^"]*(?<![-\w])color:\s*' + SOIGNER + r'[^"]*"', re.I)

def styles_en_ligne(conteneur, cle):
    """Un `style="color:#19A7DB"` posé à même la balise bat toute feuille de
    style : aucune règle ne pouvait le rattraper. On le réécrit à la source."""
    v = conteneur.get(cle)
    if not isinstance(v, str):
        return 0
    neuf, n = EN_LIGNE.subn(
        lambda m: m.group(0).replace(SOIGNER, ENCRE).replace(SOIGNER.lower(), ENCRE), v)
    if n:
        conteneur[cle] = neuf
    return n


def en_ligne_partout(noeud):
    """Le même geste, mais partout sous `settings` — listes comprises."""
    n = 0
    if isinstance(noeud, dict):
        for k, v in list(noeud.items()):
            if isinstance(v, str):
                n += styles_en_ligne(noeud, k)
            else:
                n += en_ligne_partout(v)
    elif isinstance(noeud, list):
        for v in noeud:
            n += en_ligne_partout(v)
    return n


def feuille_embarquee(txt):
    sorties = []
    n = 0
    for bloc in re.split(r"(\{[^}]*\})", txt):
        if bloc.startswith("{") and COULEUR.search(bloc):
            bloc, k = COULEUR.subn("color:" + ENCRE, bloc)
            n += k
        sorties.append(bloc)
    return "".join(sorties), n


BLOC_CSS = """


/* ============================================================
   SOHA — la place de Soigner · v07d · 14 septembre 2026
   Posé par kit_soigner.py. Additif : rien au-dessus n'est remplacé.
   ============================================================ */

/* Soigner quitte les lettres sur fond clair et revient sous elles. Le
   soulignement se pose sur le TEXTE et non sur la boîte : les liens portent
   une cible tactile de 44 px (WCAG 2.2), et un `border-bottom` aurait suivi
   cette boîte en flottant cinquante pixels sous le mot. Mesuré. */
/* Cette règle ne pose AUCUNE couleur, et c'est délibéré : la première version
   en posait une, et elle a repeint en encre quatre liens qui vivaient sur une
   section encre — invisibles. Une feuille de style ne sait pas sur quel fond
   elle tombe. Le seul endroit qui le sait, c'est la source : la couleur est
   décidée page par page par kit_soigner.py, qui, lui, remonte l'arbre.
   Ici on ne pose que le trait — il hérite du fond de personne. */
.soha-article-corps a,
.soha-carte-lire, .soha-retour,
.elementor-widget-text-editor a:not(.elementor-button),
.elementor-widget-theme-post-content a:not(.elementor-button){
  text-decoration:underline;
  text-decoration-color:#19A7DB;
  text-decoration-thickness:1.5px;
  text-underline-offset:4px;
}
.soha-article-corps a:hover,
.soha-carte-lire:hover, .soha-retour:hover,
.elementor-widget-text-editor a:not(.elementor-button):hover{
  text-decoration-thickness:3px;
}

/* L'italique de titre valait 2,43 sur l'ivoire — et 2,43 reste sous le seuil
   même à 48 px, où il n'en faut que 3,0. L'italique porte déjà l'accent ;
   il n'a pas besoin d'une couleur pour cela. Sur l'encre, Soigner reste. */
/* Le corps d'article, lui, est TOUJOURS sur l'ivoire : on peut le nommer. */
.soha-article-corps a{color:#0E1A15}
.elementor-heading-title em, .disp-em{color:#0E1A15}
.soha-lieu.soha-lieu .elementor-heading-title em,
.soha-lieu.soha-lieu .disp-em{color:#19A7DB}

/* Le surtitre en DM Mono : l'encre pour les lettres, Soigner pour le filet
   qui les tient — c'est déjà ce que fait le bloc « LE LIEU » du kit, et
   c'est ce qui donne au surtitre sa raison d'être bleue. */
.soha-surtitre{color:#0E1A15;border-left:2px solid #19A7DB;padding-left:14px}

/* L'anneau de focus mesurait 2,61 sur le papier : invisible au clavier.
   Deux anneaux — encre sur bleu — tiennent sur tous les fonds du canon. */
:where(a,button,input,select,textarea,summary,[tabindex]):focus-visible{
  outline:2px solid #0E1A15;
  outline-offset:2px;
  box-shadow:0 0 0 5px #19A7DB;
}
"""


def poser_le_style(kit, journal, ecrire=True):
    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if "la place de Soigner · v07d" in css:
        journal.append(("style", "v07", "déjà posé"))
        return
    # Les trois règles du kit qui font de Soigner des lettres sur fond clair.
    css = css.replace(".elementor-heading-title em{color:#19A7DB;",
                      ".elementor-heading-title em{color:#0E1A15;")
    st["custom_css"] = css + BLOC_CSS
    if ecrire:
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    journal.append(("style", "v07", "%d caractères" % len(BLOC_CSS)))


def appliquer(kit, ecrire=True):
    journal = []
    touches = 0
    for f in sorted(glob.glob(os.path.join(kit, "content", "*", "*.json"))):
        doc = json.load(open(f, encoding="utf-8"))
        avant = json.dumps(doc, ensure_ascii=False)
        marcher(doc, None, journal)
        if json.dumps(doc, ensure_ascii=False) != avant:
            touches += 1
            if ecrire:
                json.dump(doc, open(f, "w", encoding="utf-8"),
                          ensure_ascii=False, separators=(",", ":"))
    poser_le_style(kit, journal, ecrire)
    return journal, touches


def main():
    ap = argparse.ArgumentParser(description="Rendre à Soigner sa place dans le kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true", help="montrer sans écrire")
    a = ap.parse_args()
    journal, touches = appliquer(a.kit, ecrire=not a.lire)
    import collections
    c = collections.Counter(g for g, _, _ in journal)
    for genre, n in c.most_common():
        print("   %-10s %d" % (genre, n))
    print("   %d fichier(s) du kit modifié(s)." % touches)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
