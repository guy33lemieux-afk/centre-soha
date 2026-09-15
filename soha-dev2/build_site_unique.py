#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — le site entier dans un seul fichier HTML, cliquable.

Pourquoi
--------
Le dossier livré marche, mais il faut le décompresser, trouver `index.html`,
double-cliquer. On ne l'envoie pas à quelqu'un « pour voir ». Ici, tout tient
dans un fichier : les vingt-neuf pages, les soixante-quatorze images, les
douze polices. Une adresse, et on clique dedans comme dans un vrai site.

Comment
-------
L'en-tête et le pied sont **identiques** sur les vingt-neuf pages (vérifié, pas
supposé : le script s'arrête si ce n'est plus vrai). On les garde donc une fois,
et on empile les `<main>` les uns sous les autres, tous cachés sauf un. Un clic
sur un lien interne montre la vue voulue et écrit `#/page.html` dans l'adresse —
donc le bouton « retour » du navigateur fonctionne, et un lien vers une page
précise se partage.

Ce que le script refuse de deviner
----------------------------------
Rien n'est réécrit au-delà de ce qu'il faut pour que les pages cohabitent :
- Les identifiants **en double** entre les pages (`courriel`, `consentement`…)
  sont préfixés, et leurs références avec eux (`for`, `aria-controls`…). Sans
  ça, cliquer une étiquette de formulaire activerait le champ d'une page cachée.
- Les identifiants **uniques** ne sont pas touchés : deux scripts de page
  cherchent `#sohaEstim` et `#soha-semaine` par leur nom. Les renommer les
  casserait en silence.

Usage
-----
    python3 build_site_unique.py --site <dossier> --sortie site-unique.html
    python3 build_site_unique.py --site <dossier> --sortie frag.html --artefact
"""

import argparse
import base64
import collections
import html
import mimetypes
import os
import re
import sys

ACCUEIL = "index.html"
HORS_SITE = ("lisez-moi.html",)          # le sommaire du dossier n'est pas une page


# --------------------------------------------------------------------------
#  Lecture
# --------------------------------------------------------------------------

def lire(chemin):
    return open(chemin, encoding="utf-8").read()


def decouper(texte, nom):
    """Sépare une page en ses morceaux. Une absence est une erreur, pas un vide."""
    def prendre(motif, quoi):
        m = re.search(motif, texte, re.S)
        if not m:
            raise SystemExit("%s : %s introuvable." % (nom, quoi))
        return m.group(0)

    titre = re.search(r"<title>(.*?)</title>", texte, re.S)
    descr = re.search(r'<meta name="description" content="([^"]*)"', texte)
    corps = re.search(r'<body class="([^"]*)"', texte)

    return {
        "titre": (titre.group(1).strip() if titre else ""),
        "description": (descr.group(1) if descr else ""),
        "classe": (corps.group(1) if corps else "soha-page"),
        "entete": prendre(r'<header class="soha-entete">.*?</header>', "l'en-tête"),
        "main": prendre(r"<main\b.*?</main>", "le contenu principal"),
        "pied": prendre(r'<footer class="soha-pied">.*?</footer>', "le pied"),
        "scripts": re.findall(r"<script>(.*?)</script>", texte, re.S),
    }


# --------------------------------------------------------------------------
#  Les fichiers embarqués
# --------------------------------------------------------------------------

def data_uri(chemin):
    type_, _ = mimetypes.guess_type(chemin)
    if not type_:
        type_ = "font/woff2" if chemin.endswith(".woff2") else "application/octet-stream"
    brut = open(chemin, "rb").read()
    return "data:%s;base64,%s" % (type_, base64.b64encode(brut).decode("ascii"))


class Coffre:
    """Les binaires du site, encodés une seule fois même s'ils servent dix fois."""

    def __init__(self, site):
        self.site = site
        self.cache = {}
        self.manquants = collections.Counter()

    def uri(self, relatif):
        relatif = relatif.split("?")[0].split("#")[0]
        if relatif in self.cache:
            return self.cache[relatif]
        chemin = os.path.join(self.site, relatif)
        if not os.path.isfile(chemin):
            self.manquants[relatif] += 1
            return relatif
        u = data_uri(chemin)
        self.cache[relatif] = u
        return u


def embarquer_css(css, coffre):
    """`url(polices/x.woff2)` et `url(../medias/x.webp)` → le fichier lui-même."""
    def un(m):
        brut = m.group(1).strip().strip('"\'')
        if brut.startswith(("data:", "http://", "https://")):
            return m.group(0)
        relatif = brut
        if relatif.startswith("../"):
            relatif = relatif[3:]                   # la feuille vit dans assets/
        elif not relatif.startswith(("medias/", "assets/")):
            relatif = "assets/" + relatif           # polices/x.woff2
        return "url(%s)" % coffre.uri(relatif)
    return re.sub(r"url\(([^)]+)\)", un, css)


def embarquer_html(frag, coffre):
    """Les `src` et `href` qui pointent vers `medias/` deviennent le fichier.

    Le `srcset`, lui, est RETIRÉ, pas embarqué. Mala a ouvert le fichier et
    a vu des images cassées partout : le navigateur choisit un candidat du
    `srcset` — un chemin relatif vers un fichier qui n'existe pas à côté du
    document — et ignore le `src` embarqué. Emballer cinq échelons par photo
    en base64 quintuplerait le poids pour rien : dans un fichier unique, la
    seule version qui compte est celle qu'on a sous la main.
    """
    frag = re.sub(r'\s(?:srcset|sizes|imagesrcset|imagesizes)="[^"]*"', "", frag)
    def attribut(m):
        return '%s="%s"' % (m.group(1), coffre.uri(m.group(2)))
    return re.sub(r'\b(src|href|content)="(medias/[^"]+)"', attribut, frag)


# --------------------------------------------------------------------------
#  Les identifiants qui se marchent dessus
# --------------------------------------------------------------------------

REFERENCES = ("for", "aria-controls", "aria-labelledby", "aria-describedby", "list", "form")


def identifiants(frag):
    return set(re.findall(r'\sid="([^"]+)"', frag))


def prefixer(frag, prefixe, a_prefixer):
    """Renomme les identifiants en double d'une vue, et ce qui les désigne.

    Vingt-neuf formulaires portaient tous un champ `courriel`. Dans un seul
    document, `<label for="courriel">` en désigne un seul — celui de la première
    page, cachée. On clique l'étiquette, rien ne se passe, et personne ne
    comprend pourquoi.
    """
    if not a_prefixer:
        return frag

    def neuf(i):
        return prefixe + "-" + i

    def un_id(m):
        i = m.group(1)
        return ' id="%s"' % (neuf(i) if i in a_prefixer else i)
    frag = re.sub(r'\sid="([^"]+)"', un_id, frag)

    for attr in REFERENCES:
        def une_ref(m, attr=attr):
            valeurs = m.group(1).split()
            return ' %s="%s"' % (attr, " ".join(
                neuf(v) if v in a_prefixer else v for v in valeurs))
        frag = re.sub(r'\s%s="([^"]+)"' % attr, une_ref, frag)

    def une_ancre(m):
        i = m.group(1)
        return ' href="#%s"' % (neuf(i) if i in a_prefixer else i)
    frag = re.sub(r'\shref="#([^"]+)"', une_ancre, frag)

    return frag


# --------------------------------------------------------------------------
#  Le routeur
# --------------------------------------------------------------------------

ROUTEUR = r"""
/* Le routeur : vingt-neuf vues empilées, une seule visible.
   Pas de bibliothèque — un clic, une vue, une adresse. */
(function () {
  "use strict";
  var boite = document.getElementById("soha-vues");
  if (!boite) return;
  var vues = {};
  Array.prototype.forEach.call(boite.children, function (v) { vues[v.getAttribute("data-f")] = v; });

  var TITRES = window.SOHA_TITRES || {};
  var courante = "";

  function fermerLeMenu() {
    var m = document.querySelector(".soha-menu");
    if (!m) return;
    m.removeAttribute("data-ouvert");
    var b = m.querySelector(".soha-bascule");
    if (b) b.setAttribute("aria-expanded", "false");
  }

  function montrer(f, ancre) {
    if (!vues[f]) f = "index.html";
    if (f !== courante) {
      for (var n in vues) { if (vues.hasOwnProperty(n)) vues[n].hidden = (n !== f); }
      courante = f;
      var cls = vues[f].getAttribute("data-classe");
      if (cls) document.body.className = cls;
      if (TITRES[f]) document.title = TITRES[f];
    }
    fermerLeMenu();
    /* L'ancre est cherchée DANS la vue : le même identifiant peut exister
       ailleurs, et `getElementById` ne connaît pas les vues. */
    var cible = ancre ? vues[f].querySelector("#" + (window.CSS && CSS.escape ? CSS.escape(ancre) : ancre)) : null;
    if (cible) { cible.scrollIntoView({ block: "start" }); }
    else { window.scrollTo(0, 0); }
  }

  function depuisLAdresse() {
    var h = (location.hash || "").replace(/^#\/?/, "");
    if (!h) return montrer("index.html", "");
    var bouts = h.split("#");
    montrer(bouts[0].split("?")[0] || "index.html", bouts[1] || "");
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    if (a.getAttribute("target")) return;
    var h = a.getAttribute("href") || "";
    if (/^(https?:|mailto:|tel:|data:|blob:)/i.test(h)) return;

    if (h.charAt(0) === "#") {           /* une ancre dans la page courante */
      var id = h.slice(1);
      if (!id) return;
      var dans = vues[courante] && vues[courante].querySelector(
        "#" + (window.CSS && CSS.escape ? CSS.escape(id) : id));
      if (!dans) return;
      e.preventDefault();
      dans.scrollIntoView({ block: "start" });
      if (dans.focus) { dans.setAttribute("tabindex", "-1"); dans.focus({ preventScroll: true }); }
      return;
    }

    var fichier = h.split("#")[0].split("?")[0];
    if (!/\.html$/i.test(fichier)) return;
    e.preventDefault();
    var ancre = h.indexOf("#") >= 0 ? h.split("#")[1] : "";
    location.hash = "#/" + fichier + (ancre ? "#" + ancre : "");
    depuisLAdresse();                    /* si le hash n'a pas changé, rien ne se déclenche */
  });

  window.addEventListener("hashchange", depuisLAdresse);
  depuisLAdresse();
})();
"""

STYLE_VUES = """
/* Les vues : une seule visible. `!important` parce que les conteneurs
   Elementor posent leur propre `display` et gagneraient sur `[hidden]`. */
#soha-vues > .vue[hidden]{display:none !important}
"""


# --------------------------------------------------------------------------
#  L'assemblage
# --------------------------------------------------------------------------

def construire(site, artefact=False, titre=None):
    fichiers = sorted(f for f in os.listdir(site)
                      if f.endswith(".html") and f not in HORS_SITE)
    if ACCUEIL not in fichiers:
        raise SystemExit("Pas d'%s dans %s." % (ACCUEIL, site))

    morceaux = collections.OrderedDict()
    for f in fichiers:
        morceaux[f] = decouper(lire(os.path.join(site, f)), f)

    # L'en-tête et le pied ne sont gardés qu'une fois : on vérifie qu'ils sont
    # bien les mêmes partout, plutôt que de le croire.
    entetes = {m["entete"] for m in morceaux.values()}
    pieds = {m["pied"] for m in morceaux.values()}
    if len(entetes) != 1:
        raise SystemExit("Les en-têtes diffèrent d'une page à l'autre (%d formes)." % len(entetes))
    if len(pieds) != 1:
        raise SystemExit("Les pieds diffèrent d'une page à l'autre (%d formes)." % len(pieds))

    # Les identifiants présents dans plus d'une page : eux seuls sont préfixés.
    compte = collections.Counter()
    for m in morceaux.values():
        for i in identifiants(m["main"]):
            compte[i] += 1
    doublons = {i for i, n in compte.items() if n > 1}

    coffre = Coffre(site)
    entete = embarquer_html(next(iter(entetes)), coffre)
    pied = embarquer_html(next(iter(pieds)), coffre)

    vues, titres, scripts = [], [], []
    for f, m in morceaux.items():
        slug = re.sub(r"[^a-z0-9]+", "-", f[:-5].lower()).strip("-")
        main = prefixer(m["main"], slug, doublons)
        main = embarquer_html(main, coffre)
        # `id="soha-contenu"` est sur chaque <main> : le lien d'évitement de
        # l'en-tête n'en désignerait qu'un. Il vit maintenant sur le conteneur.
        main = re.sub(r'^<main\b([^>]*)\sid="[^"]*"', r"<main\1", main)
        vues.append('<div class="vue" data-f="%s" data-classe="%s"%s>%s</div>'
                    % (html.escape(f, quote=True), html.escape(m["classe"], quote=True),
                       "" if f == ACCUEIL else " hidden", main))
        titres.append('"%s":"%s"' % (f, m["titre"].replace('"', '\\"')))
        for sc in m["scripts"]:
            scripts.append(sc)

    css = embarquer_css(lire(os.path.join(site, "assets/soha.css")), coffre)
    js = lire(os.path.join(site, "assets/soha.js"))

    if coffre.manquants:
        for n, c in coffre.manquants.most_common():
            print("  FICHIER ABSENT : %s (×%d)" % (n, c), file=sys.stderr)
        raise SystemExit("%d fichier(s) référencé(s) mais absent(s)." % len(coffre.manquants))

    titre_accueil = titre or morceaux[ACCUEIL]["titre"]
    tete = (
        "<title>%s</title>\n" % html.escape(titre_accueil)
        + '<meta name="description" content="%s">\n' % html.escape(morceaux[ACCUEIL]["description"])
        + "<style>\n%s\n%s</style>\n" % (css, STYLE_VUES)
    )

    corps = (
        '<a class="soha-saut" href="#soha-contenu">Aller au contenu</a>\n'
        + entete + "\n"
        + '<div id="soha-contenu">\n<div id="soha-vues">\n'
        + "\n".join(vues)
        + "\n</div>\n</div>\n"
        + pied + "\n"
        + "<script>window.SOHA_TITRES={%s};</script>\n" % ",".join(titres)
        + "".join("<script>%s</script>\n" % sc for sc in scripts)
        + "<script>%s</script>\n" % js
        + "<script>%s</script>\n" % ROUTEUR
    )

    if artefact:
        doc = tete + corps
    else:
        doc = ('<!DOCTYPE html>\n<html lang="fr">\n<head>\n'
               '<meta charset="utf-8">\n'
               '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
               '<meta name="robots" content="noindex, nofollow">\n'
               + tete
               + '</head>\n<body class="%s">\n' % html.escape(morceaux[ACCUEIL]["classe"], quote=True)
               + corps + "</body>\n</html>\n")

    return doc, {
        "pages": len(fichiers),
        "fichiers_embarques": len(coffre.cache),
        "ids_prefixes": len(doublons),
        "scripts_de_page": len(scripts),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Le site du Centre Soha en un seul fichier HTML cliquable.")
    ap.add_argument("--site", required=True, help="dossier du site statique")
    ap.add_argument("--sortie", required=True, help="fichier HTML à écrire")
    ap.add_argument("--artefact", action="store_true",
                    help="sans <html>/<head>/<body> : pour publier en artefact")
    ap.add_argument("--titre", default=None,
                    help="titre de l'onglet au chargement (défaut : celui de l'accueil)")
    a = ap.parse_args()

    doc, bilan = construire(a.site, a.artefact, a.titre)
    open(a.sortie, "w", encoding="utf-8").write(doc)

    print("Écrit dans « %s »" % a.sortie)
    print("  pages réunies       : %d" % bilan["pages"])
    print("  fichiers embarqués  : %d" % bilan["fichiers_embarques"])
    print("  identifiants préfixés : %d" % bilan["ids_prefixes"])
    print("  scripts de page     : %d" % bilan["scripts_de_page"])
    print("  poids               : %.2f Mo" % (os.path.getsize(a.sortie) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
