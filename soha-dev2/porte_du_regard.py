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


# La lecture de l'anneau se fait au CLAVIER, et c'est tout le sujet.
# `element.focus()` depuis un script ne met pas toujours `:focus-visible` —
# Chromium réserve ce pseudo-classe à ce qu'il juge être une navigation
# clavier. Une première version de cette porte focalisait en JS et rapportait
# trois éléments « sans anneau » qui en ont un : elle mentait. On tabule.
ETAT = r"""() => {
  function lum(c){
    var m=(c||'').match(/[\d.]+/g); if(!m||m.length<3) return null;
    var f=function(v){v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055,2.4);};
    return 0.2126*f(+m[0])+0.7152*f(+m[1])+0.0722*f(+m[2]);
  }
  var e=document.activeElement;
  if (!e || e===document.body) return null;
  var r=e.getBoundingClientRect(); if (r.width<2 || r.height<2) return null;
  var cs=getComputedStyle(e);
  var couleurs=[];
  if (cs.outlineStyle!=='none' && parseFloat(cs.outlineWidth)>0) couleurs.push(cs.outlineColor);
  var om=(cs.boxShadow||'').match(/rgba?\([^)]*\)/g);
  if (om) couleurs.push.apply(couleurs, om);
  var fond='rgb(255,255,255)';
  for (var a=e; a; a=a.parentElement){
    var b=getComputedStyle(a).backgroundColor;
    var m=(b||'').match(/[\d.]+/g);
    if (m && (m.length<4 || +m[3]>=0.98)) { fond=b; break; }
  }
  var cle=(e.tagName+'.'+String(e.className||'').split(' ')[0]).slice(0,40);
  if (!couleurs.length) return {cle:cle, ratio:0, nu:true};
  var lf=lum(fond), best=0;
  for (var i=0;i<couleurs.length;i++){
    var la=lum(couleurs[i]); if (la===null) continue;
    var x=(Math.max(la,lf)+0.05)/(Math.min(la,lf)+0.05);
    if (x>best) best=x;
  }
  return {cle:cle, ratio:best, nu:false};
}"""


def anneaux_faibles(page, arrets=18):
    """Tabule pour de vrai et rapporte les anneaux sous 3:1 (WCAG 2.2, 1.4.11)."""
    faibles, vus = [], set()
    for _ in range(arrets):
        page.keyboard.press("Tab")
        r = page.evaluate(ETAT)
        if not r or r["cle"] in vus:
            continue
        vus.add(r["cle"])
        if r["nu"]:
            faibles.append("%s — aucun anneau" % r["cle"])
        elif r["ratio"] < 3.0:
            faibles.append("%s — %.2f:1" % (r["cle"], r["ratio"]))
    return faibles





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

                # L'ANNEAU DE FOCUS. Cette porte ne le regardait pas, et le
                # 14 septembre le kit a porté pendant six heures DEUX règles de
                # focus contradictoires : celle de septembre, en #19A7DB à
                # 2,61:1, et la mienne écrite en `:where()`, qui vaut zéro en
                # spécificité et perdait donc la cascade. J'avais annoncé le
                # correctif fait. Quatorze tabulations sur quatorze gardaient
                # l'ancien anneau. Rien ne le signalait : la page s'affichait,
                # la règle existait, le fichier la contenait.
                #
                # On ne lit plus la feuille : on tabule, et on regarde ce que
                # le navigateur a réellement calculé.
                faibles = anneaux_faibles(page)

                for quoi, liste in (("ressource introuvable", manquants),
                                    ("appel externe", dehors),
                                    ("erreur JavaScript", erreurs),
                                    ("débordement horizontal", deborde),
                                    ("lien absolu (mort hors du serveur)", sorted(set(liens_absolus))),
                                    ("lien vers un fichier absent", sorted(set(liens_morts))),
                                    ("anneau de focus sous 3:1", faibles)):
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
