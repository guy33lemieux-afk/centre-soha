#!/usr/bin/env python3
"""L'estimateur dans un vrai navigateur, avec et sans JavaScript.

Les deux passages comptent autant l'un que l'autre. Sans JavaScript, on éprouve
ce que voit quelqu'un dont le script n'a pas tourné — Rocket Loader, une erreur
ailleurs sur la page, une connexion coupée au mauvais moment. Le bouton doit
mener quelque part de juste, même figé sur la sélection de départ.
"""
import json, os, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright

ICI = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(ICI, "wordpress")
# Le port est celui que `wp-config.php` déclare dans WP_HOME : WordPress
# fabrique ses liens à partir de là, et une page servie ailleurs renverrait
# vers un serveur qui n'existe pas.
PORT, CHROME = 8899, "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BASE = "http://127.0.0.1:%d" % PORT

serveur = subprocess.Popen(["php", "-S", "127.0.0.1:%d" % PORT, "-t", W],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(40):
    try:
        urllib.request.urlopen(BASE + "/", timeout=1); break
    except Exception:
        time.sleep(0.5)

ok = ko = 0
def dit(quoi, vrai, detail=""):
    global ok, ko
    if vrai: ok += 1
    else: ko += 1
    print(" %s %-54s %s" % ("✓" if vrai else "✗", quoi, detail))

def php(code):
    r = subprocess.run(["php", "-r",
        '$_SERVER["HTTP_HOST"]="127.0.0.1:%d";$_SERVER["REQUEST_URI"]="/";'
        '$_SERVER["SERVER_NAME"]="127.0.0.1";require "%s/wp-load.php";%s' % (PORT, W, code)],
        capture_output=True, text=True)
    return r.stdout.strip()

# une page qui porte le shortcode
page = php('''
$id = wp_insert_post(array("post_type"=>"page","post_status"=>"publish",
  "post_title"=>"Espaces professionnels","post_name"=>"espaces-professionnels",
  "post_content"=>"[soha_estimateur]"));
echo get_permalink($id);''')

try:
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=CHROME)

        # ---------- sans JavaScript ----------
        ctx = nav.new_context(java_script_enabled=False)
        pg = ctx.new_page()
        pg.goto(page, wait_until="domcontentloaded")
        cta = pg.locator("#seCta")
        href = cta.get_attribute("href")
        dit("sans JavaScript, le bouton mène quelque part",
            href and href != "#" and "reservation" in href, href)
        dit("sans JavaScript, un prix est affiché",
            "450" in pg.locator("#sePrice").inner_text(), pg.locator("#sePrice").inner_text().strip())
        dit("sans JavaScript, la sélection est décrite",
            "Studio" in pg.locator("#seSel").inner_text(), pg.locator("#seSel").inner_text().strip())
        ctx.close()

        # ---------- avec JavaScript ----------
        ctx = nav.new_context(viewport={"width": 1200, "height": 900})
        pg = ctx.new_page()
        erreurs = []
        pg.on("pageerror", lambda e: erreurs.append(str(e)))
        pg.goto(page, wait_until="networkidle"); pg.wait_for_timeout(400)

        dit("aucune erreur JavaScript", not erreurs, erreurs[:2])
        dit("le prix de départ est le bon", "450" in pg.locator("#sePrice").inner_text())

        # Espace SÖHA · fin de semaine · demi-journée = 400 (grille)
        pg.locator('#seSpaces .se-space[data-k="soha"]').click()
        pg.locator('#seDay button[data-k="fds"]').click()
        pg.locator('#seSlot button[data-k="demi"]').click()
        pg.wait_for_timeout(200)

        prix = pg.locator("#sePrice").inner_text()
        dit("trois clics donnent le tarif de la grille", "400" in prix, prix.strip())
        dit("la sélection est écrite en clair",
            "Espace SÖHA" in pg.locator("#seSel").inner_text()
            and "Fin de semaine" in pg.locator("#seSel").inner_text(),
            pg.locator("#seSel").inner_text().strip())

        href = pg.locator("#seCta").get_attribute("href")
        dit("le bouton emporte la sélection",
            all(x in href for x in ("espace=soha", "jour=fds", "plage=demi", "tarif=400")), href)

        enfonce = pg.locator('#seSpaces .se-space[aria-pressed="true"]')
        dit("un seul espace est annoncé comme choisi", enfonce.count() == 1,
            enfonce.first.inner_text().split("\n")[0])
        dit("le prix s'annonce aux lecteurs d'écran",
            pg.locator("#sePrice").get_attribute("aria-live") == "polite")

        # le tour complet de la grille, comparé à la source
        grille = json.loads(php('echo wp_json_encode(soha_estim_grille());'))
        faux = []
        for cle, e in grille.items():
            for jour, i in (("sem", 2), ("fds", 3)):
                for plage in ("jour", "demi", "soir"):
                    pg.locator('#seSpaces .se-space[data-k="%s"]' % cle).click()
                    pg.locator('#seDay button[data-k="%s"]' % jour).click()
                    pg.locator('#seSlot button[data-k="%s"]' % plage).click()
                    attendu = str(e[i][plage])
                    lu = pg.locator("#sePrice").inner_text()
                    if attendu not in lu.replace(" ", "").replace(" ", ""):
                        faux.append("%s/%s/%s : %s au lieu de %s" % (cle, jour, plage, lu.strip(), attendu))
        dit("les 24 tarifs affichés sont ceux de la grille", not faux,
            "24 combinaisons" if not faux else faux[:2])

        # le téléphone
        for l in (1200, 768, 390):
            pg.set_viewport_size({"width": l, "height": 900}); pg.wait_for_timeout(200)
            m = pg.evaluate("() => ({doc: document.documentElement.scrollWidth, vue: window.innerWidth})")
            dit("  %4dpx : pas de débordement" % l, m["doc"] <= m["vue"] + 1,
                "doc %d" % m["doc"])
        nav.close()
finally:
    serveur.terminate()

print("\n" + "─" * 74)
print("%d réussites, %d échecs" % (ok, ko))
sys.exit(1 if ko else 0)
