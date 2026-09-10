#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la feuille de maison.

Prend les documents de travail écrits en Markdown et les rend en HTML dans le
canon Soha : Fraunces pour les titres, Schibsted Grotesk pour le corps, DM Mono
pour les données, palette v06, sombre et clair.

Le constat qui a motivé cet outil : quatre documents de la maison — l'index du
dossier, les métas SEO, les réseaux sociaux, le livre de bord — étaient composés
en Inter. Une maison qui écrit sa charte dans une police qui n'est pas la sienne
se contredit à chaque page. Un seul style, appliqué par un seul outil, règle ça
une fois pour toutes.

Usage :
    python3 build_documents.py --entree <dossier de .md> --sortie <dossier>

Aucune dépendance externe.
"""

import argparse
import html
import os
import re
import shutil
import sys

# --------------------------------------------------------------------------
#  Le canon v06 — la seule feuille de style de la maison
# --------------------------------------------------------------------------
FEUILLE = """/* ============================================================
   Centre Soha — feuille de maison des documents · v01
   Canon v06 : encre #0E1A15 · ivoire #F4F0E7
   Accents par école : Soigner #19A7DB · Bâtir #D29A4E · Cultiver #5E8C5A
   Fraunces (titres) · Schibsted Grotesk (corps) · DM Mono (données)
   ============================================================ */
:root{
  --encre:#0E1A15; --ivoire:#F4F0E7; --papier:#FBF8F3;
  --soigner:#19A7DB; --batir:#D29A4E; --cultiver:#5E8C5A; --cramoisi:#AE1E3B;

  --fond:var(--papier); --surface:#FFFFFF; --surface-2:#F1EBE1;
  --texte:var(--encre); --doux:#5A6862;
  --filet:#E2DACC; --filet-fort:#C7BCA8;
  --accent:#0F7FA6;

  --serif:"Fraunces",Georgia,"Times New Roman",serif;
  --sans:"Schibsted Grotesk",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"DM Mono",ui-monospace,"SF Mono",Menlo,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --fond:#0A1310; --surface:#121D19; --surface-2:#1A2823;
    --texte:#EDE7DB; --doux:#9BA9A2; --filet:#293832; --filet-fort:#3B4F47;
    --accent:#63C8E6;
  }
}
:root[data-theme="dark"]{
  --fond:#0A1310; --surface:#121D19; --surface-2:#1A2823;
  --texte:#EDE7DB; --doux:#9BA9A2; --filet:#293832; --filet-fort:#3B4F47;
  --accent:#63C8E6;
}

*{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--texte);font-family:var(--sans);
  font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}
.doc{max-width:860px;margin:0 auto;padding-inline:20px;padding-block:44px 92px}

h1,h2,h3,h4{font-family:var(--serif);font-weight:500;text-wrap:balance;margin:0}
h1{font-size:clamp(2.1rem,5.6vw,3.2rem);line-height:1.03;letter-spacing:-.018em;
  margin-bottom:14px}
h2{font-size:clamp(1.35rem,3.1vw,1.9rem);line-height:1.13;letter-spacing:-.008em;
  margin:52px 0 0;padding-bottom:10px;border-bottom:1px solid var(--filet)}
h3{font-family:var(--sans);font-weight:600;font-size:1.04rem;line-height:1.25;
  margin:32px 0 0}
h4{font-family:var(--mono);font-weight:500;font-size:.72rem;letter-spacing:.13em;
  text-transform:uppercase;color:var(--doux);margin:26px 0 0}
h2+p,h3+p,h4+p{margin-top:12px}

p{margin:0 0 1em;max-width:68ch}
a{color:var(--accent);text-underline-offset:3px}
:focus-visible{outline:2px solid var(--soigner);outline-offset:3px}
strong{font-weight:600}
em{font-style:italic}
hr{border:0;border-top:1px solid var(--filet);margin:44px 0}

code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);
  padding:.1em .38em;border-radius:2px;overflow-wrap:break-word}
pre{font-family:var(--mono);font-size:.84rem;line-height:1.7;background:var(--surface);
  border:1px solid var(--filet);padding:18px 20px;overflow-x:auto;margin:22px 0}
pre code{background:none;padding:0}

ul,ol{margin:0 0 1em;padding-left:1.3em;max-width:68ch}
li{margin-bottom:.45em}
li>ul,li>ol{margin-top:.45em}

blockquote{margin:22px 0;padding:2px 0 2px 20px;border-left:3px solid var(--batir);
  color:var(--doux)}
blockquote p:last-child{margin-bottom:0}

/* --- tableaux : la donnée est du DM Mono --- */
.tableau{overflow-x:auto;margin:24px 0;border:1px solid var(--filet)}
table{border-collapse:collapse;width:100%;font-size:.93rem}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--filet);
  vertical-align:top}
th{font-family:var(--mono);font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;
  color:var(--doux);font-weight:500;background:var(--surface-2);white-space:nowrap}
tr:last-child td{border-bottom:0}
td code{font-size:.82em}
td:first-child{font-weight:500}

/* --- l'en-tête du document --- */
.entete{border-bottom:1px solid var(--filet-fort);padding-bottom:30px;margin-bottom:8px}
.entete .sceau{display:flex;align-items:center;gap:8px;margin-bottom:18px}
.entete .sceau i{width:9px;height:9px;border-radius:50%;background:var(--soigner)}
.entete .sceau b{width:46px;height:2px;background:var(--batir)}
.entete .sceau u{width:7px;height:7px;border-radius:50%;background:var(--cramoisi)}
.entete .lieu{font-family:var(--mono);font-size:.7rem;letter-spacing:.15em;
  text-transform:uppercase;color:var(--doux);margin:0 0 14px}
.entete .sous{font-family:var(--serif);font-size:clamp(1.1rem,2.4vw,1.42rem);
  font-weight:400;font-style:italic;color:var(--doux);margin:0;max-width:56ch;
  line-height:1.35}

.pied{margin-top:64px;padding-top:20px;border-top:1px solid var(--filet-fort);
  font-size:.86rem;color:var(--doux)}
.pied p{max-width:none;margin-bottom:.4em}

@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

GABARIT = """<!DOCTYPE html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre} — Centre Soha</title>
<meta name="robots" content="noindex, nofollow">
<link rel="stylesheet" href="soha-document.css">
<link rel="preload" as="font" type="font/woff2" crossorigin href="polices/schibsted-grotesk-v7-latin-regular.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin href="polices/fraunces-v38-latin-600.woff2">
</head>
<body>
<article class="doc">
<header class="entete">
  <div class="sceau" aria-hidden="true"><i></i><b></b><u></u></div>
  <p class="lieu">Centre Soha · 961 Rachel Est · Montréal</p>
  <h1>{titre}</h1>
  {sous}
</header>
{corps}
<footer class="pied">
  <p>{nom}</p>
  <p>Document de travail du pôle Centre. Composé dans le canon v06 : Fraunces, Schibsted Grotesk, DM Mono.</p>
</footer>
</article>
</body>
</html>
"""


# --------------------------------------------------------------------------
#  Un rendu Markdown réduit à ce que ces documents utilisent
# --------------------------------------------------------------------------
def en_ligne(t):
    """Gras, italique, code, liens — dans cet ordre, le code d'abord."""
    jetons = []

    def garder(m):
        jetons.append(m.group(1))
        return "\x00%d\x00" % (len(jetons) - 1)

    t = re.sub(r"`([^`]+)`", garder, t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(2)), m.group(1)), t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"\x00(\d+)\x00",
               lambda m: "<code>%s</code>" % html.escape(jetons[int(m.group(1))]), t)
    return t


def rendre(md):
    """Markdown → HTML. Titres, listes, tableaux, citations, code, filets."""
    lignes = md.split("\n")
    sortie = []
    i = 0
    pile = []          # listes ouvertes

    def fermer_listes(jusqu=0):
        while len(pile) > jusqu:
            sortie.append("</%s>" % pile.pop())

    while i < len(lignes):
        l = lignes[i]

        if not l.strip():
            fermer_listes(); i += 1; continue

        # bloc de code
        if l.startswith("```"):
            i += 1
            bloc = []
            while i < len(lignes) and not lignes[i].startswith("```"):
                bloc.append(lignes[i]); i += 1
            i += 1
            fermer_listes()
            sortie.append("<pre><code>%s</code></pre>" % html.escape("\n".join(bloc)))
            continue

        # filet
        if re.match(r"^\s*---\s*$", l):
            fermer_listes(); sortie.append("<hr>"); i += 1; continue

        # tableau
        if l.lstrip().startswith("|") and i + 1 < len(lignes) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lignes[i + 1]):
            fermer_listes()
            def cellules(x):
                return [c.strip() for c in x.strip().strip("|").split("|")]
            entetes = cellules(l)
            i += 2
            corps = []
            while i < len(lignes) and lignes[i].lstrip().startswith("|"):
                corps.append(cellules(lignes[i])); i += 1
            th = "".join("<th>%s</th>" % en_ligne(c) for c in entetes)
            trs = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % en_ligne(c) for c in r)
                          for r in corps)
            sortie.append('<div class="tableau"><table><thead><tr>%s</tr></thead>'
                          '<tbody>%s</tbody></table></div>' % (th, trs))
            continue

        # titre
        m = re.match(r"^(#{1,4})\s+(.*)$", l)
        if m:
            fermer_listes()
            n = len(m.group(1))
            sortie.append("<h%d>%s</h%d>" % (n, en_ligne(m.group(2)), n))
            i += 1; continue

        # citation
        if l.lstrip().startswith(">"):
            fermer_listes()
            bloc = []
            while i < len(lignes) and lignes[i].lstrip().startswith(">"):
                bloc.append(re.sub(r"^\s*>\s?", "", lignes[i])); i += 1
            sortie.append("<blockquote><p>%s</p></blockquote>" % en_ligne(" ".join(bloc)))
            continue

        # listes
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", l)
        if m:
            creux = len(m.group(1))
            genre = "ul" if m.group(2) in ("-", "*") else "ol"
            niveau = creux // 2 + 1
            while len(pile) > niveau:
                sortie.append("</%s>" % pile.pop())
            while len(pile) < niveau:
                sortie.append("<%s>" % genre); pile.append(genre)
            sortie.append("<li>%s</li>" % en_ligne(m.group(3)))
            i += 1; continue

        # paragraphe
        fermer_listes()
        bloc = []
        while i < len(lignes) and lignes[i].strip() and not re.match(
                r"^(#{1,4}\s|\s*[-*]\s|\s*\d+\.\s|\s*>|```|\s*---\s*$|\s*\|)", lignes[i]):
            bloc.append(lignes[i]); i += 1
        sortie.append("<p>%s</p>" % en_ligne(" ".join(bloc)))

    fermer_listes()
    return "\n".join(sortie)


def separer(md):
    """Sort le titre (# …), le sous-titre (## …) et le reste du corps."""
    lignes = md.split("\n")
    titre, sous, debut = "", "", 0
    for j, l in enumerate(lignes[:6]):
        if not titre and l.startswith("# "):
            titre = l[2:].strip(); debut = j + 1
        elif titre and not sous and l.startswith("## "):
            sous = l[3:].strip(); debut = j + 1
        elif titre and l.strip() and not l.startswith("#"):
            break
    return titre, sous, "\n".join(lignes[debut:])


FAMILLES = {"schibsted-grotesk": "Schibsted Grotesk", "fraunces": "Fraunces", "dm-mono": "DM Mono"}


def faces_css(dossier):
    """Les @font-face des trois familles, servies depuis le dossier du document."""
    out = []
    for f in sorted(os.listdir(dossier)):
        if not f.endswith(".woff2"):
            continue
        famille = next((v for k, v in FAMILLES.items() if f.startswith(k)), None)
        if not famille:
            continue
        m = re.search(r"-(\d{3})\.woff2$", f)
        out.append('@font-face{font-family:"%s";font-style:%s;font-weight:%s;'
                   'font-display:swap;src:url("polices/%s") format("woff2")}'
                   % (famille, "italic" if "italic" in f else "normal",
                      m.group(1) if m else "400", f))
    return out


def construire(entree, sortie, polices=None):
    os.makedirs(sortie, exist_ok=True)
    tete = ""
    if polices and os.path.isdir(polices):
        cible = os.path.join(sortie, "polices")
        os.makedirs(cible, exist_ok=True)
        for f in os.listdir(polices):
            if f.endswith(".woff2"):
                shutil.copy2(os.path.join(polices, f), os.path.join(cible, f))
        tete = ("/* Les trois familles du canon, servies depuis la maison.\n"
                "   Aucun appel à Google : exigence Loi 25. */\n"
                + "\n".join(faces_css(cible)) + "\n\n")
    open(os.path.join(sortie, "soha-document.css"), "w", encoding="utf-8").write(tete + FEUILLE)
    faits = []
    for f in sorted(os.listdir(entree)):
        if not f.endswith(".md"):
            continue
        md = open(os.path.join(entree, f), encoding="utf-8").read()
        titre, sous, corps = separer(md)
        nom = re.sub(r"^[0-9a-f]{8}-", "", f)[:-3]
        doc = GABARIT.format(
            titre=html.escape(titre or nom),
            sous=('<p class="sous">%s</p>' % en_ligne(sous)) if sous else "",
            corps=rendre(corps),
            nom=html.escape(nom))
        cible = os.path.join(sortie, nom + ".html")
        open(cible, "w", encoding="utf-8").write(doc)
        faits.append((nom, len(doc)))
    return faits


def main():
    ap = argparse.ArgumentParser(description="Rend les documents Soha dans la feuille de maison.")
    ap.add_argument("--entree", required=True, help="dossier contenant les .md")
    ap.add_argument("--sortie", default="documents", help="dossier de sortie")
    ap.add_argument("--polices", default=None, help="dossier de .woff2 (facultatif)")
    a = ap.parse_args()
    faits = construire(a.entree, a.sortie, a.polices)
    print("Documents composés dans « %s » :" % a.sortie)
    for nom, taille in faits:
        print("   %-52s %5.0f Ko" % (nom + ".html", taille / 1024))
    print("   %-52s %5.0f Ko" % ("soha-document.css", len(FEUILLE) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
