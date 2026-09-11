#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — générateur du site en HTML statique complet.

Lit le kit Elementor (celui qu'on importe dans WordPress) et le kit médias,
et fabrique un site HTML autonome, navigable hors ligne, dans le dossier `site/`.

Le balisage produit reprend les classes réelles d'Elementor (`e-con`,
`elementor-widget-heading`, …) pour que le CSS global du kit — celui qui porte
les titres fluides, les zones sûres et les cibles tactiles — s'applique tel quel.
Ce qui est rendu ici est donc ce que WordPress rendra.

Usage :
    python3 build_site.py --kit <dossier du kit> --medias <dossier du kit médias>

Aucune dépendance externe.
"""

import datetime
import argparse
import html
import json
import os
import re
import shutil
import sys
from collections import Counter, OrderedDict

# --------------------------------------------------------------------------
#  Les fichiers de police : reconnaître la famille, le poids et le style
# --------------------------------------------------------------------------
FAMILLES = {
    "schibsted-grotesk": "Schibsted Grotesk",
    "fraunces": "Fraunces",
    "dm-mono": "DM Mono",
}


def famille_de(nom):
    for prefixe, famille in FAMILLES.items():
        if nom.startswith(prefixe):
            return famille
    return None


def face_css(famille, nom, chemin):
    """Un @font-face par fichier. « regular » vaut 400 ; « italic » sans poids aussi."""
    m = re.search(r"-(\d{3})\.woff2$", nom)
    poids = m.group(1) if m else "400"
    style = "italic" if "italic" in nom else "normal"
    return ('@font-face{font-family:"%s";font-style:%s;font-weight:%s;'
            'font-display:swap;src:url("%s") format("woff2")}'
            % (famille, style, poids, chemin))


# --------------------------------------------------------------------------
#  Les métas SEO rédigées (soha_metas-seo_20260907_v01), page par page.
#  Elles priment sur le titre et l'extrait du kit : c'est le texte travaillé.
#  Confidentialité (7386) et Page introuvable (7388) restent sans méta
#  marketing — elles ne doivent pas être proposées dans les résultats.
# --------------------------------------------------------------------------
METAS = {
    7319: ("Centre Soha — cours, soins et ateliers · Plateau, Montréal",
           "Un lieu vivant au 961 Rachel Est : cours, soins et ateliers, plus des salles "
           "et un studio à louer. Viens voir. Réserve en ligne."),
    7326: ("Se ressourcer au Centre Soha — Plateau Mont-Royal, Montréal",
           "Des pratiques pour souffler et revenir à toi, au 961 Rachel Est. Cours et "
           "ateliers ouverts à tous les niveaux. Réserve ta place."),
    7339: ("Prendre soin — pratiques et présence · Centre Soha, Montréal",
           "Prendre le temps du corps et du souffle, au 961 sur le Plateau. Une pratique, "
           "pas un soin médical. Découvre l'horaire et réserve."),
    7350: ("Se transformer — ateliers et parcours · Centre Soha, Montréal",
           "Des ateliers pour bouger quelque chose en toi, au 961 Rachel Est. Petits "
           "groupes, artisan·es présent·es. Vois les prochaines dates."),
    # La formule « Podcast audio · 200 $ » a été retirée le 10 septembre 2026 :
    # la moins chère qui reste est le podcast filmé, à 300 $.
    7355: ("Studio podcast à louer à Montréal — Centre Soha, dès 300 $",
           "Un studio insonorisé sur le Plateau pour enregistrer ton balado, filmé et "
           "monté. Équipé, calme, dès 300 $. Estime ton prix et réserve en ligne."),
    7373: ("Salle à louer sur le Plateau, Montréal — Centre Soha",
           "Cabinet, grand plateau de 2200 pi² ou studio : loue ton espace au 961, à deux "
           "pas du métro Mont-Royal. Dès 30 $. Estime ton prix."),
    7380: ("Journal du Centre Soha — bien-être, écologie, herboristerie",
           "Nos textes sur le vivant : bien-être, écologie, herboristerie, recettes. "
           "À lire depuis le 961 Rachel Est, sur le Plateau."),
    7382: ("Contact — Centre Soha, 961 Rachel Est, Montréal",
           "Une question, une visite, une location ? Écris-nous ou passe au 961 Rachel "
           "Est, sur le Plateau. On te répond vite."),
    7385: ("Première visite au Centre Soha — tout savoir avant de venir",
           "Comment se passe une première visite au 961 : accès, stationnement, à quoi "
           "t'attendre. Le Plateau t'attend. Réserve ta place."),
    7387: ("Dialogue Authentique — atelier d'introduction · Centre Soha",
           "Un atelier pour parler et écouter autrement, au 961 sur le Plateau. Une "
           "pratique de présence, ouverte à tous. Vois les dates."),
    7389: ("Atelier d'écriture spontanée à Montréal — Centre Soha",
           "Laisser venir les mots sans les juger, en petit groupe au 961 Rachel Est. "
           "Aucune expérience requise. Réserve ta place."),
    7390: ("Core Energetics : cœur et bassin — atelier · Centre Soha",
           "Un atelier de mouvement et de présence au corps, au 961 sur le Plateau. "
           "Une pratique, pas un soin. Découvre les prochaines dates."),
    7391: ("Demander une location — Centre Soha, 961 Rachel Est",
           "Réserve un espace au 961 : cabinet, grand plateau de 2200 pi² ou studio "
           "insonorisé. Dis-nous ta date, on te revient sous 24 h."),
    7392: ("Activation de l'Énergie Sacrée — atelier · Centre Soha",
           "Un atelier pour renouer avec ton énergie, au 961 Rachel Est. Une pratique de "
           "présence, pas un soin. Vois les dates et inscris-toi."),
}

# --------------------------------------------------------------------------
#  Points de rupture — ceux que déclare le kit (viewport_md 768, viewport_lg 1025)
# --------------------------------------------------------------------------
MQ_TABLETTE = "@media (max-width:1024px)"
MQ_TELEPHONE = "@media (max-width:767px)"

# Adresses de pages du kit → fichiers du site statique
def fichier_de_slug(slug):
    return "index.html" if slug in ("", "dev2", "accueil") else slug + ".html"


# --------------------------------------------------------------------------
#  Aides de conversion des réglages Elementor vers du CSS
# --------------------------------------------------------------------------
def longueur(v):
    """{'unit':'px','size':24} → '24px'. Tolère les valeurs vides."""
    if not isinstance(v, dict):
        return None
    t = v.get("size")
    if t in (None, ""):
        return None
    u = v.get("unit") or "px"
    if u == "custom":
        return str(t)
    return "%s%s" % (t, u)


def boite(v):
    """{'top':'10','right':'0',…,'unit':'px'} → '10px 0 0 0'."""
    if not isinstance(v, dict):
        return None
    u = v.get("unit") or "px"
    cotes = []
    for c in ("top", "right", "bottom", "left"):
        x = v.get(c)
        if x in (None, ""):
            x = "0"
        cotes.append("0" if str(x) in ("0", "0.0") else "%s%s" % (x, u))
    if all(c == "0" for c in cotes):
        return "0"
    return " ".join(cotes)


def typographie(s, prefixe, suffixe=""):
    """Traduit un groupe typographique Elementor en déclarations CSS."""
    d = []
    g = lambda k: s.get(prefixe + k + suffixe)
    fam = g("font_family")
    if fam:
        pile = {
            "Fraunces": '"Fraunces",Georgia,"Times New Roman",serif',
            "Schibsted Grotesk": '"Schibsted Grotesk",system-ui,-apple-system,"Segoe UI",sans-serif',
            "DM Mono": '"DM Mono",ui-monospace,"SF Mono",Menlo,monospace',
        }.get(fam, '"%s",system-ui,sans-serif' % fam)
        d.append("font-family:" + pile)
    if g("font_weight"):
        d.append("font-weight:%s" % g("font_weight"))
    if longueur(g("font_size")):
        d.append("font-size:%s" % longueur(g("font_size")))
    if g("text_transform"):
        d.append("text-transform:%s" % g("text_transform"))
    if g("font_style"):
        d.append("font-style:%s" % g("font_style"))
    lh = g("line_height")
    if longueur(lh):
        # Elementor écrit l'interligne en 'em' quand c'est un multiple
        d.append("line-height:%s" % longueur(lh))
    ls = g("letter_spacing")
    if longueur(ls):
        d.append("letter-spacing:%s" % longueur(ls))
    return d


def css_voile(s):
    """Le voile d'Elementor (« background overlay »), entre l'image et le contenu.

    Le kit le déclare sur ses huit héros — `background_overlay_color` à
    `rgba(14,26,21,0.80)` — et le générateur ne le lisait pas. Résultat : sur le
    site HTML, un titre blanc et un paragraphe ivoire posés **nus** sur la photo.
    Mesuré au pixel : 1,04 de contraste là où il en faut 4,5. Les seize textes
    des huit héros étaient sous le seuil, et aucune mesure ne le disait —
    l'image était là, la page s'affichait, rien ne manquait.

    Le défaut n'était pas dans le kit : le site importé dans WordPress, lui,
    a toujours eu son voile.
    """
    if s.get("background_overlay_background") != "classic":
        return []
    couleur = s.get("background_overlay_color")
    if not couleur:
        return []
    decl = ["content:''", "position:absolute", "inset:0", "border-radius:inherit",
            "pointer-events:none", "background-color:%s" % couleur, "z-index:0"]
    op = s.get("background_overlay_opacity")
    if isinstance(op, dict) and op.get("size") not in (None, ""):
        decl.append("opacity:%s" % op["size"])
    return decl


def css_conteneur(s, media=None):
    """Réglages de conteneur → (déclarations base, tablette, téléphone).

    `media` résout une URL d'upload vers le chemin local ; sans lui, une image
    de fond resterait servie par le serveur d'origine — deux d'entre elles
    faisaient encore sortir une requête, mesuré au navigateur."""
    base, tab, tel = [], [], []
    if s.get("flex_direction"):
        base.append("flex-direction:%s" % s["flex_direction"])
    if s.get("flex_direction_tablet"):
        tab.append("flex-direction:%s" % s["flex_direction_tablet"])
    if s.get("flex_direction_mobile"):
        tel.append("flex-direction:%s" % s["flex_direction_mobile"])
    if s.get("flex_justify_content"):
        base.append("justify-content:%s" % s["flex_justify_content"])
    if s.get("flex_justify_content_mobile"):
        tel.append("justify-content:%s" % s["flex_justify_content_mobile"])
    if s.get("flex_align_items"):
        base.append("align-items:%s" % s["flex_align_items"])
    if s.get("flex_wrap"):
        base.append("flex-wrap:%s" % s["flex_wrap"])
    for cle, dest in (("flex_gap", base), ("flex_gap_tablet", tab), ("flex_gap_mobile", tel)):
        g = s.get(cle)
        if isinstance(g, dict):
            col, row = g.get("column"), g.get("row")
            u = g.get("unit") or "px"
            if col not in (None, "") and row not in (None, ""):
                dest.append("gap:%s%s %s%s" % (row, u, col, u))
            elif longueur(g):
                dest.append("gap:%s" % longueur(g))
    for cle, dest in (("width", base), ("width_tablet", tab), ("width_mobile", tel)):
        w = longueur(s.get(cle))
        if w:
            dest.append("width:%s" % w)
            # une largeur figée ne doit jamais dépasser l'écran : mesuré à 768 px
            # sur les pages d'atelier, où un conteneur de 900 px faisait glisser
            # toute la page de côté faute de palier tablette.
            dest.append("max-width:min(%s, 100%%)" % w)
    for cle, dest in (("padding", base), ("padding_tablet", tab), ("padding_mobile", tel)):
        p = boite(s.get(cle))
        if p:
            dest.append("padding:%s" % p)
    m = boite(s.get("_margin"))
    if m:
        base.append("margin:%s" % m)
    mh = longueur(s.get("min_height"))
    if mh:
        base.append("min-height:%s" % mh)
    if s.get("background_background") == "classic":
        if s.get("background_color"):
            base.append("background-color:%s" % s["background_color"])
        bi = s.get("background_image")
        if isinstance(bi, dict) and bi.get("url"):
            # `media` est ici la version « vue depuis la feuille de style » :
            # c'est dans `assets/soha.css` que cette règle atterrit.
            url = media(bi["url"]) if media else bi["url"]
            base.append("background-image:url(%s)" % url)
            base.append("background-position:%s" % (s.get("background_position") or "center center"))
            base.append("background-size:%s" % (s.get("background_size") or "cover"))
            base.append("background-repeat:no-repeat")
    if s.get("border_border"):
        base.append("border-style:%s" % s["border_border"])
        bw = boite(s.get("border_width"))
        if bw:
            base.append("border-width:%s" % bw)
        if s.get("border_color"):
            base.append("border-color:%s" % s["border_color"])
    br = longueur(s.get("border_radius")) or boite(s.get("border_radius"))
    if br:
        base.append("border-radius:%s" % br)
    if s.get("overflow"):
        base.append("overflow:%s" % s["overflow"])
    if s.get("_flex_grow") not in (None, ""):
        base.append("flex-grow:%s" % s["_flex_grow"])
    return base, tab, tel


# --------------------------------------------------------------------------
#  Lecture du kit
# --------------------------------------------------------------------------
def prefixe_du_manifeste(manifest, defaut="/dev"):
    """Le sous-dossier où le site vit, lu dans le manifeste.

    Il était écrit en dur (« /dev2 ») dans la traduction des liens. Le jour où
    le kit est passé à « /dev », la traduction a cessé de reconnaître ses
    propres liens : quatre cent vingt adresses internes sont sorties telles
    quelles, absolues, mortes dès qu'on ouvre le dossier ailleurs que sur
    centresoha.com. Aucune erreur, aucune image manquante — rien à voir tant
    qu'on ne clique pas. On lit donc le préfixe là où il est déclaré.
    """
    m = re.match(r"https?://[^/]+(/[^/]+)/?$", (manifest.get("site") or ""))
    return m.group(1) if m else defaut


class Kit:
    def __init__(self, racine):
        self.racine = racine
        self.manifest = json.load(open(os.path.join(racine, "manifest.json"), encoding="utf-8"))
        self.prefixe = prefixe_du_manifeste(self.manifest)
        self.reglages = json.load(open(os.path.join(racine, "site-settings.json"), encoding="utf-8"))
        self.pages = OrderedDict()
        for pid, info in sorted(self.manifest["content"]["page"].items(), key=lambda x: int(x[0])):
            slug = (info.get("url", "").rstrip("/").rsplit("/", 1)[-1]) or ""
            if info.get("show_on_front"):
                slug = ""
            self.pages[int(pid)] = {
                "id": int(pid),
                "titre": info.get("title", ""),
                "extrait": info.get("excerpt") or "",
                "slug": slug,
                "fichier": fichier_de_slug(slug),
                "doc": json.load(open(os.path.join(racine, "content/page/%s.json" % pid), encoding="utf-8")),
            }
        self.entete = self._gabarit("header")
        self.pied = self._gabarit("footer")
        self.menu = self._menu()
        self.articles = self._articles()

    def _gabarit(self, genre):
        for tid, info in self.manifest["templates"].items():
            if info.get("doc_type") == genre and info.get("conditions"):
                return json.load(open(os.path.join(self.racine, "templates/%s.json" % tid), encoding="utf-8"))
        return None

    def _menu(self):
        """Les entrées du menu, dans l'ordre, résolues vers les pages du kit."""
        chemin = os.path.join(self.racine, "wp-content/nav_menu_item/nav_menu_item.xml")
        x = open(chemin, encoding="utf-8").read()
        entrees = []
        for bloc in re.findall(r"<item>(.*?)</item>", x, re.S):
            def meta(cle):
                m = re.search(
                    r"<wp:meta_key>(?:<!\[CDATA\[)?%s(?:\]\]>)?</wp:meta_key>\s*"
                    r"<wp:meta_value>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</wp:meta_value>" % re.escape(cle),
                    bloc, re.S)
                return m.group(1).strip() if m else ""
            ordre = re.search(r"<wp:menu_order>(\d+)</wp:menu_order>", bloc)
            titre = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", bloc, re.S)
            entrees.append({
                "ordre": int(ordre.group(1)) if ordre else 99,
                "titre": html.unescape(titre.group(1).strip() if titre else ""),
                "type": meta("_menu_item_type"),
                "objet": meta("_menu_item_object_id"),
                "url": meta("_menu_item_url"),
            })
        entrees.sort(key=lambda e: e["ordre"])
        sortie = []
        for e in entrees:
            if e["type"] == "custom":
                sortie.append((e["titre"], e["url"], True))
            else:
                p = self.pages.get(int(e["objet"])) if e["objet"].isdigit() else None
                if p:
                    sortie.append((e["titre"] or p["titre"], p["fichier"], False))
        return sortie

    def _articles(self):
        """Les articles du Journal, lus dans le WXR du kit."""
        chemin = os.path.join(self.racine, "wp-content/post/post.xml")
        x = open(chemin, encoding="utf-8").read()
        pieces, arts = {}, []
        for bloc in re.findall(r"<item>(.*?)</item>", x, re.S):
            def champ(tag):
                m = re.search(r"<%s>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</%s>" % (tag, tag), bloc, re.S)
                return m.group(1).strip() if m else ""
            def meta(cle):
                m = re.search(
                    r"<wp:meta_key>(?:<!\[CDATA\[)?%s(?:\]\]>)?</wp:meta_key>\s*"
                    r"<wp:meta_value>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</wp:meta_value>" % re.escape(cle),
                    bloc, re.S)
                return m.group(1).strip() if m else ""
            pid = champ("wp:post_id")
            genre = champ("wp:post_type")
            if genre == "attachment":
                pieces[pid] = champ("wp:attachment_url")
                continue
            if genre != "post":
                continue
            arts.append({
                "id": pid,
                # le WXR porte déjà des entités HTML : on les défait avant de
                # ré-échapper, sinon « j&#039;osais » devient « j&amp;#039;osais »
                "titre": html.unescape(champ("title")),
                "slug": champ("wp:post_name"),
                "date": champ("wp:post_date")[:10],
                "contenu": champ("content:encoded"),
                "vignette_id": meta("_thumbnail_id"),
                "auteur": meta("_soha_author"),
            })
        for a in arts:
            a["vignette"] = pieces.get(a["vignette_id"], "")
            a["fichier"] = "article-%s.html" % (a["slug"] or a["id"])
        arts.sort(key=lambda a: (a["date"], a["titre"]), reverse=True)
        return arts


# --------------------------------------------------------------------------
#  Rendu
# --------------------------------------------------------------------------
class Rendu:
    def __init__(self, kit, medias_dispo, journal_fichier="journal.html"):
        self.kit = kit
        self.medias = medias_dispo          # {nom de base: chemin source}
        self.regles = OrderedDict()         # sélecteur → déclarations (base)
        self.regles_tab = OrderedDict()
        self.regles_tel = OrderedDict()
        self.images_utilisees = set()
        self.images_manquantes = Counter()
        self.journal_fichier = journal_fichier
        self.estimateur_pose = False
        self.premiere_image_posee = False

    # ---- chemins ----
    def media(self, url):
        """URL d'upload → chemin local, en retirant le suffixe de collision -N."""
        if not url:
            return ""
        nom = os.path.basename(url.split("?")[0])
        if nom not in self.medias:
            propre = re.sub(r"-[1-9](\.[A-Za-z0-9]+)$", r"\1", nom)
            if propre in self.medias:
                nom = propre
        if nom in self.medias:
            self.images_utilisees.add(nom)
            return "medias/" + nom
        self.images_manquantes[nom] += 1
        return "medias/" + nom

    def media_css(self, url):
        """Le même chemin, mais vu depuis la feuille de style.

        Une `url()` dans un fichier CSS se résout par rapport au CSS, pas à la
        page. `assets/soha.css` cherchait donc `assets/medias/…` et ne trouvait
        rien : les neuf images de fond du site — dont quatre hero de page — ne
        s'affichaient pas, en silence, depuis la première version. Aucune erreur
        nulle part : un fond qui manque, ça ressemble à un fond qui n'existe pas.
        """
        chemin = self.media(url)
        return ("../" + chemin) if chemin else chemin

    def lien(self, url):
        """Lien du kit → lien du site statique.

        Le préfixe vient du manifeste (`self.kit.prefixe`), jamais d'une
        constante : c'est en le figeant à « /dev2 » qu'on a laissé passer
        quatre cent vingt liens absolus le jour où le site est devenu « /dev ».
        """
        if not url:
            return "#"
        u = url.strip()
        if u.startswith(("mailto:", "tel:", "#")):
            return u

        pre = self.kit.prefixe                      # « /dev »
        pres = pre + "/"                            # « /dev/ »

        if re.match(r"^https?://", u):
            if "/wp-content/uploads/" in u:
                # les images sont rapatriées en local ; les autres pièces (vidéos,
                # PDF) restent servies par le serveur — elles ne sont dans aucun kit
                if re.search(r"\.(webp|jpe?g|png|gif|svg|avif)$", u, re.I):
                    return self.media(u)
                return re.sub(r"/dev\d*/wp-content/", pres + "wp-content/", u)
            m = re.match(r"^https?://[^/]+" + re.escape(pre) + r"(?:/(.*))?$", u)
            if m:
                u = pres + (m.group(1) or "")
            else:
                return u                       # lien vraiment externe : on n'y touche pas

        if u == pre or u.startswith(pres):
            reste = u[len(pres):] if u.startswith(pres) else ""
            ancre = ""
            if "#" in reste:
                reste, ancre = reste.split("#", 1)
                ancre = "#" + ancre
            slug = reste.strip("/").rsplit("/", 1)[-1]
            for p in self.kit.pages.values():
                if p["slug"] == slug:
                    return p["fichier"] + ancre
            if slug == "":
                return "index.html" + ancre
            return fichier_de_slug(slug) + ancre
        return u

    def reecrire_html(self, frag):
        """Réécrit les href et src d'un fragment HTML d'éditeur."""
        if not frag:
            return ""
        frag = re.sub(r'href="([^"]*)"', lambda m: 'href="%s"' % self.lien(m.group(1)), frag)
        frag = re.sub(r'src="([^"]*)"', lambda m: 'src="%s"' % self.media(m.group(1)), frag)
        return frag

    # ---- CSS ----
    def ajoute(self, sel, base, tab=None, tel=None):
        if base:
            self.regles.setdefault(sel, []).extend(base)
        if tab:
            self.regles_tab.setdefault(sel, []).extend(tab)
        if tel:
            self.regles_tel.setdefault(sel, []).extend(tel)

    def sel(self, eid):
        return ".elementor-element-%s" % eid

    # ---- éléments ----
    def element(self, e, profondeur=0):
        t = e.get("elType")
        if t == "container":
            return self.conteneur(e, profondeur)
        if t == "section":
            return "".join(self.element(x, profondeur + 1) for x in e.get("elements", []))
        if t == "column":
            return "".join(self.element(x, profondeur + 1) for x in e.get("elements", []))
        if t == "widget":
            return self.widget(e)
        return ""

    def conteneur(self, e, profondeur):
        eid = e.get("id", "x")
        s = e.get("settings") if isinstance(e.get("settings"), dict) else {}
        # `media_css` et non `media` : ces règles vont dans `assets/soha.css`.
        base, tab, tel = css_conteneur(s, self.media_css)
        boxed = (s.get("content_width") or "boxed") != "full"
        classes = ["elementor-element", "elementor-element-%s" % eid, "e-con",
                   "e-parent" if profondeur == 0 else "e-child"]
        classes.append("e-con-boxed" if boxed else "e-con-full")
        for c in (s.get("_css_classes") or "").split():
            classes.append(c)
        if s.get("sticky") == "top":
            classes.append("soha-collant")
        # le padding et le fond vont sur l'enveloppe ; la largeur interne sur e-con-inner
        self.ajoute(self.sel(eid), base, tab, tel)
        voile = css_voile(s)
        if voile:
            # Le voile se dessine derrière le contenu : le conteneur devient le
            # repère, et ses enfants remontent d'un cran.
            self.ajoute(self.sel(eid), ["position:relative"])
            self.ajoute(self.sel(eid) + "::before", voile)
            self.ajoute(self.sel(eid) + " > *", ["position:relative", "z-index:1"])
        if boxed:
            lb = longueur(s.get("boxed_width"))
            if lb:
                self.ajoute(self.sel(eid) + " > .e-con-inner", ["max-width:%s" % lb])
        attrs = ' id="%s"' % html.escape(s["_element_id"]) if s.get("_element_id") else ""
        dedans = "".join(self.element(x, profondeur + 1) for x in e.get("elements", []))
        if boxed:
            dedans = '<div class="e-con-inner">%s</div>' % dedans
        return '<div class="%s"%s>%s</div>' % (" ".join(classes), attrs, dedans)

    def enveloppe(self, e, genre, dedans, extra_classes=()):
        eid = e.get("id", "x")
        s = e.get("settings") if isinstance(e.get("settings"), dict) else {}
        classes = ["elementor-element", "elementor-element-%s" % eid,
                   "elementor-widget", "elementor-widget-%s" % genre]
        classes.extend(extra_classes)
        m = boite(s.get("_margin"))
        if m:
            self.ajoute(self.sel(eid), ["margin:%s" % m])
        if s.get("align"):
            self.ajoute(self.sel(eid), ["text-align:%s" % s["align"]])
        if s.get("align_mobile"):
            self.ajoute(self.sel(eid), [], None, ["text-align:%s" % s["align_mobile"]])
        w = longueur(s.get("_element_width")) if s.get("_element_width") else None
        if w:
            self.ajoute(self.sel(eid), ["width:%s" % w])
        attrs = ' id="%s"' % html.escape(s["_element_id"]) if s.get("_element_id") else ""
        return '<div class="%s"%s><div class="elementor-widget-container">%s</div></div>' % (
            " ".join(classes), attrs, dedans)

    def widget(self, e):
        t = e.get("widgetType")
        s = e.get("settings") if isinstance(e.get("settings"), dict) else {}
        eid = e.get("id", "x")
        fn = getattr(self, "w_" + t.replace("-", "_"), None)
        if fn is None:
            return "<!-- widget non rendu : %s -->" % html.escape(str(t))
        return fn(e, s, eid)

    # ---- widgets ----
    def w_heading(self, e, s, eid):
        niveau = s.get("header_size") or "h2"
        if niveau not in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div"):
            niveau = "h2"
        d = typographie(s, "typography_")
        if s.get("title_color"):
            d.append("color:%s" % s["title_color"])
        self.ajoute(self.sel(eid) + " .elementor-heading-title", d,
                    typographie(s, "typography_", "_tablet"),
                    typographie(s, "typography_", "_mobile"))
        if s.get("_border_border"):
            b = ["border-style:%s" % s["_border_border"]]
            if boite(s.get("_border_width")):
                b.append("border-width:%s" % boite(s["_border_width"]))
            if s.get("_border_color"):
                b.append("border-color:%s" % s["_border_color"])
            if boite(s.get("_padding")):
                b.append("padding:%s" % boite(s["_padding"]))
            self.ajoute(self.sel(eid), b)
        texte = self.reecrire_html(str(s.get("title", "")))
        if isinstance(s.get("link"), dict) and s["link"].get("url"):
            texte = '<a href="%s">%s</a>' % (self.lien(s["link"]["url"]), texte)
        corps = '<%s class="elementor-heading-title">%s</%s>' % (niveau, texte, niveau)
        return self.enveloppe(e, "heading", corps)

    def w_text_editor(self, e, s, eid):
        d = typographie(s, "typography_")
        if s.get("text_color"):
            d.append("color:%s" % s["text_color"])
        self.ajoute(self.sel(eid), d,
                    typographie(s, "typography_", "_tablet"),
                    typographie(s, "typography_", "_mobile"))
        return self.enveloppe(e, "text-editor", self.reecrire_html(s.get("editor", "")))

    def w_image(self, e, s, eid):
        img = s.get("image") or {}
        src = self.media(img.get("url", ""))
        d = []
        w = longueur(s.get("width"))
        if w:
            d.append("width:%s" % w)
        h = longueur(s.get("height"))
        if h:
            d.append("height:%s" % h)
        if s.get("object-fit"):
            d.append("object-fit:%s" % s["object-fit"])
        r = longueur(s.get("image_border_radius")) or boite(s.get("image_border_radius"))
        if r:
            d.append("border-radius:%s" % r)
        self.ajoute(self.sel(eid) + " img", d)
        alt = texte_alternatif(src)
        # la première image de la page est celle du héros : elle est préchargée,
        # donc jamais paresseuse — sinon le préchargement se contredit lui-même
        if self.premiere_image_posee:
            attrs_img = ' loading="lazy" decoding="async"'
        else:
            attrs_img = ' loading="eager" fetchpriority="high" decoding="async"'
            self.premiere_image_posee = True
        balise = '<img src="%s" alt="%s"%s>' % (src, html.escape(alt), attrs_img)
        if s.get("link_to") == "custom" and isinstance(s.get("link"), dict):
            balise = '<a href="%s">%s</a>' % (self.lien(s["link"].get("url", "")), balise)
        return self.enveloppe(e, "image", balise)

    def w_button(self, e, s, eid):
        d = typographie(s, "typography_")
        if s.get("background_color"):
            d.append("background-color:%s" % s["background_color"])
        if s.get("button_text_color"):
            d.append("color:%s" % s["button_text_color"])
        if s.get("border_border"):
            d.append("border-style:%s" % s["border_border"])
            if boite(s.get("border_width")):
                d.append("border-width:%s" % boite(s["border_width"]))
            if s.get("border_color"):
                d.append("border-color:%s" % s["border_color"])
        r = longueur(s.get("border_radius")) or boite(s.get("border_radius"))
        if r:
            d.append("border-radius:%s" % r)
        if boite(s.get("text_padding")):
            d.append("padding:%s" % boite(s["text_padding"]))
        self.ajoute(self.sel(eid) + " .elementor-button", d)
        survol = []
        if s.get("button_background_hover_color"):
            survol.append("background-color:%s" % s["button_background_hover_color"])
        if s.get("button_hover_text_color"):
            survol.append("color:%s" % s["button_hover_text_color"])
        if s.get("button_hover_border_color"):
            survol.append("border-color:%s" % s["button_hover_border_color"])
        if survol:
            self.ajoute(self.sel(eid) + " .elementor-button:hover", survol)
        lien = s.get("link") or {}
        cible = ' target="_blank" rel="noopener"' if lien.get("is_external") else ""
        corps = ('<div class="elementor-button-wrapper">'
                 '<a class="elementor-button elementor-button-link" href="%s"%s>'
                 '<span class="elementor-button-content-wrapper">'
                 '<span class="elementor-button-text">%s</span></span></a></div>') % (
            self.lien(lien.get("url", "")), cible, self.reecrire_html(str(s.get("text", ""))))
        return self.enveloppe(e, "button", corps)

    def w_divider(self, e, s, eid):
        d = []
        if s.get("color"):
            d.append("border-top-color:%s" % s["color"])
        if longueur(s.get("weight")):
            d.append("border-top-width:%s" % longueur(s["weight"]))
        self.ajoute(self.sel(eid) + " .elementor-divider-separator", d)
        corps = '<div class="elementor-divider"><span class="elementor-divider-separator"></span></div>'
        return self.enveloppe(e, "divider", corps)

    def w_accordion(self, e, s, eid):
        morceaux = []
        for i, t in enumerate(s.get("tabs") or []):
            ouvert = " open" if i == 0 else ""
            morceaux.append(
                '<details class="soha-pli"%s><summary>%s</summary>'
                '<div class="soha-pli-corps">%s</div></details>' % (
                    ouvert, html.escape(t.get("tab_title", "")),
                    self.reecrire_html(t.get("tab_content", ""))))
        d = typographie(s, "title_typography_")
        if s.get("title_color"):
            d.append("color:%s" % s["title_color"])
        self.ajoute(self.sel(eid) + " summary", d)
        dc = typographie(s, "content_typography_")
        if s.get("content_color"):
            dc.append("color:%s" % s["content_color"])
        self.ajoute(self.sel(eid) + " .soha-pli-corps", dc)
        if s.get("border_color"):
            self.ajoute(self.sel(eid) + " .soha-pli",
                        ["border-bottom:%s solid %s" % (longueur(s.get("border_width")) or "1px",
                                                        s["border_color"])])
        return self.enveloppe(e, "accordion", "".join(morceaux))

    def w_testimonial(self, e, s, eid):
        d = typographie(s, "content_typography_")
        if s.get("content_content_color"):
            d.append("color:%s" % s["content_content_color"])
        self.ajoute(self.sel(eid) + " blockquote", d)
        if s.get("name_text_color"):
            self.ajoute(self.sel(eid) + " cite b", ["color:%s" % s["name_text_color"]])
        if s.get("job_text_color"):
            self.ajoute(self.sel(eid) + " cite span", ["color:%s" % s["job_text_color"]])
        nom = html.escape(s.get("testimonial_name", ""))
        metier = html.escape(s.get("testimonial_job", ""))
        corps = ('<figure class="soha-temoin"><blockquote>%s</blockquote>'
                 '<figcaption><cite><b>%s</b>%s</cite></figcaption></figure>') % (
            html.escape(re.sub(r"\s+", " ", s.get("testimonial_content", "")).strip()),
            nom, (" <span>%s</span>" % metier) if metier else "")
        return self.enveloppe(e, "testimonial", corps)

    def w_form(self, e, s, eid):
        champs = []
        for f in s.get("form_fields") or []:
            fid = f.get("custom_id") or f.get("_id")
            label = html.escape(f.get("field_label", ""))
            req = ' required' if f.get("required") == "true" else ""
            ph = html.escape(f.get("placeholder") or "")
            genre = f.get("field_type")
            if genre == "textarea":
                entree = '<textarea id="%s" name="%s" rows="%s" placeholder="%s"%s></textarea>' % (
                    fid, fid, f.get("rows") or "4", ph, req)
            elif genre == "select":
                opts = "".join('<option>%s</option>' % html.escape(o)
                               for o in (f.get("field_options") or "").split("\n") if o.strip())
                entree = '<select id="%s" name="%s"%s>%s</select>' % (fid, fid, req, opts)
            elif genre == "radio":
                choix = [o for o in (f.get("field_options") or "").split("\n") if o.strip()]
                boutons = "".join(
                    '<label class="soha-radio"><input type="radio" name="%s" value="%s"%s> %s</label>'
                    % (fid, html.escape(o.strip()), req if i == 0 else "", html.escape(o.strip()))
                    for i, o in enumerate(choix))
                champs.append('<div class="soha-champ"><span class="soha-legende">%s</span>'
                              '<div class="soha-radios" role="radiogroup" aria-label="%s">%s</div></div>'
                              % (label, label, boutons))
                continue
            elif genre == "acceptance":
                entree = ('<label class="soha-case"><input type="checkbox" id="%s" name="%s"%s> %s</label>'
                          % (fid, fid, req, self.reecrire_html(f.get("acceptance_text", "") or label)))
                champs.append('<div class="soha-champ soha-champ-case">%s</div>' % entree)
                continue
            else:
                entree = '<input type="%s" id="%s" name="%s" placeholder="%s"%s>' % (
                    genre if genre in ("email", "tel", "date", "number", "url") else "text",
                    fid, fid, ph, req)
            champs.append('<div class="soha-champ"><label for="%s">%s</label>%s</div>' % (fid, label, entree))
        d = typographie(s, "button_typography_")
        if s.get("button_background_color"):
            d.append("background-color:%s" % s["button_background_color"])
        if s.get("button_text_color"):
            d.append("color:%s" % s["button_text_color"])
        if boite(s.get("button_text_padding")):
            d.append("padding:%s" % boite(s["button_text_padding"]))
        r = longueur(s.get("button_border_radius")) or boite(s.get("button_border_radius"))
        if r:
            d.append("border-radius:%s" % r)
        self.ajoute(self.sel(eid) + " button", d)
        if s.get("label_color"):
            self.ajoute(self.sel(eid) + " label", ["color:%s" % s["label_color"]])
        dc = typographie(s, "field_typography_")
        if dc:
            self.ajoute(self.sel(eid) + " input," + self.sel(eid) + " select," + self.sel(eid) + " textarea", dc)
        corps = ('<form class="soha-formulaire" method="post" action="#" '
                 'aria-label="%s" novalidate>%s'
                 '<p class="soha-note-form">Site de démonstration : l\'envoi est désactivé. '
                 'Sur le site WordPress, ce formulaire écrit à info@centresoha.com.</p>'
                 '<button type="submit">%s</button></form>') % (
            html.escape(s.get("form_name", "Formulaire")), "".join(champs),
            html.escape(s.get("button_text", "Envoyer")))
        return self.enveloppe(e, "form", corps)

    def w_html(self, e, s, eid):
        return self.enveloppe(e, "html", self.reecrire_html(s.get("html", "")))

    def w_shortcode(self, e, s, eid):
        code = (s.get("shortcode") or "").strip()
        if code == "[soha_estimateur]":
            return self.enveloppe(e, "shortcode", self.estimateur())
        return self.enveloppe(e, "shortcode",
                              "<!-- raccourci non rendu : %s -->" % html.escape(code))

    def w_nav_menu(self, e, s, eid):
        liens = []
        for titre, cible, externe in self.kit.menu:
            ext = ' target="_blank" rel="noopener"' if externe else ""
            liens.append('<li><a href="%s"%s>%s</a></li>' % (cible, ext, html.escape(titre)))
        d = typographie(s, "menu_typography_")
        if s.get("color_menu_item"):
            d.append("color:%s" % s["color_menu_item"])
        self.ajoute(self.sel(eid) + " .elementor-nav-menu a", d)
        if s.get("color_menu_item_hover"):
            self.ajoute(self.sel(eid) + " .elementor-nav-menu a:hover",
                        ["color:%s" % s["color_menu_item_hover"]])
        corps = ('<nav class="soha-menu" aria-label="Menu principal">'
                 '<button class="soha-bascule" type="button" aria-expanded="false" '
                 'aria-controls="soha-menu-liste"><span></span>Menu</button>'
                 '<ul class="elementor-nav-menu" id="soha-menu-liste">%s</ul></nav>') % "".join(liens)
        return self.enveloppe(e, "nav-menu", corps)

    def w_posts(self, e, s, eid):
        cartes = []
        for a in self.kit.articles:
            vign = self.media(a["vignette"]) if a["vignette"] else ""
            extrait = extrait_de(a["contenu"], int(s.get("classic_excerpt_length") or 18))
            balise = s.get("classic_title_tag") or "h3"
            img = ('<a class="soha-carte-img" href="%s"><img src="%s" alt="%s" loading="lazy" decoding="async"></a>'
                   % (a["fichier"], vign, html.escape(a["titre"]))) if vign else ""
            cartes.append(
                '<article class="soha-carte">%s<div class="soha-carte-corps">'
                '<p class="soha-carte-meta">%s</p>'
                '<%s class="soha-carte-titre"><a href="%s">%s</a></%s>'
                '<p class="soha-carte-extrait">%s</p>'
                '<a class="soha-carte-lire" href="%s">%s</a>'
                '</div></article>' % (
                    img, date_fr(a["date"]), balise, a["fichier"], html.escape(a["titre"]), balise,
                    html.escape(extrait), a["fichier"],
                    html.escape(s.get("classic_read_more_text") or "Lire l'article →")))
        col = s.get("classic_columns") or "3"
        colt = s.get("classic_columns_tablet") or "2"
        colm = s.get("classic_columns_mobile") or "1"
        g = longueur(s.get("classic_row_gap")) or "28px"
        self.ajoute(self.sel(eid) + " .soha-grille-articles",
                    ["display:grid", "gap:%s" % g, "grid-template-columns:repeat(%s,minmax(0,1fr))" % col],
                    ["grid-template-columns:repeat(%s,minmax(0,1fr))" % colt],
                    ["grid-template-columns:repeat(%s,minmax(0,1fr))" % colm])
        d = typographie(s, "classic_title_typography_")
        if s.get("classic_title_color"):
            d.append("color:%s" % s["classic_title_color"])
        self.ajoute(self.sel(eid) + " .soha-carte-titre a", d)
        if s.get("classic_excerpt_color"):
            self.ajoute(self.sel(eid) + " .soha-carte-extrait", ["color:%s" % s["classic_excerpt_color"]])
        if s.get("classic_read_more_color"):
            self.ajoute(self.sel(eid) + " .soha-carte-lire", ["color:%s" % s["classic_read_more_color"]])
        if s.get("classic_meta_color"):
            self.ajoute(self.sel(eid) + " .soha-carte-meta", ["color:%s" % s["classic_meta_color"]])
        ratio = s.get("classic_item_ratio")
        if isinstance(ratio, dict) and ratio.get("size"):
            self.ajoute(self.sel(eid) + " .soha-carte-img",
                        ["aspect-ratio:1/%s" % ratio["size"], "display:block", "overflow:hidden"])
            self.ajoute(self.sel(eid) + " .soha-carte-img img",
                        ["width:100%", "height:100%", "object-fit:cover"])
        return self.enveloppe(e, "posts",
                              '<div class="soha-grille-articles">%s</div>' % "".join(cartes))

    def w_theme_post_content(self, e, s, eid):
        return ""

    # ---- l'estimateur, porté de l'extension vers le statique ----
    def estimateur(self):
        grille = OrderedDict([
            ("studio",    ["Studio", "900 pi² · insonorisé",
                           {"jour": 450, "demi": 250, "soir": 200}, {"jour": 550, "demi": 300, "soir": 250}]),
            ("soha",      ["Espace SÖHA", "2200 pi² · grand plateau",
                           {"jour": 600, "demi": 350, "soir": 250}, {"jour": 700, "demi": 400, "soir": 300}]),
            ("salle4",    ["Salle 4", "bureau double · fenestré",
                           {"jour": 160, "demi": 100, "soir": 80}, {"jour": 240, "demi": 140, "soir": 120}]),
            ("salles123", ["Salles 1·2·3", "cabinet de soin",
                           {"jour": 120, "demi": 60, "soir": 30}, {"jour": 160, "demi": 90, "soir": 60}]),
        ])
        espaces = "".join(
            '<button type="button" class="se-space%s" data-k="%s">'
            '<span class="se-space-name">%s</span>'
            '<span class="se-space-sub">%s</span></button>' % (
                " on" if i == 0 else "", k, html.escape(v[0]), html.escape(v[1]))
            for i, (k, v) in enumerate(grille.items()))
        data = json.dumps(grille, ensure_ascii=False)
        resa = json.dumps("reservation.html")
        self.estimateur_pose = True
        return ('<div id="sohaEstim" data-first="studio"><div class="se-grid">'
                '<div class="se-panel">'
                '<h3 class="se-step">1 · Choisissez votre espace</h3>'
                '<div class="se-spaces" id="seSpaces">%s</div>'
                '<h3 class="se-step">2 · Type de journée</h3>'
                '<div class="se-seg" id="seDay">'
                '<button type="button" data-k="sem" class="on">Semaine</button>'
                '<button type="button" data-k="fds">Fin de semaine</button></div>'
                '<h3 class="se-step">3 · Plage horaire</h3>'
                '<div class="se-seg" id="seSlot">'
                '<button type="button" data-k="jour" class="on">Journée</button>'
                '<button type="button" data-k="demi">Demi-journée</button>'
                '<button type="button" data-k="soir">Soirée</button></div></div>'
                '<div class="se-out"><div class="se-lab">Estimation</div>'
                '<div class="se-price" id="sePrice">450 $ <small>+tx</small></div>'
                '<div class="se-sel" id="seSel">Studio · Semaine · Journée</div>'
                '<p class="se-note">* Tarif indicatif. Prix, conditions et disponibilités sujets à '
                'changement. Minimum 2 jours les fins de semaine. Aucune réservation par téléphone.</p>'
                '<a class="se-cta" id="seCta" href="reservation.html">'
                'Demander cette réservation</a></div></div>'
                '<script>window.SOHA_ESTIM=%s;window.SOHA_ESTIM_RESA=%s;</script></div>'
                % (espaces, data, resa))

    # ---- feuille de style ----
    def feuille(self, css_global):
        out = [SOCLE, css_global, ESTIMATEUR_CSS]
        def bloc(regles):
            morceaux = []
            for sel, decls in regles.items():
                vues, propre = set(), []
                for d in reversed(decls):          # la dernière écriture gagne
                    p = d.split(":", 1)[0]
                    if p in vues:
                        continue
                    vues.add(p)
                    propre.append(d)
                morceaux.append("%s{%s}" % (sel, ";".join(reversed(propre))))
            return "\n".join(morceaux)
        out.append("/* --- éléments --- */")
        out.append(bloc(self.regles))
        if self.regles_tab:
            out.append("%s{\n%s\n}" % (MQ_TABLETTE, bloc(self.regles_tab)))
        if self.regles_tel:
            out.append("%s{\n%s\n}" % (MQ_TELEPHONE, bloc(self.regles_tel)))
        return "\n\n".join(out)


# --------------------------------------------------------------------------
#  Petites aides de contenu
# --------------------------------------------------------------------------
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def date_fr(iso):
    try:
        a, m, j = iso.split("-")
        return "%d %s %s" % (int(j), MOIS[int(m) - 1], a)
    except Exception:
        return iso


def extrait_de(html_contenu, mots):
    t = re.sub(r"<[^>]+>", " ", html_contenu or "")
    t = html.unescape(re.sub(r"\s+", " ", t)).strip()
    bouts = t.split(" ")
    return " ".join(bouts[:mots]) + ("…" if len(bouts) > mots else "")


def texte_alternatif(chemin):
    """Texte alternatif déduit du nom de fichier — comme le fait l'extension Finition."""
    nom = os.path.basename(chemin)
    nom = re.sub(r"\.(webp|jpg|jpeg|png|avif)$", "", nom, flags=re.I)
    nom = re.sub(r"^soha[-_]", "", nom)
    nom = re.sub(r"-[0-9a-f]{6,}$", "", nom)
    nom = re.sub(r"-(\d{3})$", "", nom)
    if nom.startswith("portrait-"):
        qui = nom[len("portrait-"):].replace("-", " ").title()
        return "Portrait de %s, au Centre Soha" % qui
    if nom.startswith("hero-"):
        return "Le Centre Soha — %s" % nom[len("hero-"):].replace("-", " ")
    if nom.startswith("logo"):
        return "Centre Soha"
    return "Le Centre Soha — %s" % nom.replace("-", " ")


# --------------------------------------------------------------------------
#  Socle CSS (ce qu'Elementor apporte nativement et qu'il faut reproduire)
# --------------------------------------------------------------------------
SOCLE = """/* ============================================================
   Centre Soha — socle du site statique
   Reproduit ce qu'Elementor fournit nativement, rien de plus.
   ============================================================ */
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#FBF8F3;color:#0E1A15;
  font-family:"Schibsted Grotesk",system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
img,video{max-width:100%;height:auto;display:block}
a{color:inherit}
h1,h2,h3,h4,h5,h6{margin:0;font-weight:400}
p{margin:0 0 1em}
ul,ol{margin:0 0 1em;padding-left:1.25em}
blockquote{margin:0}
figure{margin:0}

/* conteneurs — équivalents de .e-con d'Elementor */
.e-con{display:flex;flex-direction:column;position:relative;width:100%;
  --content-width:1200px}
.e-con-boxed{align-items:center}
.e-con-boxed>.e-con-inner{display:flex;flex-direction:inherit;
  gap:inherit;align-items:inherit;justify-content:inherit;flex-wrap:inherit;
  width:100%;max-width:var(--content-width);margin-inline:auto}
.e-con-full{align-items:stretch}
.elementor-widget{min-width:0}
.elementor-widget-container>*:last-child{margin-bottom:0}

/* boutons */
.elementor-button{display:inline-flex;align-items:center;justify-content:center;
  text-align:center;text-decoration:none;cursor:pointer;border:0 solid transparent;
  background:#0E1A15;color:#fff;padding:12px 24px;line-height:1.2;
  transition:background-color .2s ease,color .2s ease,border-color .2s ease}
.elementor-button-wrapper{display:flex}
.e-con-boxed[class*="align"] .elementor-button-wrapper{justify-content:inherit}

/* séparateur */
.elementor-divider-separator{display:block;border-top:1px solid #E0D8CA}

/* en-tête collant */
.soha-collant{position:sticky;top:0;z-index:50}

/* menu */
.soha-menu{display:flex;align-items:center;gap:18px}
.elementor-nav-menu{display:flex;flex-wrap:wrap;align-items:center;gap:18px;
  list-style:none;margin:0;padding:0}
.elementor-nav-menu a{text-decoration:none;white-space:nowrap}
.soha-bascule{display:none;align-items:center;gap:8px;background:none;border:0;
  font:inherit;font-weight:500;cursor:pointer;padding:10px 4px;min-height:44px;color:inherit}
.soha-bascule span{display:block;width:20px;height:2px;background:currentColor;
  box-shadow:0 6px 0 currentColor,0 -6px 0 currentColor}
@media (max-width:1024px){
  .soha-bascule{display:inline-flex}
  .elementor-nav-menu{display:none;position:absolute;left:0;right:0;top:100%;
    flex-direction:column;align-items:flex-start;gap:0;
    background:#FBF8F3;border-bottom:1px solid #E0D8CA;padding:8px 22px 16px;z-index:60}
  .soha-menu[data-ouvert="oui"] .elementor-nav-menu{display:flex}
  .elementor-nav-menu li{width:100%;border-top:1px solid #EFE8DA}
  .elementor-nav-menu a{display:flex;align-items:center;min-height:48px;width:100%}
}

/* accordéon */
.soha-pli{border-bottom:1px solid #E0D8CA}
.soha-pli summary{cursor:pointer;padding:16px 0;list-style:none;min-height:44px;
  display:flex;align-items:center;justify-content:space-between;gap:12px}
.soha-pli summary::-webkit-details-marker{display:none}
.soha-pli summary::after{content:"+";font-size:1.2em;line-height:1;flex:none}
.soha-pli[open] summary::after{content:"–"}
.soha-pli-corps{padding:0 0 18px}

/* témoignage */
.soha-temoin blockquote{margin:0 0 10px}
.soha-temoin cite{font-style:normal;font-size:.9rem}
.soha-temoin cite b{font-weight:600}

/* formulaires */
.soha-formulaire{display:grid;gap:14px}
.soha-champ{display:grid;gap:6px}
.soha-champ label{font-size:.85rem;font-weight:500}
.soha-formulaire input,.soha-formulaire select,.soha-formulaire textarea{
  font:inherit;padding:12px 14px;min-height:46px;border:1px solid #C9BEAB;
  border-radius:2px;background:#fff;color:inherit;width:100%}
.soha-formulaire textarea{min-height:110px;resize:vertical}
.soha-champ-case label{display:flex;gap:10px;align-items:flex-start;font-weight:400}
.soha-legende{font-size:.85rem;font-weight:500}
.soha-radios{display:flex;flex-wrap:wrap;gap:8px 18px}
.soha-radio{display:inline-flex;align-items:center;gap:8px;min-height:44px;
  font-weight:400;cursor:pointer}
.soha-radio input{flex:none;width:20px;height:20px;min-height:0;accent-color:#19A7DB}
.soha-champ-case input{flex:none;width:24px;height:24px;min-height:0;margin-top:2px;accent-color:#19A7DB}
.soha-formulaire button{font:inherit;cursor:pointer;border:0;background:#19A7DB;color:#fff;
  padding:14px 26px;min-height:48px;border-radius:2px;justify-self:start}
.soha-note-form{font-size:.8rem;color:#6B7A73;margin:0}

/* cartes d'articles */
.soha-carte{display:flex;flex-direction:column;gap:12px;min-width:0}
.soha-carte-corps{display:flex;flex-direction:column;gap:8px}
.soha-carte-meta{font-family:"DM Mono",ui-monospace,monospace;font-size:.72rem;
  letter-spacing:.06em;text-transform:uppercase;margin:0}
.soha-carte-titre{margin:0;line-height:1.15}
.soha-carte-titre a{text-decoration:none}
.soha-carte-titre a:hover{text-decoration:underline}
.soha-carte-extrait{font-size:.95rem;margin:0}
.soha-carte-lire{font-size:.88rem;font-weight:600;text-decoration:none}
.soha-carte-lire:hover{text-decoration:underline}

/* corps d'article */
.soha-article{max-width:1200px;margin:0 auto;padding:56px 22px 72px}
.soha-article-entete{max-width:42rem;margin:0 auto 34px}
.soha-article-surtitre{font-family:"DM Mono",ui-monospace,monospace;font-size:.72rem;
  letter-spacing:.14em;text-transform:uppercase;color:#5A6460;margin:0 0 14px}
.soha-article h1{font-family:"Fraunces",Georgia,serif;font-weight:600;
  font-size:clamp(2rem,5vw,3rem);line-height:1.06;margin:0 0 12px}
.soha-article-photo{margin:0 0 34px}
.soha-article-corps{max-width:38rem;margin:0 auto;font-size:1.06rem;line-height:1.7;
  overflow-wrap:break-word}
.soha-article-corps h2{font-family:"Fraunces",Georgia,serif;font-weight:600;
  font-size:clamp(1.4rem,3.4vw,2rem);line-height:1.15;margin:1.8em 0 .6em}
.soha-article-corps h3{font-family:"Fraunces",Georgia,serif;font-weight:600;
  font-size:1.25rem;margin:1.6em 0 .5em}
.soha-article-corps img{margin:1.6em 0}
.soha-article-corps a{color:#19A7DB}
.soha-retour{display:inline-block;margin-top:40px;font-weight:600;
  text-decoration:none;color:#19A7DB}

/* accessibilité */
.soha-saut{position:absolute;left:-9999px;top:0;background:#0E1A15;color:#fff;
  padding:12px 18px;z-index:100}
.soha-saut:focus{left:8px;top:8px}
:focus-visible{outline:2px solid #19A7DB;outline-offset:2px}
@media (prefers-reduced-motion:reduce){
  *{animation-duration:.01ms!important;animation-iteration-count:1!important;
    transition-duration:.01ms!important;scroll-behavior:auto!important}
}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

ESTIMATEUR_CSS = """/* ============================================================
   Estimateur de location — porté de l'extension soha-estimateur v2.0.1.
   Deux écarts au canon corrigés ici : la police passe d'Inter à
   Schibsted Grotesk, et l'ivoire #F4F1E9 (retiré) devient #F4F0E7.
   ============================================================ */
#sohaEstim{--se-accent:#19A7DB;--se-ink:#0E1A15;--se-paper:#F4F0E7;
  --se-card:#14100C;--se-card-ink:#F4F0E7;--se-line:rgba(14,26,21,.16);
  font-family:"Schibsted Grotesk",system-ui,-apple-system,"Segoe UI",sans-serif;
  color:var(--se-ink);max-width:960px;margin:0 auto;width:100%}
#sohaEstim *{box-sizing:border-box}
#sohaEstim .se-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:22px}
@media (max-width:720px){#sohaEstim .se-grid{grid-template-columns:1fr}}
#sohaEstim .se-panel{background:var(--se-paper);border:1px solid var(--se-line);
  border-radius:14px;padding:22px 24px}
#sohaEstim .se-step{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;
  color:rgba(14,26,21,.55);font-weight:600;margin:18px 0 10px}
#sohaEstim .se-step:first-child{margin-top:0}
#sohaEstim .se-spaces{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media (max-width:480px){#sohaEstim .se-spaces{grid-template-columns:1fr}}
#sohaEstim .se-space{display:flex;flex-direction:column;gap:2px;text-align:left;
  cursor:pointer;background:#fff;border:1px solid var(--se-line);border-radius:11px;
  padding:13px 15px;min-height:60px;font:inherit;color:inherit}
#sohaEstim .se-space .se-space-name{font-family:"Fraunces",Georgia,serif;font-size:1.05rem}
#sohaEstim .se-space .se-space-sub{font-size:.78rem;color:rgba(14,26,21,.55)}
#sohaEstim .se-space.on{border-color:var(--se-accent);box-shadow:inset 0 0 0 1px var(--se-accent)}
#sohaEstim .se-seg{display:flex;flex-wrap:wrap;gap:8px}
#sohaEstim .se-seg button{cursor:pointer;font:inherit;background:#fff;color:inherit;
  border:1px solid var(--se-line);border-radius:999px;padding:9px 16px;min-height:44px}
#sohaEstim .se-seg button.on{background:var(--se-ink);color:#fff;border-color:var(--se-ink)}
#sohaEstim .se-out{background:var(--se-card);color:var(--se-card-ink);border-radius:14px;
  padding:28px 26px;display:flex;flex-direction:column;justify-content:center}
#sohaEstim .se-lab{font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;
  color:var(--se-accent);font-weight:600}
#sohaEstim .se-price{font-family:"Fraunces",Georgia,serif;font-size:3rem;line-height:1.05;margin:8px 0 6px}
#sohaEstim .se-price small{font-size:1rem;color:var(--se-accent)}
#sohaEstim .se-sel{font-size:.95rem;color:rgba(244,240,231,.7)}
#sohaEstim .se-note{font-size:.74rem;color:rgba(244,240,231,.5);margin:16px 0 18px;line-height:1.5}
#sohaEstim .se-cta{display:inline-block;text-align:center;text-decoration:none;font-weight:600;
  background:var(--se-accent);color:#fff;border-radius:999px;padding:14px 22px;min-height:50px}
#sohaEstim .se-cta:hover{filter:brightness(.95)}
"""

JS = """/* Centre Soha — le strict nécessaire : le menu, et l'estimateur. */
(function(){
  var menu=document.querySelector('.soha-menu');
  if(menu){
    var b=menu.querySelector('.soha-bascule');
    var ferme=function(){menu.removeAttribute('data-ouvert');b.setAttribute('aria-expanded','false');};
    b.addEventListener('click',function(){
      var ouvert=menu.getAttribute('data-ouvert')==='oui';
      if(ouvert){ferme();}else{menu.setAttribute('data-ouvert','oui');b.setAttribute('aria-expanded','true');}
    });
    document.addEventListener('keydown',function(e){if(e.key==='Escape')ferme();});
    document.addEventListener('click',function(e){if(!menu.contains(e.target))ferme();});
  }

  var racine=document.getElementById('sohaEstim');
  if(racine&&window.SOHA_ESTIM){
    var G=window.SOHA_ESTIM,RESA=window.SOHA_ESTIM_RESA||'#';
    var JOUR={sem:'Semaine',fds:'Fin de semaine'};
    var PLAGE={jour:'Journée',demi:'Demi-journée',soir:'Soirée'};
    var espace=racine.getAttribute('data-first'),jour='sem',plage='jour';
    var prix=racine.querySelector('#sePrice'),sel=racine.querySelector('#seSel'),cta=racine.querySelector('#seCta');
    function sync(){
      var e=G[espace],table=(jour==='fds')?e[3]:e[2],v=table[plage];
      prix.innerHTML=v.toLocaleString('fr-CA')+' $ <small>+tx</small>';
      sel.textContent=e[0]+' · '+JOUR[jour]+' · '+PLAGE[plage];
      cta.setAttribute('href',RESA+'?espace='+encodeURIComponent(espace)
        +'&jour='+encodeURIComponent(jour)+'&plage='+encodeURIComponent(plage)
        +'&tarif='+encodeURIComponent(v));
    }
    function groupe(id,poser){
      racine.querySelectorAll('#'+id+' button').forEach(function(b){
        b.addEventListener('click',function(){
          poser(b.getAttribute('data-k'));
          racine.querySelectorAll('#'+id+' button').forEach(function(x){x.classList.remove('on');});
          b.classList.add('on');sync();
        });
      });
    }
    groupe('seSpaces',function(v){espace=v;});
    groupe('seDay',function(v){jour=v;});
    groupe('seSlot',function(v){plage=v;});
    sync();
  }
})();
"""

GABARIT = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<meta name="description" content="{description}">
<meta name="robots" content="noindex, nofollow">
<meta property="og:type" content="website">
<meta property="og:title" content="{titre}">
<meta property="og:description" content="{description}">
<meta property="og:locale" content="fr_CA">
<link rel="stylesheet" href="assets/soha.css">
<link rel="preload" as="font" type="font/woff2" crossorigin href="assets/polices/schibsted-grotesk-v7-latin-regular.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin href="assets/polices/fraunces-v38-latin-600.woff2">
{prechargement}
</head>
<body class="soha-page soha-page-{corps}">
<a class="soha-saut" href="#soha-contenu">Aller au contenu</a>
{entete}
<main id="soha-contenu">
{contenu}
</main>
{pied}
<script src="assets/soha.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
#  Construction
# --------------------------------------------------------------------------
def construire(kit_dir, medias_dir, sortie, polices_dir=None):
    kit = Kit(kit_dir)
    medias = {}
    for r, _d, fs in os.walk(medias_dir):
        for f in fs:
            if f.lower().endswith((".webp", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".avif")):
                medias[f] = os.path.join(r, f)

    if os.path.isdir(sortie):
        shutil.rmtree(sortie)
    os.makedirs(os.path.join(sortie, "assets"), exist_ok=True)
    os.makedirs(os.path.join(sortie, "medias"), exist_ok=True)

    r = Rendu(kit, medias)

    # en-tête et pied, rendus une fois et partagés
    entete = "".join(r.element(e, 0) for e in (kit.entete["content"] if kit.entete else []))
    entete = '<header class="soha-entete">%s</header>' % entete
    r.premiere_image_posee = False
    pied = "".join(r.element(e, 0) for e in (kit.pied["content"] if kit.pied else []))
    pied = '<footer class="soha-pied">%s</footer>' % pied

    pages_ecrites = []

    # les 12 pages du kit
    for p in kit.pages.values():
        r.premiere_image_posee = False
        contenu = "".join(r.element(e, 0) for e in p["doc"]["content"])
        pre = ""
        prem = premiere_image(contenu)
        if prem:
            pre = '<link rel="preload" as="image" href="%s" fetchpriority="high">' % prem
        seo = METAS.get(p["id"])
        doc = GABARIT.format(
            titre=html.escape(seo[0] if seo else "%s — Centre Soha" % p["titre"]),
            description=html.escape(seo[1] if seo else re.sub(r"\s+", " ", p["extrait"])[:300]),
            corps=re.sub(r"[^a-z0-9]+", "-", (p["slug"] or "accueil").lower()).strip("-"),
            prechargement=pre, entete=entete, pied=pied, contenu=contenu)
        chemin = os.path.join(sortie, p["fichier"])
        open(chemin, "w", encoding="utf-8").write(doc)
        pages_ecrites.append(p["fichier"])

    # les 13 articles du Journal
    for a in kit.articles:
        r.premiere_image_posee = True      # la photo de l'article est posée à la main
        vign = r.media(a["vignette"]) if a["vignette"] else ""
        photo = ('<figure class="soha-article-photo"><img src="%s" alt="%s" '
                 'loading="eager" fetchpriority="high" decoding="async"></figure>'
                 % (vign, html.escape(a["titre"]))) if vign else ""
        corps = r.reecrire_html(a["contenu"])
        if "<p" not in corps:
            corps = "".join("<p>%s</p>" % html.escape(b.strip())
                            for b in corps.split("\n\n") if b.strip())
        signe = ('<p class="soha-article-surtitre">Journal · %s%s</p>'
                 % (date_fr(a["date"]),
                    (" · " + html.escape(a["auteur"])) if a["auteur"] else ""))
        contenu = ('<article class="soha-article">'
                   '<div class="soha-article-entete">%s<h1>%s</h1></div>%s'
                   '<div class="soha-article-corps">%s</div>'
                   '<p style="max-width:38rem;margin:0 auto">'
                   '<a class="soha-retour" href="%s">← Revenir au Journal</a></p>'
                   '</article>') % (signe, html.escape(a["titre"]), photo, corps, "journal.html")
        doc = GABARIT.format(
            titre=html.escape("%s — Journal du Centre Soha" % a["titre"]),
            description=html.escape(extrait_de(a["contenu"], 28)),
            corps="article",
            prechargement=('<link rel="preload" as="image" href="%s" fetchpriority="high">' % vign) if vign else "",
            entete=entete, pied=pied, contenu=contenu)
        open(os.path.join(sortie, a["fichier"]), "w", encoding="utf-8").write(doc)
        pages_ecrites.append(a["fichier"])

    # feuille de style et script
    css_global = (kit.reglages.get("settings") or {}).get("custom_css", "")
    open(os.path.join(sortie, "assets/soha.css"), "w", encoding="utf-8").write(r.feuille(css_global))
    open(os.path.join(sortie, "assets/soha.js"), "w", encoding="utf-8").write(JS)

    # médias réellement utilisés
    copiees = 0
    for nom in sorted(r.images_utilisees):
        shutil.copy2(medias[nom], os.path.join(sortie, "medias", nom))
        copiees += 1

    # les trois familles du canon, auto-hébergées : plus aucun appel à Google
    if polices_dir and os.path.isdir(polices_dir):
        os.makedirs(os.path.join(sortie, "assets/polices"), exist_ok=True)
        faces = []
        for f in sorted(os.listdir(polices_dir)):
            if not f.endswith(".woff2"):
                continue
            shutil.copy2(os.path.join(polices_dir, f), os.path.join(sortie, "assets/polices", f))
            famille = famille_de(f)
            if not famille:
                continue
            faces.append(face_css(famille, f, "polices/" + f))
        with open(os.path.join(sortie, "assets/soha.css"), "r+", encoding="utf-8") as fh:
            reste = fh.read()
            fh.seek(0)
            fh.write("/* ============================================================\n"
                     "   Les trois familles du canon, servies depuis le site lui-même.\n"
                     "   Aucun appel à Google : exigence Loi 25, et un aller-retour de\n"
                     "   moins avant le premier affichage.\n"
                     "   ============================================================ */\n"
                     + "\n".join(faces) + "\n\n" + reste)

    sommaire(sortie, list(kit.pages.values()), kit.articles)

    return {
        "pages": pages_ecrites,
        "images_copiees": copiees,
        "images_manquantes": dict(r.images_manquantes),
        "articles": len(kit.articles),
        "menu": kit.menu,
        "estimateur": r.estimateur_pose,
    }


# --------------------------------------------------------------------------
#  Le sommaire
# --------------------------------------------------------------------------
#  Le dossier livré contient vingt-neuf fichiers HTML et deux dossiers. Sans
#  porte d'entrée, on l'ouvre et on ne sait pas par où commencer — et on finit
#  par cliquer au hasard en croyant qu'il manque des pages. Celle-ci les nomme
#  toutes, dit ce que ce dossier est, et surtout ce qu'il n'est pas.

SOMMAIRE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Le site du 961, en HTML — sommaire</title>
<meta name="robots" content="noindex, nofollow">
<link rel="stylesheet" href="assets/soha.css">
<style>
/* Le site est en clair seulement — body y est #FBF8F3 sans variante sombre.
   Ce sommaire s'y tient : pas de bloc « prefers-color-scheme », sinon les
   listes passeraient au noir sur une page restée ivoire. */
.s-page{{max-width:62rem;margin:0 auto;padding:3rem 1.25rem 5rem}}
.s-titre{{font-family:"Fraunces",Georgia,serif;font-weight:500;
  font-size:clamp(2rem,5vw,2.9rem);line-height:1.05;margin:0 0 .6em}}
.s-chapeau{{max-width:40rem;font-size:1.05rem;line-height:1.6}}
.s-avis{{border-left:3px solid #AE1E3B;padding:1rem 1.15rem;margin:2rem 0;
  background:rgba(174,30,59,.05)}}
.s-avis p{{margin:0 0 .6em}} .s-avis p:last-child{{margin:0}}
.s-bloc{{margin-top:2.75rem}}
.s-bloc h2{{font-family:"Fraunces",Georgia,serif;font-weight:500;
  font-size:1.45rem;margin:0 0 .2em;padding-bottom:.5rem;border-bottom:1px solid #C7BCA8}}
.s-bloc>p{{margin:.7em 0 0;max-width:40rem;color:#5A6862;font-size:.95rem}}
.s-liste{{list-style:none;margin:1.1rem 0 0;padding:0;
  display:grid;gap:1px;background:#E2DACC;border-block:1px solid #E2DACC}}
.s-liste li{{background:#FBF8F3;padding:.7rem .2rem}}
/* `a{{color:inherit}}` dans la feuille du site : sans ceci, vingt-huit liens
   auraient l'air de vingt-huit titres en gras. */
.s-liste a{{color:#0F7FA6;font-weight:600;text-decoration:none;
  border-bottom:1px solid rgba(15,127,166,.35)}}
.s-liste a:hover,.s-liste a:focus-visible{{border-bottom-color:#0F7FA6}}
.s-liste code{{font-family:"DM Mono",ui-monospace,monospace;
  font-size:.8rem;color:#5A6862;display:block;margin-top:.15rem}}
.s-pied{{margin-top:3.5rem;padding-top:1.1rem;border-top:1px solid #C7BCA8;
  font-size:.88rem;color:#5A6862}}
</style>
</head>
<body class="soha-page">
<div class="s-page">
  <h1 class="s-titre">Le site du 961, en HTML</h1>
  <p class="s-chapeau">Les {n} pages du site, fabriquées en HTML simple :
  aucun WordPress, aucun Elementor, aucun appel vers l'extérieur. Tu peux
  l'ouvrir hors ligne, le copier sur une clé, l'envoyer à quelqu'un.</p>

  <div class="s-avis">
    <p><strong>Ceci ne s'installe pas.</strong> C'est la <em>référence</em> :
    ce à quoi le site doit ressembler après l'import du kit. Quand une page
    importée ne ressemble pas à celle d'ici, c'est l'import qui a un problème,
    pas la page.</p>
    <p>Les formulaires ne partent nulle part — il n'y a pas de serveur derrière.
    L'estimateur, lui, calcule pour de vrai.</p>
  </div>

  <div class="s-bloc">
    <h2>Commence ici</h2>
    <ul class="s-liste"><li><a href="index.html">L'accueil</a><code>index.html</code></li></ul>
    <p>Et à côté de ce dossier, <strong>soha-site-cliquable.html</strong> : le même
    site entier dans un seul fichier. Rien à décompresser, rien à installer — on
    l'ouvre, on clique dedans. C'est celui qu'on envoie à quelqu'un.</p>
  </div>

  <div class="s-bloc">
    <h2>Les pages</h2>
    <p>Dans l'ordre du kit, celui des identifiants WordPress.</p>
    <ul class="s-liste">{pages}</ul>
  </div>

  <div class="s-bloc">
    <h2>Le Journal</h2>
    <p>{na} articles, du plus récent au plus ancien.</p>
    <ul class="s-liste">{articles}</ul>
  </div>

  <p class="s-pied">Centre Soha · 961 Rachel Est, Montréal. Fabriqué le {jour}.
  Le pôle soha.live n'est pas concerné.</p>
</div>
</body>
</html>
"""


def sommaire(sortie, pages, articles):
    """Écrit « lisez-moi.html » : la porte d'entrée du dossier livré."""
    def ligne(titre, fichier, apres=""):
        return ('<li><a href="%s">%s</a>%s<code>%s</code></li>'
                % (fichier, html.escape(titre or fichier), apres, fichier))

    lignes_pages = "".join(
        ligne(p["titre"], p["fichier"]) for p in pages if p["fichier"] != "index.html")
    lignes_arts = "".join(
        ligne(a["titre"], a["fichier"]) for a in articles)

    doc = SOMMAIRE.format(
        n=len(pages) + len(articles),
        na=len(articles),
        pages=lignes_pages,
        articles=lignes_arts,
        jour=datetime.date.today().isoformat(),
    )
    open(os.path.join(sortie, "lisez-moi.html"), "w", encoding="utf-8").write(doc)
    return "lisez-moi.html"


def premiere_image(html_page):
    m = re.search(r'<img src="(medias/[^"]+)"', html_page)
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser(description="Fabrique le site du Centre Soha en HTML statique.")
    ap.add_argument("--kit", required=True, help="dossier du kit Elementor décompressé")
    ap.add_argument("--medias", required=True, help="dossier du kit médias décompressé")
    ap.add_argument("--polices", default=None, help="dossier de polices .woff2 (facultatif)")
    ap.add_argument("--sortie", default="site", help="dossier de sortie (défaut : site)")
    a = ap.parse_args()

    bilan = construire(a.kit, a.medias, a.sortie, a.polices)
    print("Site fabriqué dans « %s »" % a.sortie)
    print("  pages écrites      : %d (%d pages + %d articles)"
          % (len(bilan["pages"]), len(bilan["pages"]) - bilan["articles"], bilan["articles"]))
    print("  images copiées     : %d" % bilan["images_copiees"])
    print("  estimateur rendu   : %s" % ("oui" if bilan["estimateur"] else "non"))
    print("  entrées de menu    : %d" % len(bilan["menu"]))
    if bilan["images_manquantes"]:
        print("  IMAGES MANQUANTES  : %d" % len(bilan["images_manquantes"]))
        for n, c in sorted(bilan["images_manquantes"].items()):
            print("     %s (×%d)" % (n, c))
    else:
        print("  images manquantes  : aucune")
    return 0


if __name__ == "__main__":
    sys.exit(main())
