#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — branche le CRM React sur WordPress.

Le CRM v02 de Mala enregistre à travers `window.storage`, un objet que le
navigateur ne fournit pas : ses écritures partaient dans le vide, sans erreur.
Plutôt que de réécrire ses 897 lignes, cette extension **fournit** cet objet —
adossé à la base de données de WordPress. Son interface reste la sienne, au
caractère près ; c'est le sol sous ses pieds qui change.

Ce script prend son fichier `.jsx` tel quel et fabrique l'extension :

  1. remplace l'import de React par `wp.element` (React est déjà dans WordPress) ;
  2. retire l'appel à Google Fonts du bloc de style (les polices sont servies
     par l'extension elle-même — exigence Loi 25) ;
  3. **cloisonne le CSS** sous `#soha-crm-racine` : ses 124 classes nues, dont
     `.card` et `.badge`, se cogneraient sinon avec l'administration WordPress,
     dans les deux sens ;
  4. compile le JSX avec esbuild ;
  5. pose par-dessus le contenu de `crm-modele/` — le PHP de l'extension et
     l'adaptateur de stockage, qui vivent dans le dépôt et non ici.

Tout ce qui est écrit à la main est dans `crm-modele/` ; tout ce qui est dans le
dossier de sortie est jetable et se refabrique. C'est la leçon d'une
reconstruction qui avait emporté le PHP avec elle.

Usage :
    python3 build_crm.py --source <fichier .jsx> --polices <dossier woff2> \\
                         --sortie <dossier de l'extension>
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

RACINE = "#soha-crm-racine"
MODELE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crm-modele")


# --------------------------------------------------------------------------
#  1 · Cloisonner le CSS
# --------------------------------------------------------------------------
def cloisonner(css, racine=RACINE):
    """Préfixe chaque sélecteur par la racine, sans toucher aux at-règles.

    Écrit à la main plutôt qu'avec une bibliothèque : le CSS à traiter est
    connu — 12 Ko, deux sortes d'at-règles (`@import`, `@media`), aucun
    commentaire — et une dépendance de plus pour ça ne se justifie pas.

    Le découpage se fait sur l'accolade ouvrante : tout ce qui précède est le
    préambule. S'il commence par `@`, c'est une at-règle et on le garde mot pour
    mot ; sinon ce sont des sélecteurs à préfixer. La première version testait
    `@` à la position exacte du curseur, où il n'y a en pratique qu'un saut de
    ligne et deux espaces : le bloc `@media` passait alors pour un sélecteur et
    devenait `#soha-crm-racine @media (max-width:860px)`, c'est-à-dire rien.
    Toute la mise en page pour petits écrans était morte, en silence.
    """
    # Les at-règles qui contiennent des règles entières : on entre dedans.
    # Les autres (`@font-face`, `@keyframes`…) gardent leur intérieur tel quel,
    # où `from` et `to` ne sont pas des sélecteurs à préfixer.
    groupes = ("@media", "@supports", "@container", "@layer", "@scope")

    sortie = []
    i = 0
    n = len(css)
    while i < n:
        j = css.find("{", i)
        if j == -1:
            sortie.append(css[i:])
            break

        preambule = css[i:j]
        nu = preambule.strip()

        # une at-règle sans bloc, terminée par `;` : @import, @charset…
        if nu.startswith("@"):
            point = css.find(";", i)
            if point != -1 and point < j:
                sortie.append(css[i:point + 1])
                i = point + 1
                continue

        fin = _accolade_fermante(css, j)
        corps = css[j + 1:fin]

        if nu.startswith("@"):
            interieur = cloisonner(corps, racine) if nu.startswith(groupes) else corps
            sortie.append(preambule + "{" + interieur + "}")
        else:
            sortie.append(_prefixer(preambule, racine) + "{" + corps + "}")
        i = fin + 1
    return "".join(sortie)


def _accolade_fermante(s, ouverture):
    """L'accolade qui ferme celle ouverte en `ouverture`, imbrications comprises."""
    profondeur = 0
    for k in range(ouverture, len(s)):
        if s[k] == "{":
            profondeur += 1
        elif s[k] == "}":
            profondeur -= 1
            if profondeur == 0:
                return k
    return len(s) - 1


def _prefixer(selecteurs, racine):
    """`.card, .badge` devient `RACINE .card, RACINE .badge`.

    `html`, `body` et `:root` ne sont pas préfixés mais remplacés : dans l'écran
    d'administration, c'est la racine du CRM qui tient lieu de document, et c'est
    là que doivent atterrir ses variables de couleur.
    """
    morceaux = []
    for sel in selecteurs.split(","):
        nu = sel.strip()
        if not nu:
            continue
        if nu.startswith(racine):
            morceaux.append(nu)
        elif nu in ("html", "body", ":root"):
            morceaux.append(racine)
        else:
            morceaux.append("%s %s" % (racine, nu))
    return ("\n" + ",".join(morceaux)) if morceaux else selecteurs


# --------------------------------------------------------------------------
#  2 · Préparer la source
# --------------------------------------------------------------------------
def preparer(jsx):
    rapport = {}

    # React vient de WordPress (wp-element), pas d'un paquet npm
    avant = jsx
    jsx = re.sub(r'^\s*import\s+React\s*,?\s*\{([^}]*)\}\s*from\s*"react";?\s*$',
                 lambda m: ("const React = window.wp.element;\n"
                            "const { %s } = window.wp.element;" % m.group(1).strip()),
                 jsx, count=1, flags=re.M)
    rapport["import React remplacé"] = jsx != avant

    # le bloc de style : on le trouve, on le nettoie, on le cloisonne
    m = re.search(r"(function Style\(\)\s*\{[^`]*`)(.*?)(`[^`]*\})", jsx, re.S)
    if not m:
        raise SystemExit("Bloc <Style/> introuvable — la source a changé de forme.")
    css = m.group(2)

    avant_css = css
    css = re.sub(r"@import\s+url\([^)]*\)\s*;?", "", css)
    rapport["appels à Google Fonts retirés"] = len(re.findall(r"@import", avant_css))

    # 100vh vaut pour une page entière, pas pour un écran d'administration
    css = css.replace("min-height:100vh", "min-height:calc(100vh - 32px)")


    css = cloisonner(css)
    verifier_le_cloisonnement(css)
    rapport["sélecteurs cloisonnés"] = css.count(RACINE)
    rapport["at-règles préservées"] = len(re.findall(r"@media|@supports", css))

    # Le recollage se fait avec les positions mesurées sur le JSX d'origine :
    # toute autre retouche du texte doit donc venir après, jamais avant.
    jsx = jsx[:m.start(2)] + css + jsx[m.end(2):]

    jsx, faites = retoucher(jsx)
    rapport["retouches de contenu"] = len(faites)
    return jsx, rapport


def verifier_le_cloisonnement(css):
    """Le garde-fou de la panne découverte au banc d'essai.

    Une at-règle préfixée ne lève aucune erreur : le navigateur jette la règle
    et personne ne le voit. C'est exactement ce qui est arrivé — toute la mise
    en page pour petits écrans avait disparu en silence. On refuse donc de
    fabriquer une extension où `RACINE @media` apparaît, et on exige que chaque
    `@media` contienne encore des sélecteurs cloisonnés.
    """
    fautes = re.findall(re.escape(RACINE) + r"\s*@", css)
    if fautes:
        raise SystemExit("Cloisonnement fautif : %d at-règle(s) préfixée(s)." % len(fautes))

    for bloc in re.finditer(r"@media[^{]*", css):
        ouverture = bloc.end()
        if ouverture >= len(css) or css[ouverture] != "{":
            continue
        corps = css[ouverture + 1:_accolade_fermante(css, ouverture)]
        if RACINE not in corps:
            raise SystemExit("Une @media ne contient aucun sélecteur cloisonné : %s"
                             % bloc.group(0).strip())


RETOUCHES = [
    (
        "Données gardées dans ton navigateur.",
        "Données gardées dans la base du site, sauvegardées avec elle.",
        "C'était vrai du prototype — et c'était le défaut lui-même. Une "
        "interface qui dit faux sur l'endroit où dorment les noms de ses "
        "membres n'est pas un détail de formulation.",
    ),
    (
        'const ESPACES = ["Grande salle", "Studio", "Petite salle"];',
        'const ESPACES = ["Studio", "Espace SÖHA", "Salle 4", "Salles 1·2·3"];',
        "Le 961 n'a pas de « Grande salle » ni de « Petite salle ». Le site, "
        "l'estimateur et le formulaire de réservation nomment quatre espaces ; "
        "le CRM en nommait trois autres. Deux vocabulaires pour un même lieu, "
        "c'est une réservation mal saisie par mois et un revenu qu'on ne sait "
        "plus attribuer.",
    ),
    (
        'const RECURRENCES = ["Ponctuel", "Hebdomadaire", "Mensuel"];',
        'const RECURRENCES = ["Ponctuel", "Récurrent", "Hebdomadaire", "Mensuel"];',
        "Le formulaire propose « Ponctuel » ou « Récurrent (résident·e) ». "
        "Sans « Récurrent » dans le CRM, il faudrait deviner entre "
        "hebdomadaire et mensuel au moment de verser la demande — et deviner, "
        "ici, c'est inventer. La valeur passe telle quelle ; Mala précise "
        "ensuite si elle le sait.",
    ),
]


def retoucher(jsx):
    """Applique les retouches de contenu, chacune exigée et vérifiée.

    Le JSX d'origine n'est jamais modifié sur le disque : il voyage intact dans
    `source/`. Ces retouches-ci sont faites à la fabrication, et si l'une d'elles
    ne trouve plus sa cible — parce que Mala aura édité sa source — la
    fabrication s'arrête au lieu de livrer une extension à moitié corrigée.
    """
    faites = []
    for motif, remplacement, _raison in RETOUCHES:
        n = jsx.count(motif)
        if n != 1:
            raise SystemExit(
                "Retouche introuvable ou ambiguë (%d occurrence(s)) : %s"
                % (n, motif[:60])
            )
        jsx = jsx.replace(motif, remplacement)
        faites.append(motif[:34])
    return jsx, faites


ENTREE = """import App from "./crm-source.jsx";

const { createElement, createRoot, render } = window.wp.element;

function demarrer() {
  const noeud = document.getElementById("soha-crm-racine");
  if (!noeud) return;
  if (typeof createRoot === "function") {
    createRoot(noeud).render(createElement(App));
  } else {
    render(createElement(App), noeud);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", demarrer);
} else {
  demarrer();
}
"""


def construire(source, polices, sortie, esbuild, modele=MODELE):
    jsx = open(source, encoding="utf-8").read()
    prepare, rapport = preparer(jsx)

    travail = os.path.join(sortie, "_travail")
    assets = os.path.join(sortie, "assets")
    for d in (travail, assets, os.path.join(sortie, "source")):
        os.makedirs(d, exist_ok=True)

    open(os.path.join(travail, "crm-source.jsx"), "w", encoding="utf-8").write(prepare)
    open(os.path.join(travail, "entree.jsx"), "w", encoding="utf-8").write(ENTREE)
    # Le JSX d'origine voyage avec l'extension, sous un nom lisible : c'est la
    # pièce que Mala reconnaît, et la preuve qu'elle n'a pas été retouchée.
    shutil.copy2(source, os.path.join(sortie, "source", "crm-interface-origine.jsx"))

    cible = os.path.join(assets, "crm.js")
    cmd = [esbuild, os.path.join(travail, "entree.jsx"),
           "--bundle", "--format=iife", "--target=es2019",
           "--loader:.jsx=jsx",
           "--jsx-factory=React.createElement",
           "--jsx-fragment=React.Fragment",
           "--outfile=" + cible]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise SystemExit("esbuild a échoué.")

    if polices and os.path.isdir(polices):
        cible_pol = os.path.join(assets, "polices")
        os.makedirs(cible_pol, exist_ok=True)
        familles = {"schibsted-grotesk": "Schibsted Grotesk",
                    "fraunces": "Fraunces", "dm-mono": "DM Mono"}
        faces = []
        for f in sorted(os.listdir(polices)):
            if not f.endswith(".woff2"):
                continue
            shutil.copy2(os.path.join(polices, f), os.path.join(cible_pol, f))
            fam = next((v for k, v in familles.items() if f.startswith(k)), None)
            if not fam:
                continue
            m = re.search(r"-(\d{3})\.woff2$", f)
            faces.append('@font-face{font-family:"%s";font-style:%s;font-weight:%s;'
                         'font-display:swap;src:url("polices/%s") format("woff2")}'
                         % (fam, "italic" if "italic" in f else "normal",
                            m.group(1) if m else "400", f))
        open(os.path.join(assets, "polices.css"), "w", encoding="utf-8").write(
            "/* Les trois familles du canon, servies par l'extension.\n"
            "   Jamais Google : l'adresse IP ne part chez personne. */\n"
            + "\n".join(faces) + "\n")
        rapport["polices embarquées"] = len(faces)

    shutil.rmtree(travail)
    rapport["crm.js"] = "%.0f Ko" % (os.path.getsize(cible) / 1024)

    # Le modèle vient en dernier : ce qui est écrit à la main ne se fait jamais
    # écraser par ce qui est fabriqué.
    rapport["fichiers du modèle"] = copier_modele(modele, sortie)
    return rapport


def copier_modele(modele, sortie):
    """Recopie `crm-modele/` dans le dossier de sortie, en préservant l'arbre."""
    if not os.path.isdir(modele):
        raise SystemExit("Modèle introuvable : %s" % modele)
    n = 0
    for racine, _, fichiers in os.walk(modele):
        rel = os.path.relpath(racine, modele)
        dest = sortie if rel == "." else os.path.join(sortie, rel)
        os.makedirs(dest, exist_ok=True)
        for f in fichiers:
            shutil.copy2(os.path.join(racine, f), os.path.join(dest, f))
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="Fabrique l'extension CRM du Centre Soha.")
    ap.add_argument("--source", required=True, help="le fichier .jsx du CRM")
    ap.add_argument("--polices", default=None, help="dossier de .woff2")
    ap.add_argument("--sortie", required=True, help="dossier de l'extension")
    ap.add_argument("--esbuild", default="esbuild", help="chemin d'esbuild")
    ap.add_argument("--modele", default=MODELE, help="dossier du modèle de l'extension")
    a = ap.parse_args()
    rapport = construire(a.source, a.polices, a.sortie, a.esbuild, a.modele)
    print("Extension fabriquée dans « %s »" % a.sortie)
    for k, v in rapport.items():
        print("   %-32s %s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
