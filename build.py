#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur du Centre Soha — lit les fichiers de contenu (que l'éditeur
modifie) et fabrique les pages du site dans la charte « Le calme habité ».

C'est la pièce qui relie l'éditeur au site : tu changes un cours dans
l'éditeur -> il enregistre un fichier -> ce script refabrique la page.

Usage : python3 build.py
Aucune dépendance externe.
"""

import os, re, glob, html, shutil

RACINE = os.path.dirname(os.path.abspath(__file__))
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# ---------- petit lecteur de "frontmatter" (les champs en haut des .md) ----------
def lire_md(chemin):
    txt = open(chemin, encoding="utf-8").read()
    meta, corps = {}, ""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", txt, re.S)
    if m:
        bloc, corps = m.group(1), m.group(2).strip()
        for ligne in bloc.splitlines():
            if ":" in ligne:
                cle, val = ligne.split(":", 1)
                val = val.strip().strip('"').strip("'")
                meta[cle.strip()] = val
    else:
        corps = txt.strip()
    meta["_corps"] = corps
    return meta

def paragraphes(texte):
    blocs = [b.strip() for b in re.split(r"\n\s*\n", texte) if b.strip()]
    return "".join("<p>{}</p>".format(html.escape(b)) for b in blocs)

# ---------- chargement du contenu ----------
def charger_cours():
    items = []
    for f in glob.glob(os.path.join(RACINE, "content", "cours", "*.md")):
        c = lire_md(f)
        items.append(c)
    def cle(c):
        try: j = JOURS.index(c.get("jour", ""))
        except ValueError: j = 99
        try: o = int(c.get("ordre", 99))
        except (TypeError, ValueError): o = 99
        return (j, o, c.get("titre", ""))
    return sorted(items, key=cle)

def charger_page(nom):
    chemin = os.path.join(RACINE, "content", "pages", nom + ".md")
    return lire_md(chemin) if os.path.exists(chemin) else {}

# ---------- rendu d'une carte de cours (charte du site) ----------
def carte(c):
    titre = html.escape(c.get("titre", ""))
    jour = html.escape(c.get("jour", ""))
    heure = html.escape(c.get("heure", ""))
    form = c.get("formateur", "").strip()
    meta = (("Avec " + html.escape(form) + "  ·  ") if form else "") + jour + " · " + heure
    photo = c.get("photo", "").strip()
    if photo:
        ph = '<div class="ph" style="background-image:url({})"></div>'.format(html.escape(photo))
    else:
        ph = '<div class="ph">🖼️</div>'
    return """    <article class="card">
      {ph}
      <div class="body">
        <span class="chip">Cette semaine</span>
        <h3>{titre}</h3>
        <p class="meta">{meta}</p>
        {desc}
      </div>
    </article>""".format(ph=ph, titre=titre, meta=meta, desc=paragraphes(c.get("_corps", "")))

# ---------- gabarit de page ----------
GABARIT = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre_page} — Centre Soha</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{{--papier:#FBF8F3;--sable:#F2ECE1;--cyan:#046C86;--cyan-vif:#19A7DB;--foret:#16241F;--terre:#B5623C;--radius:8px;
    --serif:"Fraunces",Georgia,serif;--sans:"Inter",system-ui,sans-serif;}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--papier);color:var(--foret);font-family:var(--sans);font-size:17px;line-height:1.6}}
  .wrap{{max-width:1040px;margin:0 auto;padding:0 24px}}
  .hero{{background:var(--foret);color:var(--papier);padding:56px 0 46px}}
  .hero .kicker{{font-weight:600;letter-spacing:.14em;text-transform:uppercase;font-size:12.5px;color:var(--cyan-vif);margin:0 0 12px}}
  .hero h1{{font-family:var(--serif);font-weight:500;font-size:38px;line-height:1.08;margin:0 0 10px}}
  .hero p{{margin:0;color:#DCE7E4;font-size:18px}}
  .hero .faits{{margin-top:16px;font-size:14px;color:#9FD9EA;font-weight:600;letter-spacing:.02em}}
  main{{padding:40px 0 70px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:22px}}
  .card{{background:var(--papier);border-radius:var(--radius);overflow:hidden;border:1px solid #E7DFD1;box-shadow:0 8px 24px rgba(22,36,31,.07)}}
  .card .ph{{height:150px;background-size:cover;background-position:center;background-color:#D9CBB4;display:grid;place-items:center;color:#8A7A5E;font-size:26px}}
  .card .body{{padding:16px 18px}}
  .card .chip{{display:inline-block;background:var(--sable);color:var(--cyan);font-size:11.5px;font-weight:600;padding:3px 10px;border-radius:20px;margin-bottom:9px}}
  .card h3{{font-family:var(--serif);font-weight:500;font-size:20px;margin:0 0 6px;line-height:1.15}}
  .card .meta{{font-size:13px;color:var(--terre);font-weight:600;margin:0 0 8px}}
  .card p{{font-size:14px;color:#4A574F;margin:0 0 8px}}
  .note{{max-width:1040px;margin:26px auto 0;padding:0 24px;color:#7A8983;font-size:13.5px}}
</style>
</head>
<body>
  <header class="hero"><div class="wrap">
    <p class="kicker">Centre Soha — Se ressourcer</p>
    <h1>{hero_titre}</h1>
    <p>{hero_soustitre}</p>
    <p class="faits">{faits}</p>
  </div></header>
  <main><div class="wrap">
    <div class="grid">
{cartes}
    </div>
  </div></main>
  <p class="note">Page fabriquée automatiquement à partir des fichiers de contenu ({n} cours). Modifie un cours dans l'éditeur, relance, et cette page se met à jour.</p>
</body>
</html>
"""

def main():
    cours = charger_cours()
    accueil = charger_page("accueil")
    cartes = "\n".join(carte(c) for c in cours)
    page = GABARIT.format(
        titre_page="Se ressourcer",
        hero_titre=html.escape(accueil.get("hero_titre", "Les cours de la semaine")),
        hero_soustitre=html.escape(accueil.get("hero_soustitre", "")),
        faits=html.escape(accueil.get("bande_faits", "")),
        cartes=cartes,
        n=len(cours),
    )
    sortie = os.path.join(RACINE, "site")
    os.makedirs(sortie, exist_ok=True)
    with open(os.path.join(sortie, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    # Recopie l'éditeur (/admin) et les photos (/media) dans le dossier publié
    for dossier in ("admin", "media"):
        src = os.path.join(RACINE, dossier)
        dst = os.path.join(sortie, dossier)
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    print("OK — {} cours rendus dans site/index.html (+ /admin, /media copiés)".format(len(cours)))
    for c in cours:
        print("   ·", c.get("jour"), c.get("heure"), "—", c.get("titre"))

if __name__ == "__main__":
    main()
