#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La porte du contraste : le texte clair posé sur une photo se lit-il vraiment ?

Pourquoi cette porte existe
---------------------------
Le kit déclare un voile sur ses huit héros — `background_overlay_color`,
`rgba(14,26,21,0.80)` — et le générateur du site HTML ne le lisait pas. Les
seize textes de ces héros se retrouvaient **nus sur la photo** : contraste
mesuré jusqu'à 1,04 là où il en faut 4,5. Rien ne le signalait. L'image était
là, la page s'affichait, aucune requête ne manquait : toutes les portes
existantes disaient « tout va bien ».

Comment elle mesure
-------------------
Pas d'estimation. On cache le texte clair, on photographie l'emplacement qu'il
occupait, et on lit les pixels de la photo en dessous. Le verdict porte sur le
**pire cas** — le 95ᵉ centile de luminance, c'est-à-dire l'endroit le plus
clair sous un texte clair — et non sur la moyenne : une moyenne confortable ne
console personne devant le mot illisible.

Les seuils sont ceux de WCAG 2.2 AA : 3,0 pour le texte large (≥ 24 px, ou
≥ 18,66 px en gras), 4,5 pour le reste.

Usage
-----
    python3 porte_du_contraste.py --site <dossier>
"""

import argparse
import base64
import functools
import http.server
import os
import socketserver
import sys
import threading
import time

CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
PORT = 8929
CENTILE = 0.95            # le pire cas plutôt que la moyenne


class Muet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def servir(dossier, port):
    socketserver.TCPServer.allow_reuse_address = True
    dernier = None
    for essai in range(port, port + 12):
        try:
            s = socketserver.TCPServer(("127.0.0.1", essai),
                                       functools.partial(Muet, directory=dossier))
        except OSError as e:
            dernier = e
            continue
        threading.Thread(target=s.serve_forever, daemon=True).start()
        time.sleep(0.4)
        return s, essai
    raise SystemExit("Aucun port libre à partir de %d : %s" % (port, dernier))


def luminance(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def contraste(a, b):
    la, lb = luminance(a) + 0.05, luminance(b) + 0.05
    return round(max(la, lb) / min(la, lb), 2)


# Le texte clair posé sur une image de fond, et rien d'autre : on ne juge pas
# une page entière, on va chercher le cas précis qui a échappé à tout le reste.
CANDIDATS = r"""() => {
  function lum(c){
    var m = c.match(/\d+(\.\d+)?/g); if(!m) return null;
    var f = function(v){ v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(+m[0]) + 0.7152*f(+m[1]) + 0.0722*f(+m[2]);
  }
  var out = [];
  document.querySelectorAll('main *, #soha-vues *').forEach(function(e){
    if (e.children.length) return;
    var t = (e.innerText||'').trim(); if (t.length < 12) return;
    var cs = getComputedStyle(e); var L = lum(cs.color);
    if (L === null || L < 0.45) return;
    var r = e.getBoundingClientRect();
    var a = e, fond = null;
    for (var i=0; i<8 && a; i++, a = a.parentElement){
      var acs = getComputedStyle(a);
      if (acs.backgroundImage && acs.backgroundImage.indexOf('url(') === 0){ fond = a; break; }
    }
    // Un fond peut aussi être une VRAIE image posée derrière le texte. Depuis
    // que les huit héros sont des widgets `image` et non des `background-image`,
    // cette porte ne voyait plus une seule photo : elle annonçait « 0 texte sur
    // photo » sur les pages mêmes pour lesquelles elle avait été écrite. Une
    // porte aveugle est pire qu'une porte absente.
    if (!fond) {
      var imgs = document.querySelectorAll('img');
      for (var j=0; j<imgs.length; j++){
        // On ne filtre PAS sur la position de l'image : dans le kit, c'est son
        // enveloppe qui est en `absolute`, l'image elle-même reste statique.
        // Le test qui compte est géométrique — l'image couvre-t-elle le texte.
        var ir = imgs[j].getBoundingClientRect();
        if (ir.left <= r.left && ir.top <= r.top &&
            ir.right >= r.right && ir.bottom >= r.bottom){ fond = imgs[j]; break; }
      }
    }
    if (!fond) return;
    out.push({texte: t.slice(0,44), couleur: cs.color,
              taille: parseFloat(cs.fontSize), poids: parseInt(cs.fontWeight, 10) || 400,
              x: Math.round(r.left+scrollX), y: Math.round(r.top+scrollY),
              w: Math.round(r.width), h: Math.round(r.height)});
  });
  return out;
}"""

CACHER = r"""() => {
  document.querySelectorAll('main *, #soha-vues *').forEach(function(e){
    if (e.children.length) return;
    var t = (e.innerText||'').trim(); if (t.length < 12) return;
    var m = getComputedStyle(e).color.match(/\d+/g); if (!m) return;
    var L = (0.2126*+m[0] + 0.7152*+m[1] + 0.0722*+m[2]) / 255;
    if (L > 0.6) e.style.visibility = 'hidden';
  });
}"""

PIXELS = r"""async (b64) => {
  const img = new Image();
  await new Promise(r => { img.onload = r; img.src = 'data:image/png;base64,' + b64; });
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0);
  const d = ctx.getImageData(0, 0, c.width, c.height).data;
  const out = [];
  for (let i = 0; i < d.length; i += 4) out.push([d[i], d[i+1], d[i+2]]);
  return out;
}"""


# ── Le texte posé sur une couleur, et non sur une photo ─────────────────────
#
# La première version de cette porte ne regardait que le texte CLAIR posé sur une
# IMAGE. Elle a donc laissé passer exactement ce qu'un département a trouvé à la
# main : une étiquette de 12 px en #0F7FA6 sur ivoire, à 4,30 pour un seuil de
# 4,5. Le défaut n'était pas dans la page, il était dans la liste de ce que je
# vérifiais — pour la troisième fois de ce projet.
#
# Ici, pas de pixels : la couleur du texte et celle du premier fond opaque
# au-dessus de lui suffisent, et se lisent exactement.
SUR_COULEUR = r"""() => {
  function rgb(c){
    var m = (c||'').match(/[\d.]+/g);
    return m && m.length >= 3 ? [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1] : null;
  }
  var out = [];
  document.querySelectorAll('main *, #soha-vues *').forEach(function(e){
    if (e.children.length) return;
    var t = (e.innerText||'').trim(); if (t.length < 3) return;
    var cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') return;
    var r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return;

    // Le premier fond opaque en remontant. Une image de fond : on passe —
    // c'est l'autre moitié de la porte qui s'en occupe, aux pixels.
    var a = e, fond = null;
    for (var i = 0; i < 14 && a; i++, a = a.parentElement){
      var acs = getComputedStyle(a);
      if (acs.backgroundImage && acs.backgroundImage.indexOf('url(') === 0) return;
      var b = rgb(acs.backgroundColor);
      if (b && b[3] >= 0.98){ fond = b; break; }
    }
    if (!fond) return;
    var c = rgb(cs.color); if (!c) return;
    out.push({texte: t.slice(0,40), couleur: [c[0],c[1],c[2]], fond: [fond[0],fond[1],fond[2]],
              taille: parseFloat(cs.fontSize), poids: parseInt(cs.fontWeight,10) || 400});
  });
  return out;
}"""


def seuil_de(taille, poids):
    """WCAG 2.2 AA : 3,0 pour le texte large, 4,5 pour le reste."""
    grand = taille >= 24 or (taille >= 18.66 and poids >= 700)
    return 3.0 if grand else 4.5


def mesurer(site, chromium, port=PORT):
    from playwright.sync_api import sync_playwright

    pages = sorted(f for f in os.listdir(site)
                   if f.endswith(".html") and f != "lisez-moi.html")
    serveur, port = servir(site, port)
    base = "http://127.0.0.1:%d" % port
    resultats = []

    try:
        with sync_playwright() as p:
            nav = p.chromium.launch(executable_path=chromium)
            lecteur = nav.new_page()               # sert de décodeur d'images
            for nom in pages:
                pg = nav.new_page(viewport={"width": 1440, "height": 900})
                pg.goto("%s/%s" % (base, nom), wait_until="networkidle")
                pg.wait_for_timeout(250)
                for x in pg.evaluate(SUR_COULEUR):
                    resultats.append({
                        "page": nom, "texte": x["texte"], "ou": "couleur",
                        "taille": x["taille"], "poids": x["poids"],
                        "median": contraste(x["couleur"], x["fond"]),
                        "pire": contraste(x["couleur"], x["fond"]),
                        "seuil": seuil_de(x["taille"], x["poids"]),
                    })

                candidats = pg.evaluate(CANDIDATS)
                if not candidats:
                    pg.close()
                    continue
                pg.evaluate(CACHER)                # ce qui reste, c'est le fond
                pg.wait_for_timeout(120)
                for c in candidats:
                    clip = {"x": c["x"], "y": c["y"],
                            "width": max(c["w"], 4), "height": max(c["h"], 4)}
                    px = lecteur.evaluate(PIXELS,
                                          base64.b64encode(pg.screenshot(clip=clip)).decode())
                    px.sort(key=luminance)
                    pire = px[min(int(len(px) * CENTILE), len(px) - 1)]
                    couleur = [int(v) for v in
                               c["couleur"].replace("rgb(", "").replace(")", "").split(",")[:3]]
                    resultats.append({
                        "page": nom, "texte": c["texte"], "ou": "photo",
                        "taille": c["taille"], "poids": c["poids"],
                        "median": contraste(couleur, px[len(px) // 2]),
                        "pire": contraste(couleur, pire),
                        "seuil": seuil_de(c["taille"], c["poids"]),
                    })
                pg.close()
            nav.close()
    finally:
        serveur.shutdown()

    return resultats


def main():
    ap = argparse.ArgumentParser(description="La porte du contraste du site Centre Soha.")
    ap.add_argument("--site", required=True, help="dossier du site statique")
    ap.add_argument("--chromium", default=CHROMIUM)
    ap.add_argument("--bavard", action="store_true", help="montrer aussi ce qui passe")
    a = ap.parse_args()

    r = mesurer(a.site, a.chromium)
    if not r:
        print("Aucun texte clair posé sur une image : rien à mesurer.")
        return 0

    sous = [x for x in r if x["pire"] < x["seuil"]]
    if a.bavard or sous:
        print("%-28s %-42s %7s %7s %6s" % ("page", "texte", "médian", "pire", "seuil"))
        for x in (r if a.bavard else sous):
            print("%-28s %-42s %7.2f %7.2f %6.1f  %s"
                  % (x["page"], x["texte"][:42], x["median"], x["pire"], x["seuil"],
                     "◀ SOUS LE SEUIL" if x["pire"] < x["seuil"] else ""))
        print()

    photo = [x for x in r if x.get("ou") == "photo"]
    couleur = [x for x in r if x.get("ou") == "couleur"]
    print("%d texte(s) mesuré(s) — %d sur photo, %d sur couleur."
          % (len(r), len(photo), len(couleur)))
    if sous:
        print("%d sous le seuil WCAG AA." % len(sous))
        return 1
    print("Tous au-dessus du seuil WCAG AA (pire cas : %.2f)."
          % min(x["pire"] for x in r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
