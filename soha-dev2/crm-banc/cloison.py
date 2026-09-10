#!/usr/bin/env python3
"""Deux mesures que le premier banc ne fait pas : l'étanchéité du CSS, et la
largeur. L'écran d'administration se regarde aussi sur une tablette."""
import subprocess, sys, time
from playwright.sync_api import sync_playwright

R = sys.argv[1]; PORT = 8735; BASE = "http://127.0.0.1:%d" % PORT
srv = subprocess.Popen([sys.executable, R + "/serveur.py", R, str(PORT)]); time.sleep(1)
try:
    with sync_playwright() as p:
        n = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = n.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.goto(BASE + "/crm.html", wait_until="networkidle"); pg.wait_for_timeout(1400)

        # 1 · l'étanchéité : on pose DEHORS les classes que WordPress utilise aussi
        temoins = pg.evaluate("""() => {
          const hote = document.createElement('div');
          hote.id = 'temoins';
          hote.innerHTML = "<div class='card'>c</div><span class='badge'>b</span>"
                         + "<button class='btn btn-primary'>p</button>"
                         + "<div class='soha'><h2>h</h2></div>";
          document.getElementById('banc-admin').appendChild(hote);
          const lu = (s, props) => {
            const e = hote.querySelector(s); const c = getComputedStyle(e);
            const o = {}; props.forEach(k => o[k] = c[k]); return o;
          };
          return {
            card:   lu('.card',  ['backgroundColor','borderRadius','padding']),
            badge:  lu('.badge', ['backgroundColor','fontSize','textTransform']),
            bouton: lu('.btn',   ['backgroundColor','color','borderRadius']),
            titre:  lu('.soha h2', ['fontFamily','color'])
          };
        }""")
        neutre = {
            "card":   temoins["card"]["backgroundColor"] in ("rgba(0, 0, 0, 0)", "transparent"),
            "badge":  temoins["badge"]["textTransform"] == "none",
            "bouton": temoins["bouton"]["backgroundColor"] not in ("rgb(14, 26, 21)",),
            "titre":  "Fraunces" not in temoins["titre"]["fontFamily"],
        }
        print("étanchéité du CSS hors de la racine")
        for k, v in neutre.items():
            print("   %-10s intact : %s   %s" % (k, v, temoins[k]))

        # 2 · la largeur — avec la gouttière de wp-admin, qui est la vraie
        #     contrainte : le menu de WordPress prend 160 px, donc le CRM voit
        #     toujours moins large que la fenêtre. Sa seule @media est en
        #     max-width:860px, mesurée sur la fenêtre : c'est là que ça se joue.
        pg.evaluate("document.getElementById('banc-admin').style.paddingLeft='160px'")
        print("débordement horizontal (menu wp-admin de 160 px compris)")
        for l in (1440, 1100, 1024, 960, 860, 768, 390):
            pg.set_viewport_size({"width": l, "height": 900})
            pg.wait_for_timeout(500)
            m = pg.evaluate("""() => {
              const r = document.getElementById('soha-crm-racine');
              let pire = null, large = 0;
              r.querySelectorAll('*').forEach(e => {
                const b = e.getBoundingClientRect();
                if (b.right > window.innerWidth + 1 && b.width > large) {
                  large = b.width; pire = e.className + ' (' + Math.round(b.right) + 'px)';
                }
              });
              return {doc: document.documentElement.scrollWidth, vue: window.innerWidth, pire: pire};
            }""")
            print("   %4dpx : doc %4dpx   %s" % (l, m["doc"], "—" if not m["pire"] else "déborde : " + str(m["pire"])))
        n.close()
finally:
    srv.terminate()
