#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — appliquer au kit la trame validée pour l'accueil.

La proposition a été rendue, regardée, approuvée. Ici elle entre dans le kit —
donc dans le **vrai** site, pas seulement dans le site HTML de référence.

Trois gestes, et rien d'autre
-----------------------------
A. LE HÉROS. La colonne photo portait `min-height: 82vh` : la rangée faisait
   donc 82 % de l'écran quel que soit le texte, et la colonne de gauche restait
   vide sur six cents pixels sous le bouton. La hauteur passe sur la RANGÉE,
   plus basse — les deux colonnes la partagent, et la photo cesse de commander.

B. LA BANDE DE TROIS. « Se transformer » et « Studio Podcast » vivaient dans une
   colonne de 46 % pendant qu'« Espaces professionnels » en occupait 50 % à lui
   seul : 552×306, 552×306, puis 600×719. Les trois cartes deviennent sœurs, à
   parts égales, avec le même cadrage carré et le lien au fond de chacune.

C. LE LIEU. La section passe sur fond encre. Ce n'est pas de la décoration :
   c'est le seul endroit de la page où le registre change — on ne parle plus de
   ce qu'on offre mais de l'endroit où ça se passe — et rien ne le signalait.

Ce que le script refuse de faire
--------------------------------
Il ne touche à aucun texte de Mala, n'ajoute ni ne retire aucune photo, et
n'invente aucune couleur : tout vient du canon v06 ou du kit lui-même. Les
couleurs de la bande encre sont posées par une règle de style unique plutôt que
sur quinze widgets — un widget oublié se verrait, une règle non.

    python3 kit_accueil.py --kit <dossier> [--lire]
"""

import argparse
import json
import os
import sys

PAGE = "7319.json"          # l'accueil

# ── les identifiants, relevés dans le kit et vérifiés avant d'écrire ─────────
HERO_RANGEE = "13fd70e4"
HERO_TEXTE = "1a600534"
HERO_PHOTO = "78dd0b"

BANDE = "51281e55"          # la rangée des trois portes
ENVELOPPE_46 = "63542338"   # la colonne de 46 % qui empilait deux cartes
CARTE_03 = "52c47f6a"
CARTE_04 = "5896aebc"
CARTE_05 = "5510aacb"

LIEU = "4ea69c6f"           # la section « Le lieu »

HAUTEUR_HERO = 62           # vh — mesurée pour que la photo cesse de commander
TITRE_05 = "6f899b31"       # le titre de la troisième carte, resté en 48 px
TAILLE_PORTE = 32           # px — la taille des deux autres titres de carte


def trouver(noeud, cible):
    if isinstance(noeud, dict):
        if noeud.get("id") == cible:
            return noeud
        for v in noeud.values():
            r = trouver(v, cible)
            if r is not None:
                return r
    elif isinstance(noeud, list):
        for v in noeud:
            r = trouver(v, cible)
            if r is not None:
                return r
    return None


def reglages(e):
    return e.setdefault("settings", {})


def largeur(e, pourcent):
    reglages(e)["width"] = {"unit": "%", "size": pourcent}


def classe(e, nom):
    s = reglages(e)
    deja = (s.get("_css_classes") or "").split()
    if nom not in deja:
        deja.append(nom)
    s["_css_classes"] = " ".join(deja)


# ── A · le héros ─────────────────────────────────────────────────────────────

def le_heros(doc, journal):
    rangee = trouver(doc, HERO_RANGEE)
    texte = trouver(doc, HERO_TEXTE)
    photo = trouver(doc, HERO_PHOTO)
    if not (rangee and texte and photo):
        raise SystemExit("Héros : un des trois conteneurs est introuvable.")

    avant = (reglages(photo).get("min_height") or {}).get("size")
    if avant is None:
        journal.append("héros : aucune hauteur imposée sur la photo — rien à reprendre")
        return

    # La hauteur quitte la colonne photo pour la rangée : les deux colonnes la
    # partagent, au lieu que l'une l'impose à l'autre.
    reglages(photo).pop("min_height", None)
    reglages(rangee)["min_height"] = {"unit": "vh", "size": HAUTEUR_HERO}
    largeur(texte, 48)
    largeur(photo, 48)
    journal.append("héros : hauteur %svh (photo) → %svh (rangée) · colonnes 40/56 → 48/48"
                   % (avant, HAUTEUR_HERO))


# ── B · la bande de trois ────────────────────────────────────────────────────

def la_bande(doc, journal):
    bande = trouver(doc, BANDE)
    if bande is None:
        raise SystemExit("La bande des trois portes est introuvable.")

    enfants = bande.get("elements") or []
    if len(enfants) == 3:
        journal.append("bande : déjà à trois colonnes — rien à reprendre")
        return
    if len(enfants) != 2:
        raise SystemExit("La bande a %d enfant(s) : forme inattendue, on n'écrit rien."
                         % len(enfants))

    enveloppe = trouver(bande, ENVELOPPE_46)
    c03, c04, c05 = (trouver(doc, CARTE_03), trouver(doc, CARTE_04), trouver(doc, CARTE_05))
    if not (enveloppe and c03 and c04 and c05):
        raise SystemExit("Bande : une des trois cartes est introuvable.")

    # Les deux cartes empilées sortent de leur enveloppe et deviennent sœurs
    # de la troisième. L'enveloppe, vidée, disparaît.
    bande["elements"] = [c03, c04, c05]
    for c in (c03, c04, c05):
        # Aucune largeur en pourcentage : 3 × 32,5 % plus deux gouttières de
        # 40 px dépassent 100 %, et la troisième carte passait à la ligne. La
        # classe `soha-porte` les fait se partager la place exactement, gouttières
        # déduites — c'est à `flex` de compter, pas à moi.
        reglages(c).pop("width", None)
        classe(c, "soha-porte")
    reglages(bande)["flex_align_items"] = "stretch"
    reglages(bande)["flex_wrap"] = "wrap"
    reglages(bande)["flex_direction_mobile"] = "column"

    # La troisième carte était la grande : son titre faisait 48 px quand les
    # deux autres en font 32. Devenue leur sœur, elle prend leur taille.
    titre = trouver(doc, TITRE_05)
    if titre is not None:
        t = reglages(titre).get("typography_font_size") or {}
        if t.get("size") != TAILLE_PORTE:
            avant = t.get("size")
            reglages(titre)["typography_font_size"] = {"unit": "px", "size": TAILLE_PORTE}
            journal.append("bande : titre de la 3e carte %s px → %s px" % (avant, TAILLE_PORTE))

    journal.append("bande : deux colonnes (46 %% + 50 %%) → trois colonnes égales")


# ── C · le lieu ──────────────────────────────────────────────────────────────

def le_lieu(doc, journal):
    section = trouver(doc, LIEU)
    if section is None:
        raise SystemExit("La section « Le lieu » est introuvable.")
    s = reglages(section)
    if s.get("background_color") == "#0E1A15":
        journal.append("le lieu : déjà sur encre — rien à reprendre")
        return
    avant = s.get("background_color")
    s["background_color"] = "#0E1A15"
    classe(section, "soha-lieu")
    journal.append("le lieu : fond %s → #0E1A15, et la classe qui inverse ses couleurs" % avant)


# ── le style qui accompagne les trois gestes ─────────────────────────────────

BLOC_CSS = """


/* ============================================================
   SOHA — la trame de l'accueil · v06b · 14 septembre 2026
   Deux classes, posées sur la page d'accueil par kit_accueil.py.
   Additif : aucune règle ci-dessus n'est remplacée.
   ============================================================ */

/* --- Les trois portes ------------------------------------------------------
   Les photos faisaient 552×306, 552×306 et 600×719 : la troisième valait les
   deux autres empilées, et son titre finissait seul tout en bas. Un cadrage
   carré commun leur rend la même hauteur — et le lien tombe au fond de chaque
   carte, sinon une description d'une ligne de plus le décale de vingt-cinq
   pixels. C'est exactement ce qui rend la grille du Journal irrégulière alors
   que ses vignettes, elles, sont parfaites. */
.soha-porte{display:flex;flex-direction:column;flex:1 1 200px;min-width:0;align-self:stretch}
/* En colonne, `flex:1 1 200px` se partagerait la HAUTEUR : on le relâche. */
@media (max-width:767px){.soha-porte{flex:1 1 auto}}
.soha-porte .elementor-widget-image img{aspect-ratio:1/1;object-fit:cover;width:100%;height:auto}
.soha-porte > .e-con:last-child{flex:1 1 auto;display:flex;flex-direction:column}
.soha-porte > .e-con:last-child > .elementor-widget:last-child{margin-top:auto}

/* --- Le lieu, sur encre ----------------------------------------------------
   Une règle plutôt que quinze réglages de widget : un widget oublié se
   verrait, une règle non.

   La classe est DOUBLÉE — `.soha-lieu.soha-lieu` — et ce n'est pas une
   coquetterie. Elementor écrit ses couleurs ainsi :

       .elementor-element-54f43e66 .elementor-heading-title{color:#0E1A15}

   soit deux classes. Une règle en `.soha-lieu h3` n'en compte qu'une : elle
   perd, et le titre reste encre SUR l'encre — invisible. C'est exactement ce
   que la porte du contraste a mesuré, à 1,00 sur 4,5. Répéter la classe porte
   la nôtre à trois : elle gagne, sans un seul `!important`.

   Et le bleu reste le bleu du canon : #19A7DB tient 6,45 sur l'encre, bien
   au-dessus des 4,5 exigés. Le #63C8E6 des premières esquisses est abandonné —
   il n'appartient à aucune des trois familles. */
.soha-lieu.soha-lieu,
.soha-lieu.soha-lieu h1,.soha-lieu.soha-lieu h2,.soha-lieu.soha-lieu h3,
.soha-lieu.soha-lieu h4,.soha-lieu.soha-lieu h5,
.soha-lieu.soha-lieu p,.soha-lieu.soha-lieu li,
.soha-lieu.soha-lieu .elementor-heading-title{color:#F4F0E7}
/* Le surtitre et le corps de texte restent en retrait, sans descendre sous le
   seuil : l'ivoire à 72 % tient encore 8,14 sur l'encre. */
.soha-lieu.soha-lieu h6,
.soha-lieu.soha-lieu h6.elementor-heading-title{color:rgba(244,240,231,.72)}
.soha-lieu.soha-lieu .elementor-widget-text-editor{color:rgba(244,240,231,.82)}
.soha-lieu.soha-lieu em,.soha-lieu.soha-lieu .disp-em{color:#19A7DB}
.soha-lieu.soha-lieu a:not(.elementor-button){color:#19A7DB}
/* Le bouton portait un texte encre et une bordure bleue : sur l'encre, le texte
   disparaissait purement et simplement (1,00). */
.soha-lieu.soha-lieu .elementor-button{color:#F4F0E7;border-color:#F4F0E7;background-color:transparent}
.soha-lieu.soha-lieu .elementor-button .elementor-button-text{color:inherit}
.soha-lieu.soha-lieu .elementor-button:hover{background-color:#F4F0E7;color:#0E1A15;border-color:#F4F0E7}
.soha-lieu.soha-lieu .elementor-button:hover .elementor-button-text{color:#0E1A15}
/* Les quatre repères portaient chacun le fond ivoire de la page : sur encre,
   ils redeviennent des renseignements posés sur le fond, séparés par un filet. */
.soha-lieu .e-con[style],.soha-lieu .e-con{background-color:transparent !important}
.soha-lieu .e-con.e-child > .e-con.e-child{border-top:1px solid rgba(244,240,231,.18)}
"""


def poser_le_style(kit, journal, ecrire=True):
    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if "la trame de l'accueil · v06b" in css:
        journal.append("style : le bloc v06 est déjà là")
        return
    st["custom_css"] = css + BLOC_CSS
    if ecrire:
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    journal.append("style : bloc v06 ajouté (%d caractères)" % len(BLOC_CSS))


def appliquer(kit, ecrire=True):
    chemin = os.path.join(kit, "content/page", PAGE)
    doc = json.load(open(chemin, encoding="utf-8"))
    journal = []

    le_heros(doc, journal)
    la_bande(doc, journal)
    le_lieu(doc, journal)

    if ecrire:
        json.dump(doc, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    poser_le_style(kit, journal, ecrire)
    return journal


def main():
    ap = argparse.ArgumentParser(description="La trame de l'accueil, appliquée au kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true", help="montrer sans écrire")
    a = ap.parse_args()
    for ligne in appliquer(a.kit, ecrire=not a.lire):
        print("   " + ligne)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
