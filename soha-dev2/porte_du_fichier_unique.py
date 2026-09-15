#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La porte du fichier unique : on l'ouvre et on clique dedans.

Le dossier a sa porte (`porte_du_regard.py`), qui ouvre chaque page dans un
navigateur. Celle-ci vérifie autre chose : que **réunir** les vingt-neuf pages
en un seul fichier ne les a pas abîmées. C'est une transformation, donc elle a
le droit de casser quelque chose ; il faut donc la regarder casser ou tenir.

Ce qu'elle exige :
  1. Chaque vue s'affiche, et elle seule.
  2. Le titre de l'onglet suit la page.
  3. Chaque lien interne mène à une vue qui existe — on les clique **tous**,
     un par un, depuis la page où ils se trouvent.
  4. Le bouton « retour » du navigateur ramène à la page précédente.
  5. L'estimateur calcule, et son bouton porte une vraie destination.
  6. Aucune erreur JavaScript, aucun appel vers l'extérieur, aucun identifiant
     en double, aucun débordement horizontal de 1440 px à 390 px.
"""

import argparse
import collections
import os
import sys

CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
LARGEURS = (1440, 1024, 768, 390)


def banc(fichier, chromium):
    from playwright.sync_api import sync_playwright

    url = "file://" + os.path.abspath(fichier)
    ok, fautes = [], []

    def dit(quoi, vrai, detail=""):
        (ok if vrai else fautes).append((quoi, detail))
        print("%s %-56s %s" % (" ✓" if vrai else " ✗", quoi, detail))

    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=chromium)
        ctx = nav.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        erreurs, dehors = [], []
        page.on("pageerror", lambda e: erreurs.append(str(e)))
        page.on("request", lambda r: dehors.append(r.url)
                if not r.url.startswith(("file://", "data:")) else None)

        page.goto(url, wait_until="load")
        page.wait_for_timeout(400)

        vues = page.eval_on_selector_all(
            "#soha-vues > .vue", "els => els.map(e => e.getAttribute('data-f'))")
        dit("les vingt-neuf vues sont là", len(vues) == 29, "%d vues" % len(vues))

        visibles = page.eval_on_selector_all(
            "#soha-vues > .vue", "els => els.filter(e => !e.hidden).map(e => e.getAttribute('data-f'))")
        dit("une seule vue est visible à l'ouverture",
            visibles == ["index.html"], ", ".join(visibles) or "aucune")

        # --- 1. chaque vue s'affiche, et son titre suit -----------------------
        titres_vus = 0
        images_vues = 0
        for f in vues:
            page.evaluate("f => { location.hash = '#/' + f; }", f)
            page.wait_for_timeout(90)
            etat = page.evaluate("""() => {
                var v = Array.from(document.querySelectorAll('#soha-vues > .vue'))
                             .filter(e => !e.hidden);
                return {n: v.length,
                        f: v.length ? v[0].getAttribute('data-f') : '',
                        h: v.length ? v[0].innerText.trim().length : 0,
                        titre: document.title};
            }""")
            if etat["n"] != 1 or etat["f"] != f:
                fautes.append(("vue %s" % f, "%d visible(s) : %s" % (etat["n"], etat["f"])))
                print(" ✗ %-56s %s" % ("la vue s'affiche seule : " + f, etat["f"]))
                continue
            if etat["h"] < 40:
                fautes.append(("vue %s" % f, "contenu quasi vide (%d caractères)" % etat["h"]))
                print(" ✗ %-56s %d caractères" % ("la vue a du contenu : " + f, etat["h"]))
                continue
            if etat["titre"]:
                titres_vus += 1
            # Chaque image de la vue doit VRAIMENT se décoder. Cette porte a
            # rendu « 15 réussites, 0 échec » sur un fichier où toutes les
            # photos du Journal étaient cassées : elle comptait des caractères,
            # jamais des pixels. Une porte qui ne regarde pas les images ne
            # protège pas les images.
            images = page.evaluate("""async () => {
                var v = document.querySelector('#soha-vues > .vue:not([hidden])');
                var imgs = Array.from(v ? v.querySelectorAll('img') : []);
                var cassees = [];
                for (var im of imgs) {
                    var src = im.currentSrc || im.getAttribute('src') || '';
                    if (!src.startsWith('data:')) { cassees.push('hors fichier : ' + src.slice(0, 60)); continue; }
                    im.loading = 'eager';
                    try { await im.decode(); } catch (e) { cassees.push('indécodable : ' + (im.alt || '?').slice(0, 40)); continue; }
                    if (!im.naturalWidth) cassees.push('largeur nulle : ' + (im.alt || '?').slice(0, 40));
                }
                return {n: imgs.length, cassees: cassees};
            }""")
            images_vues += images["n"]
            for c in images["cassees"]:
                fautes.append(("image %s" % f, c))
                print(" ✗ %-56s %s" % ("l'image s'affiche : " + f, c))
        dit("chaque vue s'affiche seule, avec du contenu", True, "%d vues parcourues" % len(vues))
        dit("chaque image se décode depuis le fichier lui-même",
            not any(k.startswith("image ") for k, _ in fautes), "%d images" % images_vues)
        dit("le titre de l'onglet suit la page", titres_vus == len(vues),
            "%d/%d" % (titres_vus, len(vues)))

        # --- 2. tous les liens internes, cliqués un par un --------------------
        cliques, casses = 0, []
        for f in vues:
            page.evaluate("f => { location.hash = '#/' + f; }", f)
            page.wait_for_timeout(60)
            n = page.evaluate("""() => {
                var v = document.querySelector('#soha-vues > .vue:not([hidden])');
                var tout = [].concat(
                    Array.from(document.querySelectorAll('.soha-entete a[href], .soha-pied a[href]')),
                    Array.from(v.querySelectorAll('a[href]')));
                return tout.map(a => a.getAttribute('href'))
                           .filter(h => h && /\\.html($|[?#])/i.test(h) && !/^https?:/i.test(h)).length;
            }""")
            for i in range(n):
                page.evaluate("f => { location.hash = '#/' + f; }", f)
                page.wait_for_timeout(40)
                r = page.evaluate("""(i) => {
                    var v = document.querySelector('#soha-vues > .vue:not([hidden])');
                    var tout = [].concat(
                        Array.from(document.querySelectorAll('.soha-entete a[href], .soha-pied a[href]')),
                        Array.from(v.querySelectorAll('a[href]')));
                    var liens = tout.filter(a => {
                        var h = a.getAttribute('href');
                        return h && /\\.html($|[?#])/i.test(h) && !/^https?:/i.test(h);
                    });
                    var a = liens[i];
                    if (!a) return null;
                    var vise = a.getAttribute('href').split('#')[0].split('?')[0];
                    a.click();
                    var apres = document.querySelector('#soha-vues > .vue:not([hidden])');
                    return {vise: vise, arrive: apres ? apres.getAttribute('data-f') : ''};
                }""", i)
                if r is None:
                    continue
                cliques += 1
                if r["vise"] != r["arrive"]:
                    casses.append("%s : %s → %s" % (f, r["vise"], r["arrive"]))
        dit("chaque lien interne mène là où il dit", not casses,
            "%d liens cliqués%s" % (cliques, "" if not casses else " — " + " | ".join(casses[:3])))

        # --- 3. le retour du navigateur ---------------------------------------
        page.evaluate("() => { location.hash = '#/index.html'; }")
        page.wait_for_timeout(80)
        page.evaluate("() => { location.hash = '#/contact.html'; }")
        page.wait_for_timeout(80)
        page.go_back()
        page.wait_for_timeout(150)
        ou = page.evaluate("""() => {
            var v = document.querySelector('#soha-vues > .vue:not([hidden])');
            return v ? v.getAttribute('data-f') : '';
        }""")
        dit("le bouton « retour » revient à la page précédente", ou == "index.html", ou)

        # --- 4. l'estimateur ---------------------------------------------------
        page.evaluate("() => { location.hash = '#/espaces-professionnels.html'; }")
        page.wait_for_timeout(200)
        est = page.evaluate("""() => {
            var v = document.querySelector('#soha-vues > .vue:not([hidden])');
            var prix = v.querySelector('#sePrice'), cta = v.querySelector('#seCta');
            return {prix: prix ? prix.textContent.trim() : '',
                    href: cta ? cta.getAttribute('href') : ''};
        }""")
        dit("l'estimateur affiche un prix", "$" in est["prix"], est["prix"])
        dit("son bouton porte une destination", est["href"].startswith("reservation.html?"),
            est["href"][:52])

        boutons = page.eval_on_selector_all(
            "#soha-vues > .vue:not([hidden]) #seSpaces button", "e => e.length")
        page.eval_on_selector_all(
            "#soha-vues > .vue:not([hidden]) #seSpaces button",
            "els => els[els.length-1].click()")
        page.wait_for_timeout(120)
        apres = page.evaluate("""() => document.querySelector(
            '#soha-vues > .vue:not([hidden]) #sePrice').textContent.trim()""")
        dit("changer d'espace change le prix", apres != est["prix"] and boutons >= 3,
            "%s → %s" % (est["prix"], apres))

        # cliquer le bouton doit mener à la page de réservation
        page.eval_on_selector("#soha-vues > .vue:not([hidden]) #seCta", "e => e.click()")
        page.wait_for_timeout(150)
        ou = page.evaluate("""() => {
            var v = document.querySelector('#soha-vues > .vue:not([hidden])');
            return v ? v.getAttribute('data-f') : '';
        }""")
        dit("le bouton de l'estimateur mène à la réservation", ou == "reservation.html", ou)

        # --- 5. le calendrier de « Se ressourcer » -----------------------------
        page.evaluate("() => { location.hash = '#/se-ressourcer.html'; }")
        page.wait_for_timeout(200)
        cal = page.evaluate("""() => {
            var v = document.querySelector('#soha-vues > .vue:not([hidden])');
            var s = v.querySelector('#soha-semaine');
            if (!s) return {la: false};
            return {la: true, dates: s.querySelectorAll('.jour-date').length};
        }""")
        dit("le calendrier de la semaine s'est monté",
            cal["la"] and cal.get("dates", 0) > 0, "%s date(s)" % cal.get("dates", 0))

        # --- 6. identifiants en double ----------------------------------------
        dbl = page.evaluate("""() => {
            var vus = {}, doubles = [];
            document.querySelectorAll('[id]').forEach(function (e) {
                var i = e.id;
                if (vus[i]) { if (doubles.indexOf(i) < 0) doubles.push(i); } else { vus[i] = 1; }
            });
            return doubles;
        }""")
        dit("aucun identifiant en double dans le document",
            not dbl, ", ".join(dbl[:6]) if dbl else "")

        # --- 7. débordement ----------------------------------------------------
        deborde = []
        for f in ("index.html", "espaces-professionnels.html", "journal.html",
                  "confidentialite.html", "se-ressourcer.html"):
            page.evaluate("f => { location.hash = '#/' + f; }", f)
            for l in LARGEURS:
                page.set_viewport_size({"width": l, "height": 900})
                page.wait_for_timeout(140)
                m = page.evaluate("() => ({doc: document.documentElement.scrollWidth,"
                                  " vue: window.innerWidth})")
                if m["doc"] > m["vue"] + 1:
                    deborde.append("%s à %dpx (doc %dpx)" % (f, l, m["doc"]))
        page.set_viewport_size({"width": 1440, "height": 900})
        dit("aucun débordement horizontal de 1440 px à 390 px",
            not deborde, " | ".join(deborde[:3]))

        dit("aucun appel vers l'extérieur", not dehors, ", ".join(sorted(set(dehors))[:2]))
        dit("aucune erreur JavaScript", not erreurs, " | ".join(erreurs[:2]))

        nav.close()

    print("\n" + "─" * 72)
    print("%d réussites, %d échecs" % (len(ok), len(fautes)))
    return 1 if fautes else 0


def main():
    ap = argparse.ArgumentParser(description="La porte du site en un seul fichier.")
    ap.add_argument("--fichier", required=True)
    ap.add_argument("--chromium", default=CHROMIUM)
    a = ap.parse_args()
    if not os.path.isfile(a.fichier):
        raise SystemExit("Fichier introuvable : %s" % a.fichier)
    return banc(a.fichier, a.chromium)


if __name__ == "__main__":
    sys.exit(main())
