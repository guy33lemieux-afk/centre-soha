#!/usr/bin/env python3
"""La porte du regard : on ouvre l'écran, on agit, on mesure."""
import json, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright

PORT = 8731
BASE = "http://127.0.0.1:%d" % PORT
RACINE = sys.argv[1]

srv = subprocess.Popen([sys.executable, RACINE + "/serveur.py", RACINE, str(PORT)])
time.sleep(1.0)


def banc(chemin):
    r = urllib.request.Request(BASE + chemin, method="PUT")
    return json.loads(urllib.request.urlopen(r).read())


resultats = {}
try:
    with sync_playwright() as p:
        n = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = n.new_context(viewport={"width": 1440, "height": 900})
        ctx.route("**fonts.googleapis.com**", lambda r: r.abort())
        ctx.route("**fonts.gstatic.com**", lambda r: r.abort())
        externes = []
        page = ctx.new_page()
        page.on("request", lambda r: externes.append(r.url)
                if not r.url.startswith(BASE) and not r.url.startswith("data:") else None)
        erreurs_console = []
        page.on("console", lambda m: erreurs_console.append(m.text) if m.type == "error" else None)
        page.goto(BASE + "/crm.html", wait_until="networkidle")
        page.wait_for_timeout(1200)

        racine = page.locator("#soha-crm-racine")
        resultats["l'interface est montée"] = racine.locator("*").count() > 20
        resultats["nœuds rendus"] = racine.locator("*").count()
        resultats["titre visible"] = page.locator("#soha-crm-racine").inner_text()[:60].replace("\n", " · ")
        resultats["requêtes externes"] = externes

        # 1 · la première lecture puis l'écriture du semis
        page.wait_for_timeout(1200)
        j = banc("/banc/journal")
        resultats["1. GET au chargement"] = any(l[0] == "GET" for l in j["journal"])
        resultats["2. POST du semis"] = any(l[0] == "POST" and l[1] == 200 for l in j["journal"])
        resultats["3. révision serveur"] = j["etat"]["revision"]
        semis = json.loads(j["etat"]["valeur"]) if j["etat"]["valeur"] else {}
        resultats["4. contacts enregistrés"] = len(semis.get("contacts", []))

        # 2 · un vrai geste : ajouter un contact par l'interface
        def nouveau(nom, courriel=None):
            page.get_by_role("button", name="+ Nouveau contact").first.click()
            page.wait_for_timeout(300)
            page.get_by_label("Nom").first.fill(nom)
            if courriel:
                page.get_by_label("Courriel").first.fill(courriel)
            page.get_by_role("button", name="Enregistrer").first.click()

        page.get_by_role("button", name="Répertoire").first.click()
        page.wait_for_timeout(300)
        nouveau("Essai du banc", "banc@centresoha.com")
        page.wait_for_timeout(1800)

        j = banc("/banc/journal")
        etat = json.loads(j["etat"]["valeur"])
        noms = [c.get("nom", "") for c in etat.get("contacts", [])]
        resultats["5. le contact est en base"] = "Essai du banc" in noms
        resultats["6. révision après le geste"] = j["etat"]["revision"]
        resultats["7. écritures au total (POST)"] = sum(1 for l in j["journal"] if l[0] == "POST")

        # 3 · la persistance : on recharge, le contact doit revenir
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1600)
        page.get_by_role("button", name="Répertoire").first.click()
        page.wait_for_timeout(400)
        resultats["8. survit au rechargement"] = "Essai du banc" in racine.inner_text()

        # 4 · le conflit : le serveur avance sans nous
        banc("/banc/avancer")
        nouveau("Contact du conflit", "conflit@centresoha.com")
        page.wait_for_timeout(2000)
        avis = page.locator("#soha-crm-avis")
        resultats["9. bannière de conflit"] = (avis.count() > 0 and avis.is_visible())
        texte = avis.inner_text() if avis.count() else ""
        resultats["10. la bande nomme la personne"] = texte.startswith("Dominique a enregistré")
        resultats["11. texte"] = texte[:74]

        # 5 · la panne : le serveur ne répond plus
        srv.terminate(); srv.wait()
        nouveau("Contact de la panne", "panne@centresoha.com")
        page.wait_for_timeout(2500)
        resultats["12. bannière de panne"] = (avis.inner_text()[:78] if avis.count() else "")

        resultats["erreurs console"] = [e for e in erreurs_console if "Failed to load resource" not in e][:4]
        resultats["erreurs page"] = page.evaluate("window.__erreurs")
        n.close()
finally:
    if srv.poll() is None:
        srv.terminate()

for k, v in resultats.items():
    print("%-34s %s" % (k, v))
