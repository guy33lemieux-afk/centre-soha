#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — le fil d'Ariane : un fil, pas des miettes séparées.

Le constat
----------
Trois pages sur seize portent un fil d'Ariane, et sur ces trois-là il est fait
de widgets text-editor SÉPARÉS : « Accueil », puis « › », puis le titre — trois
blocs empilés verticalement, aucun `<a>`, donc du texte gris qui ressemble à un
chemin sans en être un. On ne peut ni cliquer, ni revenir.

Le geste
--------
Les widgets fusionnent en UN seul, avec de vrais liens et la page courante
marquée `aria-current="page"` — ce qui la sort de l'ordre de tabulation sans
la cacher au lecteur d'écran. Le `›` devient `aria-hidden` : une machine qui
lit « Accueil chevron Première visite » perd son temps.

Ce que le script ne fait PAS
----------------------------
Il n'ajoute pas de fil aux treize pages qui n'en ont pas. Décider que
« Introduction au Dialogue Authentique » est sous « Se transformer » est une
décision d'architecture, pas de code — et sur la moitié des pages elle n'est
pas évidente. Le JSON-LD `BreadcrumbList`, lui, se pose côté générateur, à
partir du fil réellement présent : pas de données structurées qui décrivent une
hiérarchie que la page n'affiche pas.

    python3 kit_ariane.py --kit <dossier> [--lire]
"""

import argparse
import json
import os
import sys

# Relevé dans le kit, pas deviné : les identifiants des widgets à fusionner,
# dans l'ordre du fil, et l'URL de chaque maillon cliquable.
FILS = {
    "7385": {"parent": "732c92e5",
             "maillons": [("53347d92", "Accueil", "/dev/"),
                          ("4c3cedf7", "›", None),
                          ("19167c38", "Première visite", "")]},
    "7386": {"parent": "25f34012",
             "maillons": [("17b712ea", "Accueil", "/dev/"),
                          ("155cae7d", "›", None),
                          ("5f05a90a", "Politique de confidentialité", "")]},
    "7387": {"parent": "5caefcfa",
             "maillons": [("2243bca9", "Accueil", "/dev/"),
                          ("3d47667f", "›", None),
                          ("303c3f83", "Se transformer", "/dev/se-transformer/"),
                          ("39594920", "›", None),
                          ("16f711ae", "Introduction au Dialogue Authentique", "")]},
}

MARQUEUR = "le fil d'Ariane · v01"

BLOC_CSS = """


/* ============================================================
   SOHA — le fil d'Ariane · v01 · 15 septembre 2026
   Il etait fait de widgets separes, empiles verticalement et
   sans un seul <a> : un chemin qui n'en etait pas un.
   Un seul widget, de vrais liens, la page courante marquee.
   Les liens heritent du soulignement Soigner pose par le bloc
   v07 : rien de neuf a declarer ici.
   ============================================================ */
.soha-ariane{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.soha-ariane [aria-current="page"]{color:#3F4A45}
.soha-ariane .soha-ariane-sep{color:#5A6460}
"""


def html_du_fil(maillons):
    bouts = []
    for _id, texte, url in maillons:
        t = texte.replace("&", "&amp;").replace("<", "&lt;")
        if url is None:
            bouts.append('<span class="soha-ariane-sep" aria-hidden="true">%s</span>' % t)
        elif url == "":
            bouts.append('<span aria-current="page">%s</span>' % t)
        else:
            bouts.append('<a href="%s">%s</a>' % (url, t))
    return ('<nav class="soha-ariane" aria-label="Fil d\'Ariane">%s</nav>'
            % "".join(bouts))


def appliquer(kit, ecrire=True):
    journal = []
    for pid, fil in sorted(FILS.items()):
        chemin = os.path.join(kit, "content", "page", "%s.json" % pid)
        d = json.load(open(chemin, encoding="utf-8"))
        garder = fil["maillons"][0][0]
        a_retirer = {m[0] for m in fil["maillons"][1:]}

        etat = {"vu": 0, "retires": 0}

        def marche(o):
            if isinstance(o, dict):
                enfants = o.get("elements")
                if isinstance(enfants, list) and enfants:
                    neufs = []
                    for e in enfants:
                        i = e.get("id") if isinstance(e, dict) else None
                        if i == garder:
                            s = e.setdefault("settings", {})
                            if "soha-ariane" in (s.get("editor") or ""):
                                etat["vu"] = -1      # déjà fusionné
                            else:
                                s["editor"] = html_du_fil(fil["maillons"])
                                s["_css_classes"] = " ".join(
                                    sorted(set((s.get("_css_classes") or "").split())
                                           | {"soha-ariane-hote"}))
                                etat["vu"] = 1
                            neufs.append(e)
                        elif i in a_retirer:
                            etat["retires"] += 1
                        else:
                            neufs.append(e)
                    o["elements"] = neufs
                for v in o.values():
                    marche(v)
            elif isinstance(o, list):
                for v in o:
                    marche(v)

        marche(d)
        if etat["vu"] == -1:
            journal.append("ariane : %s déjà fusionné" % pid)
            continue
        if etat["vu"] != 1:
            raise SystemExit("ariane : le maillon %s est introuvable dans %s"
                             % (garder, pid))
        if ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
        journal.append("ariane : %s — %d widget(s) fusionné(s) en un fil cliquable"
                       % (pid, etat["retires"] + 1))

    chemin = os.path.join(kit, "site-settings.json")
    d = json.load(open(chemin, encoding="utf-8"))
    st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if MARQUEUR in css:
        journal.append("ariane : le bloc v01 est déjà là")
    else:
        st["custom_css"] = css + BLOC_CSS
        if ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
        journal.append("ariane : bloc CSS v01 ajouté")
    return journal


def main():
    ap = argparse.ArgumentParser(description="Le fil d'Ariane, cliquable.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    for l in appliquer(a.kit, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
