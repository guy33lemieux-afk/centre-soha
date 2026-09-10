#!/usr/bin/env python3
"""Le CRM dans un vrai WordPress, dans un vrai navigateur.

Le banc PHP prouve que les fonctions font ce qu'on croit. Celui-ci prouve la
seule chose qui compte pour Mala : elle se connecte, elle tape un nom, elle
recharge, et le nom est encore là — servi par WordPress, écrit dans la base.
"""
import json, os, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright

ICI = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(ICI, "wordpress")
PORT = 8899
BASE = "http://127.0.0.1:%d" % PORT
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

serveur = subprocess.Popen([sys.executable and "php", "-S", "127.0.0.1:%d" % PORT, "-t", W],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(40):
    try:
        urllib.request.urlopen(BASE + "/wp-login.php", timeout=1)
        break
    except Exception:
        time.sleep(0.5)

ok = ko = 0
def dit(quoi, vrai, detail=""):
    global ok, ko
    if vrai: ok += 1
    else: ko += 1
    print(" %s %-52s %s" % ("✓" if vrai else "✗", quoi, detail))

def en_base(php):
    r = subprocess.run(["php", "-r",
        '$_SERVER["HTTP_HOST"]="127.0.0.1:%d";$_SERVER["REQUEST_URI"]="/";'
        '$_SERVER["SERVER_NAME"]="127.0.0.1";require "%s/wp-load.php";%s' % (PORT, W, php)],
        capture_output=True, text=True)
    return r.stdout.strip()

try:
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=CHROME)
        ctx = nav.new_context(viewport={"width": 1440, "height": 900})
        externes = []
        page = ctx.new_page()
        page.on("request", lambda r: externes.append(r.url) if not r.url.startswith(BASE) else None)
        erreurs = []
        page.on("console", lambda m: erreurs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: erreurs.append(str(e)))

        # --- se connecter, comme Mala
        page.goto(BASE + "/wp-login.php", wait_until="domcontentloaded")
        page.fill("#user_login", "mala")
        page.fill("#user_pass", "motdepasse")
        page.click("#wp-submit")
        page.wait_for_load_state("domcontentloaded")
        dit("la connexion à WordPress passe", "/wp-admin" in page.url, page.url.replace(BASE, ""))

        # --- le menu
        dit("le menu « CRM Soha » est là",
            page.locator("#adminmenu a:has-text('CRM Soha')").count() > 0)

        # --- l'écran du CRM
        page.goto(BASE + "/wp-admin/admin.php?page=soha-crm", wait_until="networkidle")
        page.wait_for_timeout(1800)
        racine = page.locator("#soha-crm-racine")
        dit("l'interface se monte dans l'administration", racine.locator("*").count() > 20,
            "%d nœuds" % racine.locator("*").count())
        dit("le menu de WordPress reste visible à côté", page.locator("#adminmenu").is_visible())
        dit("la phrase de stockage dit vrai",
            "base du site" in racine.inner_text(),
            [l for l in racine.inner_text().split("\n") if "Données gardées" in l][:1])

        # --- un contact, pour de vrai
        page.get_by_role("button", name="Répertoire").first.click()
        page.wait_for_timeout(400)
        page.get_by_role("button", name="+ Nouveau contact").first.click()
        page.wait_for_timeout(300)
        page.get_by_label("Nom").first.fill("Rosalie Gagné")
        page.get_by_label("Courriel").first.fill("rosalie@exemple.test")
        page.get_by_role("button", name="Enregistrer").first.click()
        page.wait_for_timeout(2000)

        brut = en_base('$e=get_option("soha_crm_etat","");echo $e;')
        reg = json.loads(brut) if brut else {}
        noms = [c.get("nom") for c in reg.get("contacts", [])]
        dit("le contact est écrit dans la base de WordPress", "Rosalie Gagné" in noms,
            "%d contacts" % len(noms))
        dit("la révision a avancé", int(en_base('echo (int) get_option("soha_crm_revision",0);')) > 0,
            "revision=" + en_base('echo (int) get_option("soha_crm_revision",0);'))

        # --- rechargement : la seule preuve qui compte
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1800)
        page.get_by_role("button", name="Répertoire").first.click()
        page.wait_for_timeout(500)
        dit("il est encore là après rechargement", "Rosalie Gagné" in racine.inner_text())

        # --- une demande de location arrive du site, comme en vrai
        en_base(r"""
          class Faux { private $c; private $r;
            function __construct($c,$n){$this->c=$c;$this->r=array("form_name"=>$n);}
            function get($q){return "fields"===$q?$this->c:("form_settings"===$q?$this->r:null);} }
          do_action("elementor_pro/forms/new_record", new Faux(array(
            "nom"=>array("title"=>"Nom complet","type"=>"text","value"=>"Léa Bouchard"),
            "courriel"=>array("title"=>"Courriel","type"=>"email","value"=>"lea@exemple.test"),
            "espace"=>array("title"=>"Espace","type"=>"select","value"=>"Espace SÖHA (2200 pi²)"),
            "date"=>array("title"=>"Date souhaitée","type"=>"date","value"=>"2026-10-17"),
            "plage"=>array("title"=>"Plage horaire","type"=>"radio","value"=>"Demi-journée"),
            "estim_tarif"=>array("title"=>"Estimation — tarif affiché","type"=>"hidden","value"=>"400 $ +tx"),
          ), "Demande de location"), null);
          echo "ok";
        """)

        # --- l'écran des demandes
        page.goto(BASE + "/wp-admin/admin.php?page=soha-crm-demandes", wait_until="domcontentloaded")
        dit("l'écran des demandes s'ouvre", "Demandes reçues" in page.locator(".wrap h1").inner_text())
        dit("il annonce la conservation", "24 mois" in page.locator(".wrap").inner_text())
        dit("la demande arrivée du site y est", "lea@exemple.test" in page.locator(".wrap").inner_text())
        dit("le menu porte la pastille de ce qui attend",
            page.locator("#adminmenu .update-plugins").count() > 0)

        # --- un clic, et elle devient fiche + réservation
        page.get_by_role("button", name="Verser au répertoire").first.click()
        page.wait_for_load_state("domcontentloaded")
        avis = page.locator(".notice").first.inner_text()
        dit("l'avis annonce la fiche et la réservation",
            "Fiche créée" in avis and "devis" in avis, avis.strip()[:96])

        reg = json.loads(en_base('echo (string) get_option("soha_crm_etat","");') or "{}")
        r = (reg.get("reservations") or [{}])[0]
        dit("la réservation est en base, au bon espace et au bon prix",
            r.get("espace") == "Espace SÖHA" and r.get("prix") == "400"
            and r.get("date") == "2026-10-17" and r.get("paiement") == "devis",
            json.dumps({k: r.get(k) for k in ("espace", "date", "prix", "paiement")}, ensure_ascii=False))

        # --- et l'onglet Location du CRM la montre
        page.goto(BASE + "/wp-admin/admin.php?page=soha-crm", wait_until="networkidle")
        page.wait_for_timeout(1800)
        page.get_by_role("button", name="Location").first.click()
        page.wait_for_timeout(600)
        texte = racine.inner_text()
        dit("l'onglet Location du CRM l'affiche",
            "Espace SÖHA" in texte and "Léa Bouchard" in texte)
        dit("le CRM ne propose plus « Grande salle »", "Grande salle" not in texte)

        # --- la sauvegarde se télécharge
        page.goto(BASE + "/wp-admin/admin.php?page=soha-crm-sauvegarde", wait_until="domcontentloaded")
        with page.expect_download() as d:
            page.get_by_role("link", name="Télécharger la sauvegarde (JSON)").click()
        fichier = d.value
        contenu = json.load(open(fichier.path()))
        dit("le fichier de sauvegarde est complet",
            contenu.get("quoi", "").startswith("Centre Soha")
            and len(contenu["registre"]["reservations"]) >= 1
            and len(contenu["registre"]["contacts"]) >= 1,
            "%d fiches · %d réservations" % (len(contenu["registre"]["contacts"]),
                                             len(contenu["registre"]["reservations"])))

        # --- l'écran de l'infolettre
        #     Non branché : pas de faux Mailchimp ici, le navigateur parle au
        #     vrai PHP. On vérifie donc ce qui ne demande aucun réseau — et
        #     c'est justement le plus important : l'avertissement Loi 25.
        page.goto(BASE + "/wp-admin/admin.php?page=soha-crm-infolettre", wait_until="domcontentloaded")
        texte_info = page.locator(".wrap").inner_text()
        dit("l'écran de l'infolettre s'ouvre", "Infolettre" in page.locator(".wrap h1").inner_text())
        dit("il prévient que Mailchimp est américain",
            "Intuit" in texte_info and "États-Unis" in texte_info)
        dit("le paragraphe pour la politique est prêt à copier",
            "demeure au Québec" in page.locator("#soha-para").input_value())
        dit("la clé se saisit sans jamais s'afficher",
            page.locator("#cle").get_attribute("type") == "password")

        # --- l'écran des accès
        page.goto(BASE + "/wp-admin/admin.php?page=soha-crm-acces", wait_until="domcontentloaded")
        dit("l'écran des accès s'ouvre", "Qui a accès" in page.locator(".wrap h1").inner_text())
        dit("Mala y est cochée et verrouillée",
            page.locator("input[name='acces[]'][disabled]").count() >= 1)

        # --- rien ne part dehors
        #
        # Deux sources à distinguer, sinon la mesure ment. Gravatar est appelé
        # par WordPress lui-même pour les avatars de la barre d'administration :
        # ce n'est pas l'extension, et c'est une case à décocher dans Réglages →
        # Discussion si le centre le souhaite. `blob:` est interne à la page.
        dehors = [u for u in externes
                  if not u.startswith("data:") and not u.startswith("blob:")]
        gravatar = [u for u in dehors if "gravatar.com" in u]
        a_nous = [u for u in dehors if "gravatar.com" not in u]
        dit("l'extension n'appelle rien dehors", len(a_nous) == 0, a_nous[:3])
        dit("le seul appel externe vient de WordPress (avatars)",
            len(gravatar) == len(dehors),
            "%d appel(s) à secure.gravatar.com — Réglages → Discussion" % len(gravatar))

        vraies = [e for e in erreurs if "Failed to load resource" not in e]
        dit("aucune erreur JavaScript", len(vraies) == 0, vraies[:2])

        nav.close()
finally:
    serveur.terminate()

print("\n" + "─" * 72)
print("%d réussites, %d échecs" % (ok, ko))
sys.exit(1 if ko else 0)
