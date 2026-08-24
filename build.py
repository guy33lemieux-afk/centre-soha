#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur du Centre Soha — version « à plat » (aucun dossier à monter à la main).

Lit deux fichiers simples que l'éditeur modifie :
  - cours.json    : la liste des cours de la semaine
  - accueil.json  : les textes/photo d'en-tête de l'accueil
et fabrique le dossier `site/` (la page + l'éditeur /admin) dans la charte Soha.

L'éditeur (Sveltia CMS) et sa configuration sont écrits automatiquement dans
site/admin/ — il n'y a donc AUCUN dossier à créer soi-même dans GitHub.

Usage : python3 build.py
Aucune dépendance externe.
"""

import os, json, glob, html, shutil

RACINE = os.path.dirname(os.path.abspath(__file__))
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
REPO = "guy33lemieux-afk/centre-soha"   # ton dépôt GitHub

# ---------- lecture du contenu ----------
def charger_json(nom, defaut):
    chemin = os.path.join(RACINE, nom)
    if os.path.exists(chemin):
        try:
            return json.load(open(chemin, encoding="utf-8"))
        except Exception as e:
            print("  ! lecture de", nom, ":", e)
    return defaut

def cle_tri(c):
    try: j = JOURS.index(c.get("jour", ""))
    except ValueError: j = 99
    try: o = int(c.get("ordre", 99))
    except (TypeError, ValueError): o = 99
    return (j, o, c.get("titre", ""))

def paragraphes(texte):
    blocs = [b.strip() for b in (texte or "").split("\n") if b.strip()]
    return "".join("<p>{}</p>".format(html.escape(b)) for b in blocs)

# ---------- rendu d'une carte de cours ----------
def carte(c):
    titre = html.escape(c.get("titre", ""))
    jour = html.escape(c.get("jour", ""))
    heure = html.escape(c.get("heure", ""))
    form = (c.get("formateur") or "").strip()
    meta = (("Avec " + html.escape(form) + "  ·  ") if form else "") + jour + " · " + heure
    photo = (c.get("photo") or "").strip()
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
    </article>""".format(ph=ph, titre=titre, meta=meta, desc=paragraphes(c.get("description", "")))

# ---------- gabarit de la page publique ----------
PAGE = """<!DOCTYPE html>
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
  <p class="note">Page fabriquée automatiquement à partir de tes fichiers ({n} cours). Modifie un cours dans l'éditeur, et cette page se met à jour.</p>
</body>
</html>
"""

# ---------- l'éditeur (Sveltia CMS) — écrit dans site/admin/ ----------
ADMIN_INDEX = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Éditeur — Centre Soha</title>
  <link href="/admin/config.yml" type="text/yaml" rel="cms-config-url">
</head>
<body>
  <script src="https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js" type="module"></script>
</body>
</html>
"""

ADMIN_CONFIG = """# Configuration de l'éditeur du Centre Soha (Sveltia CMS)
# Générée automatiquement par build.py — ne pas modifier à la main.
backend:
  name: github
  repo: {repo}
  branch: main
media_folder: "images"     # les photos téléversées sont créées dans /images (le dossier se crée tout seul)
public_folder: "/images"
locale: "fr"
collections:
  - name: "cours"
    label: "Cours de la semaine"
    description: "Ajoute, modifie ou retire un cours. Change la date, l'heure, la photo."
    files:
      - name: "liste"
        label: "La semaine"
        file: "cours.json"
        fields:
          - label: "Cours"
            name: "cours"
            widget: "list"
            label_singular: "Cours"
            summary: "{{{{fields.jour}}}} {{{{fields.heure}}}} — {{{{fields.titre}}}}"
            fields:
              - {{ label: "Titre", name: "titre", widget: "string" }}
              - {{ label: "Formateur·rice", name: "formateur", widget: "string", required: false }}
              - {{ label: "Jour", name: "jour", widget: "select",
                   options: ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"] }}
              - {{ label: "Heure", name: "heure", widget: "string", hint: "ex. 18 h 30" }}
              - {{ label: "Ordre d'affichage", name: "ordre", widget: "number", required: false, default: 99 }}
              - {{ label: "Photo", name: "photo", widget: "image", required: false, hint: "Glisse une image depuis ton ordi" }}
              - {{ label: "Description", name: "description", widget: "text" }}
  - name: "accueil"
    label: "Page d'accueil"
    description: "Le titre, le sous-titre et la photo d'en-tête."
    files:
      - name: "textes"
        label: "En-tête de l'accueil"
        file: "accueil.json"
        fields:
          - {{ label: "Titre d'en-tête", name: "hero_titre", widget: "string" }}
          - {{ label: "Sous-titre", name: "hero_soustitre", widget: "string" }}
          - {{ label: "Photo d'en-tête", name: "hero_photo", widget: "image", required: false }}
          - {{ label: "Bande de faits", name: "bande_faits", widget: "string" }}
"""

def main():
    cours_data = charger_json("cours.json", {"cours": []})
    cours = sorted(cours_data.get("cours", []), key=cle_tri)
    accueil = charger_json("accueil.json", {})

    page = PAGE.format(
        titre_page="Se ressourcer",
        hero_titre=html.escape(accueil.get("hero_titre", "Les cours de la semaine")),
        hero_soustitre=html.escape(accueil.get("hero_soustitre", "")),
        faits=html.escape(accueil.get("bande_faits", "")),
        cartes="\n".join(carte(c) for c in cours),
        n=len(cours),
    )

    sortie = os.path.join(RACINE, "site")
    os.makedirs(os.path.join(sortie, "admin"), exist_ok=True)
    with open(os.path.join(sortie, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(sortie, "admin", "index.html"), "w", encoding="utf-8") as f:
        f.write(ADMIN_INDEX)
    with open(os.path.join(sortie, "admin", "config.yml"), "w", encoding="utf-8") as f:
        f.write(ADMIN_CONFIG.format(repo=REPO))

    # recopie les photos (dossier images/, créé par l'éditeur au 1er téléversement)
    src_img = os.path.join(RACINE, "images")
    if os.path.isdir(src_img):
        dst_img = os.path.join(sortie, "images")
        if os.path.isdir(dst_img):
            shutil.rmtree(dst_img)
        shutil.copytree(src_img, dst_img)

    print("OK — {} cours rendus".format(len(cours)))
    print("     site/index.html   (la page)")
    print("     site/admin/       (l'éditeur)")
    for c in cours:
        print("   ·", c.get("jour"), c.get("heure"), "—", c.get("titre"))

if __name__ == "__main__":
    main()
