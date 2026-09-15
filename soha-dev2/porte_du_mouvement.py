#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la porte du mouvement : ce qui bouge, combien de temps, et si ça
s'arrête quand on le demande.

Écrite par le département mouvement du grand conseil (15 septembre 2026), après
avoir mesuré ce que le site fait vraiment (mesure_mouvement.py, six pages, deux
largeurs) :

  · zéro animation, zéro transform, zéro keyframe au rendu — le silence tient ;
  · toutes les transitions rendues à 140 ms cubic-bezier(.22,.61,.36,1) SAUF
    deux, dans le widget HTML de l'horaire (7326) : `140ms ease` ;
  · trois boutons du kit portent `hover_animation: "grow"` (pages 7389, 7390,
    7392, « ← Revenir aux formations ») — Elementor le rend en
    `transform:scale(1.1)` au survol, .3s. Le générateur ignore la clé : ma
    maquette ne le montre pas, le site de Mala le fait ;
  · le bloc `prefers-reduced-motion` global (`*{…}`) n'existe QUE dans le
    générateur ; le kit ne coupe que les boutons ;
  · le halo de l'anneau de focus est #19A7DB, l'accent de Soigner ; sur le CTA
    de l'estimateur (fond #19A7DB) l'anneau mesure 1,00 — invisible.

Ce que la porte regarde
-----------------------
STATIQUE (kit + site + extension) :
  1. aucune clé Elementor d'animation non vide (hover_animation, _animation…) ;
  2. aucun motif interdit hors commentaires : scale(, marquee, spin, parallax,
     filter:blur, text-shadow, animation infinite — sauf le pulse « EN DIRECT » ;
  3. toute `transition` déclarée : durée ∈ {140 ms, 280 ms, 0} et easing =
     cubic-bezier(.22,.61,.36,1) — jamais `ease`, `linear`, `ease-in-out` ;
  4. le custom_css du kit porte les jetons --mo-fast/--mo-base/--mo-ease et un
     bloc prefers-reduced-motion GLOBAL (`*`), pas seulement pour les boutons ;
  5. l'anneau de focus n'emprunte aucun accent d'école et n'est jamais éteint
     (outline:none / outline:0 sans anneau de remplacement).
RENDU (--site, Chromium) :
  6. durées calculées ∈ {0.14s, 0.28s}, 0 animation, 0 transform au repos ;
  7. en reduced-motion : toute durée calculée ≤ 1 ms, scroll-behavior auto ;
  8. tabulation réelle : chaque anneau de focus ≥ 3:1 sur ce qui est derrière
     lui (l'outline se mesure sur le halo quand il y en a un). L'anneau est lu
     AU MOMENT du Tab, pas après : un anneau qui se fond en 140 ms est lu à
     0,00 — c'est voulu, l'anneau de focus apparaît d'un coup (soha-motion §2) ;
  9. lisible sans défiler ni JS : ≥ 40 caractères de texte dans le premier
     écran en reduced-motion.

Sort 0 si tout tient, 1 sinon, en nommant chaque défaut.

Usage :
    python3 porte_du_mouvement.py --kit <kit14> [--site <site29>]
        [--extension <soha-estimateur.php>] [--pages index,se-ressourcer,…]
"""

import argparse
import glob
import json
import os
import re
import sys

ECOLES = re.compile(r"19A7DB|D29A4E|5E8C5A", re.I)
INTERDITS = re.compile(
    r"scale\(|marquee|@keyframes[^{]*spin|parallax|filter\s*:\s*blur|"
    r"text-shadow|animation[^;}]*infinite", re.I)
EXCEPTION = re.compile(r"pulse|livedot|soha-direct", re.I)
CANON_EASE = re.compile(r"cubic-bezier\(\s*0?\.22\s*,\s*0?\.61\s*,\s*0?\.36\s*,\s*1\s*\)")
DUREES_OK = {"140ms", ".14s", "0.14s", "280ms", ".28s", "0.28s", "0s", "0ms"}
CLES_ANIM = ("hover_animation", "_animation", "_animation_mobile",
             "_animation_tablet", "animation", "button_hover_animation",
             "image_hover_animation", "hover_animation_type")


def sans_commentaires(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"^\s*#.*$", "", t, flags=re.M)  # commentaires python/php simples
    return t


def transitions_hors_canon(texte):
    """Retourne les déclarations `transition:` dont une durée ou un easing
    sort du canon. Les `transition-duration:.01ms!important` du bloc
    reduced-motion et `transition:none` sont admises."""
    defauts = []
    for m in re.finditer(r"transition\s*:\s*([^;}]*)", texte):
        v = m.group(1).strip()
        if v in ("none", "") or v.startswith("var("):
            continue
        for partie in re.split(r",(?![^(]*\))", v):
            partie = partie.strip()
            if not partie or partie == "none":
                continue
            durees = re.findall(r"(?<![\w.])(\d*\.?\d+m?s)\b", partie)
            duree = durees[0] if durees else None
            easing = "canon" if CANON_EASE.search(partie) else (
                re.search(r"\b(ease(-in|-out|-in-out)?|linear|steps\(|cubic-bezier\()", partie))
            if duree and duree not in DUREES_OK and not partie.startswith("var("):
                defauts.append("durée hors canon « %s »" % partie)
            elif easing != "canon" and easing is not None:
                defauts.append("easing hors canon « %s »" % partie)
            elif easing is None and duree and duree not in ("0s", "0ms") and "var(" not in partie:
                defauts.append("easing absent (ease implicite) « %s »" % partie)
    return defauts


def chaines(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from chaines(v)
    elif isinstance(o, list):
        for v in o:
            yield from chaines(v)
    elif isinstance(o, str):
        yield o


def cles_animation(o, chemin, out):
    if isinstance(o, dict):
        s = o.get("settings")
        if isinstance(s, dict):
            for k in CLES_ANIM:
                v = s.get(k)
                if v not in (None, "", "none", []):
                    out.append("%s · %s (%s) : %s = %r" % (
                        chemin, o.get("id"), o.get("widgetType") or o.get("elType"), k, v))
        for v in o.values():
            cles_animation(v, chemin, out)
    elif isinstance(o, list):
        for v in o:
            cles_animation(v, chemin, out)


def statique(kit, site, extension):
    defauts = []
    fichiers = sorted(glob.glob(os.path.join(kit, "content", "**", "*.json"), recursive=True)
                      + glob.glob(os.path.join(kit, "templates", "*.json")))
    for f in fichiers:
        d = json.load(open(f, encoding="utf-8"))
        rel = os.path.relpath(f, kit)
        cles_animation(d, rel, defauts)
        for s in chaines(d):
            if "transition" in s or INTERDITS.search(s):
                t = sans_commentaires(s)
                for m in INTERDITS.finditer(t):
                    ctx = t[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                    if not EXCEPTION.search(ctx):
                        defauts.append("%s : motif interdit « %s »" % (rel, m.group(0)))
                for x in transitions_hors_canon(t):
                    defauts.append("%s : %s" % (rel, x))

    ss = os.path.join(kit, "site-settings.json")
    css = json.load(open(ss, encoding="utf-8")).get("settings", {}).get("custom_css", "")
    c = sans_commentaires(css)
    for m in INTERDITS.finditer(c):
        ctx = c[max(0, m.start() - 40):m.end() + 40]
        if not EXCEPTION.search(ctx):
            defauts.append("site-settings custom_css : motif interdit « %s »" % m.group(0))
    for x in transitions_hors_canon(c):
        defauts.append("site-settings custom_css : %s" % x)
    for jeton in ("--mo-fast", "--mo-base", "--mo-ease"):
        if jeton + ":" not in c:
            defauts.append("site-settings custom_css : jeton %s absent" % jeton)
    if not re.search(r"prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{\s*\*", c):
        defauts.append("site-settings custom_css : pas de bloc prefers-reduced-motion GLOBAL (`*`)")
    for m in re.finditer(r"[^{}]*:focus-visible[^{]*\{([^}]*)\}", c):
        corps = m.group(1)
        if ECOLES.search(corps):
            defauts.append("site-settings custom_css : anneau de focus avec un accent d'école « %s »"
                           % ECOLES.search(corps).group(0))
    for m in re.finditer(r"outline\s*:\s*(none|0)\s*[;}]", c):
        defauts.append("site-settings custom_css : outline éteint sans remplacement (`%s`)" % m.group(0).strip())

    for chemin in ([extension] if extension else []):
        t = sans_commentaires(open(chemin, encoding="utf-8").read())
        for x in transitions_hors_canon(t):
            defauts.append("%s : %s" % (os.path.basename(chemin), x))
        for m in re.finditer(r"[^{}]*:focus-visible[^{]*\{([^}]*)\}", t):
            if ECOLES.search(m.group(1)) or "var(--se-accent)" in m.group(1):
                defauts.append("%s : anneau de focus sur l'accent (« %s »)" % (
                    os.path.basename(chemin), m.group(0).strip()[:80]))

    if site:
        for f in sorted(glob.glob(os.path.join(site, "assets", "*.css"))
                        + glob.glob(os.path.join(site, "*.html"))):
            t = sans_commentaires(open(f, encoding="utf-8").read())
            rel = os.path.relpath(f, site)
            for m in INTERDITS.finditer(t):
                ctx = t[max(0, m.start() - 40):m.end() + 40]
                if not EXCEPTION.search(ctx):
                    defauts.append("%s : motif interdit « %s »" % (rel, m.group(0)))
            for x in transitions_hors_canon(t):
                defauts.append("%s : %s" % (rel, x))
    return defauts


# ---------------------------------------------------------------- rendu ----
JS_INVENT = """() => {
  const out={durees:{}, anim:0, transform:0};
  for (const el of document.querySelectorAll('body *')) {
    const cs=getComputedStyle(el);
    const tfs=cs.transitionTimingFunction.match(/cubic-bezier\\([^)]*\\)|steps\\([^)]*\\)|[a-z-]+/g)||['ease'];
    cs.transitionDuration.split(',').map(s=>s.trim()).forEach((d,i)=>{
      if (d==='0s') return;
      const k=d+' '+(tfs[i]||tfs[tfs.length-1]); out.durees[k]=(out.durees[k]||0)+1; });
    if (cs.animationName!=='none') out.anim++;
    if (cs.transform!=='none') out.transform++;
  }
  return out; }"""

JS_FOCUS = """() => {
  const el=document.activeElement; if(!el||el===document.body) return null;
  const cs=getComputedStyle(el); const r=el.getBoundingClientRect();
  let p=el, sol=null;
  while(p && p!==document.documentElement){
    const bg=getComputedStyle(p).backgroundColor;
    if (bg && !bg.startsWith('rgba(0, 0, 0, 0)') && bg!=='transparent'){ sol=bg; break; }
    p=p.parentElement; }
  return {tag:el.tagName, txt:(el.innerText||el.value||el.getAttribute('aria-label')||'').trim().slice(0,40),
    oc:cs.outlineColor, ow:cs.outlineWidth, os:cs.outlineStyle, off:cs.outlineOffset, sh:cs.boxShadow, sol:sol, y:Math.round(r.top+scrollY), x:Math.round(r.left)}; }"""

JS_REDUCED = """() => {
  let maxDur=0;
  for (const el of document.querySelectorAll('body *')) {
    const cs=getComputedStyle(el);
    for (const d of cs.transitionDuration.split(',')) maxDur=Math.max(maxDur, parseFloat(d)*(d.trim().endsWith('ms')?1:1000));
    for (const d of cs.animationDuration.split(',')) maxDur=Math.max(maxDur, parseFloat(d)*(d.trim().endsWith('ms')?1:1000)); }
  const vis=[...document.querySelectorAll('h1,h2,h3,p,a,button,li')].filter(e=>{const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return r.bottom>0 && r.top<innerHeight && cs.opacity!=='0' && cs.visibility!=='hidden'});
  return {maxDurMs:maxDur, sb:getComputedStyle(document.documentElement).scrollBehavior, texte:vis.map(e=>e.innerText||'').join(' ').length}; }"""


def lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def contraste(a, b):
    la, lb = lum(a), lum(b)
    la, lb = max(la, lb), min(la, lb)
    return (la + .05) / (lb + .05)


def couleur(c):
    if not c or c == "none":
        return None, 0, 0
    m = re.search(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)", c)
    if not m:
        return None, 0, 0
    rgb = tuple(float(m.group(i)) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) else 1.0
    px = re.findall(r"(-?[\d.]+)px", c[m.end():])
    spread = float(px[3]) if len(px) >= 4 else 0
    return rgb, a, spread


def rendu(site, pages, chromium):
    import functools
    import http.server
    import threading
    from playwright.sync_api import sync_playwright

    class Muet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Muet, directory=site))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/" % srv.server_address[1]
    defauts, mesures = [], {}
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=chromium)
        for page in pages:
            for w in (1440, 390):
                nom = "%s@%d" % (page, w)
                ctx = br.new_context(viewport={"width": w, "height": 900})
                pg = ctx.new_page()
                pg.goto(base + page + ".html", wait_until="load")
                inv = pg.evaluate(JS_INVENT)
                for k, n in inv["durees"].items():
                    d, e = k.split(" ", 1)
                    if d not in ("0.14s", "0.28s") or not CANON_EASE.search(e):
                        defauts.append("%s : %d élément(s) avec transition calculée « %s »" % (nom, n, k))
                if inv["anim"]:
                    defauts.append("%s : %d élément(s) animé(s)" % (nom, inv["anim"]))
                if inv["transform"]:
                    defauts.append("%s : %d transform au repos" % (nom, inv["transform"]))
                vus, invisibles, n = set(), [], 0
                for _ in range(160):
                    pg.keyboard.press("Tab")
                    f = pg.evaluate(JS_FOCUS)
                    if not f:
                        break
                    cle = (f["tag"], f["txt"], f["y"], f["x"])
                    if cle in vus:
                        break
                    vus.add(cle)
                    n += 1
                    sol, _, _ = couleur(f["sol"])
                    orgb, _, _ = couleur(f["oc"])
                    hrgb, ha, spread = couleur(f["sh"])
                    halo = hrgb if (hrgb and ha > 0 and spread > 0) else None
                    out_ok = f["os"] != "none" and f["ow"] != "0px" and orgb is not None
                    off = float(re.sub(r"[^\d.-]", "", f["off"] or "0") or 0)
                    ow = float(re.sub(r"[^\d.]", "", f["ow"] or "0") or 0)
                    c_out = 0
                    if out_ok:
                        # l'outline est peint par-dessus le halo quand le halo l'englobe
                        fond = halo if (halo is not None and spread >= off + ow) else sol
                        c_out = contraste(orgb, fond) if fond else 0
                    c_halo = contraste(halo, sol) if (halo is not None and sol) else 0
                    if max(c_out, c_halo) < 3.0:
                        invisibles.append("%s « %s » sol %s : outline %.2f, halo %.2f" % (
                            f["tag"], f["txt"], f["sol"], c_out, c_halo))
                for i in invisibles:
                    defauts.append("%s : anneau de focus invisible — %s" % (nom, i))
                ctx.close()
                ctx2 = br.new_context(viewport={"width": w, "height": 900}, reduced_motion="reduce")
                pg2 = ctx2.new_page()
                pg2.goto(base + page + ".html", wait_until="load")
                rm = pg2.evaluate(JS_REDUCED)
                if rm["maxDurMs"] > 1:
                    defauts.append("%s : reduced-motion, une durée reste à %.0f ms" % (nom, rm["maxDurMs"]))
                if rm["sb"] != "auto":
                    defauts.append("%s : reduced-motion, scroll-behavior %s" % (nom, rm["sb"]))
                if rm["texte"] < 40:
                    defauts.append("%s : %d caractères lisibles sans défiler" % (nom, rm["texte"]))
                ctx2.close()
                mesures[nom] = {"tabules": n, "invisibles": len(invisibles),
                                "durees": inv["durees"], "reduced_max_ms": rm["maxDurMs"],
                                "texte_premier_ecran": rm["texte"]}
        br.close()
    srv.shutdown()
    return defauts, mesures


def main():
    ap = argparse.ArgumentParser(description="La porte du mouvement.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--site")
    ap.add_argument("--extension")
    ap.add_argument("--pages", default="index,se-ressourcer,prendre-soin,journal,espaces-professionnels,studio-podcast")
    ap.add_argument("--chromium", default=os.environ.get("PW_CHROMIUM", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"))
    ap.add_argument("--sans-rendu", action="store_true")
    a = ap.parse_args()

    defauts = statique(a.kit, a.site, a.extension)
    print("STATIQUE : %d défaut(s)" % len(defauts))
    for d in defauts:
        print("   ✗ " + d)
    if a.site and not a.sans_rendu:
        dr, mesures = rendu(a.site, a.pages.split(","), a.chromium)
        print("RENDU : %d défaut(s)" % len(dr))
        for d in dr:
            print("   ✗ " + d)
        for k, m in mesures.items():
            print("   · %s : %d tabulés, %d anneau(x) invisible(s), durées %s, reduced max %.2f ms, %d car. au premier écran"
                  % (k, m["tabules"], m["invisibles"], m["durees"], m["reduced_max_ms"], m["texte_premier_ecran"]))
        defauts += dr
    print("PORTE DU MOUVEMENT : %s" % ("ouverte (0 défaut)" if not defauts else "FERMÉE (%d défaut(s))" % len(defauts)))
    return 0 if not defauts else 1


if __name__ == "__main__":
    sys.exit(main())
