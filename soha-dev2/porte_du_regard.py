#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la porte du regard : on ouvre chaque page, pour de vrai.

Écrit après une leçon payée deux fois. Le générateur savait dire « 74 images
copiées, aucune manquante » — et c'était vrai : elles étaient bien copiées. Mais
les neuf images de fond du site, dont quatre hero de page, ne s'affichaient pas.
Une `url()` dans une feuille de style se résout par rapport à la feuille, pas à
la page : `assets/soha.css` cherchait `assets/medias/…` et ne trouvait rien.
Aucune erreur nulle part. Un fond qui manque, ça ressemble à un fond qui n'existe
pas.

Compter ce qu'on écrit ne prouve rien sur ce qui s'affiche. Cette porte-ci
n'ouvre aucun fichier : elle sert le site, l'ouvre dans un navigateur, et note
tout ce que le navigateur n'a pas réussi à charger.

Ce qu'elle regarde, sur chaque page :
  · toute ressource qui répond 400 ou plus — image, police, script, feuille ;
  · toute requête vers l'extérieur (le site ne doit en faire aucune) ;
  · toute erreur JavaScript ;
  · tout débordement horizontal, à quatre largeurs.

Usage :
    python3 porte_du_regard.py --site <dossier> [--chromium <chemin>]
"""

import argparse
import functools
import http.server
import os
import sys
import threading
import time

LARGEURS = (1440, 1024, 768, 390)
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


class Muet(http.server.SimpleHTTPRequestHandler):
    """Le serveur d'essai, sans journal : c'est le navigateur qu'on écoute."""

    def log_message(self, *a):
        pass


def servir(dossier, port):
    gestionnaire = functools.partial(Muet, directory=dossier)
    serveur = http.server.ThreadingHTTPServer(("127.0.0.1", port), gestionnaire)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    time.sleep(0.5)
    return serveur


def regarder(site, chromium, port=8760):
    from playwright.sync_api import sync_playwright

    pages = sorted(f for f in os.listdir(site) if f.endswith(".html"))
    if not pages:
        raise SystemExit("Aucune page dans %s" % site)

    base = "http://127.0.0.1:%d" % port
    serveur = servir(site, port)
    fautes = []

    try:
        with sync_playwright() as p:
            nav = p.chromium.launch(executable_path=chromium)
            ctx = nav.new_context(viewport={"width": LARGEURS[0], "height": 900})
            for nom in pages:
                page = ctx.new_page()
                manquants, dehors, erreurs = [], [], []
                liens_absolus, liens_morts = [], []

                page.on("response", lambda r: manquants.append("%d %s" % (r.status, r.url))
                        if r.status >= 400 and "favicon" not in r.url else None)
                page.on("request", lambda r: dehors.append(r.url)
                        if not r.url.startswith(base) and not r.url.startswith("data:") else None)
                page.on("pageerror", lambda e: erreurs.append(str(e)))

                page.goto("%s/%s" % (base, nom), wait_until="networkidle")
                page.wait_for_timeout(300)

                deborde = []
                for l in LARGEURS:
                    page.set_viewport_size({"width": l, "height": 900})
                    page.wait_for_timeout(180)
                    m = page.evaluate("() => ({doc: document.documentElement.scrollWidth,"
                                      " vue: window.innerWidth})")
                    if m["doc"] > m["vue"] + 1:
                        deborde.append("%dpx (doc %dpx)" % (l, m["doc"]))

                # Les liens : le navigateur les affiche, il ne les suit pas.
                #
                # C'est le trou par lequel quatre cent vingt liens absolus sont
                # passés. Le jour où le kit est devenu « /dev » et que la
                # traduction cherchait encore « /dev2 », chaque adresse interne
                # est sortie telle quelle. Rien ne manquait, rien n'échouait,
                # aucune image n'était absente — seulement, hors de
                # centresoha.com, plus un seul de ces liens ne menait quelque
                # part. Un lien mort ne se plaint jamais : il faut aller le
                # chercher.
                liens = page.eval_on_selector_all(
                    "a[href]", "els => els.map(e => e.getAttribute('href'))")
                for h in liens:
                    h = (h or "").strip()
                    if not h or h.startswith(("mailto:", "tel:", "#",
                                              "http://", "https://")):
                        continue
                    if h.startswith("/"):
                        liens_absolus.append(h)
                        continue
                    cible = h.split("#")[0].split("?")[0]
                    if cible and not os.path.exists(os.path.join(site, cible)):
                        liens_morts.append(h)

                for quoi, liste in (("ressource introuvable", manquants),
                                    ("appel externe", dehors),
                                    ("erreur JavaScript", erreurs),
                                    ("débordement horizontal", deborde),
                                    ("lien absolu (mort hors du serveur)", sorted(set(liens_absolus))),
                                    ("lien vers un fichier absent", sorted(set(liens_morts)))):
                    for x in liste:
                        fautes.append((nom, quoi, x))

                page.close()
            nav.close()
    finally:
        serveur.shutdown()

    return pages, fautes


def main():
    ap = argparse.ArgumentParser(description="La porte du regard du site Centre Soha.")
    ap.add_argument("--site", required=True, help="dossier du site statique")
    ap.add_argument("--chromium", default=CHROMIUM, help="chemin du binaire Chromium")
    a = ap.parse_args()

    pages, fautes = regarder(a.site, a.chromium)

    print("%d pages ouvertes dans Chromium." % len(pages))
    if not fautes:
        print("Aucune ressource manquante, aucun appel externe, aucune erreur, "
              "aucun débordement de 1440 px à 390 px.")
        return 0

    print("\n%d faute(s) :" % len(fautes))
    for nom, quoi, detail in fautes:
        print("   %-26s %-24s %s" % (nom, quoi, detail))
    return 1


if __name__ == "__main__":
    sys.exit(main())
