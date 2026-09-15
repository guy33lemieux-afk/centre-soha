#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — les neuf fiches et les onze cartes de cours deviennent une liste.

Le constat (département mise en page, 15 septembre)
----------------------------------------------------
« Se ressourcer » : douze cartes ivoire cernées d'un filet, identiques, en
grille de trois — 3 993 px de haut à 1440, 10 539 au téléphone. « Prendre soin
de soi » : neuf cartes en quatre colonnes. Vingt visages en médaillons de
132 px. C'est le tapis de cartes que la grille du goût note 0 (critère 4) :
« la page pourrait appartenir à n'importe qui ».

Ce que le script fait
---------------------
Chaque carte devient une LIGNE : portrait 200 px | identité | propos, un filet
entre chaque, aucun cadre. Le DOM garde son ordre (image, nom en premier
texte lu, propos, bouton). Les widgets sont répartis par CONTENU, pas par
position : le titre, le premier texte (nom / titre professionnel), les
« faits » (<dl class="faits">), <ul class="pratiques">, « Reçoit… »,
« Membre… » vont dans l'identité ; la présentation et le bouton dans le propos.
Un widget non reconnu va dans le propos, et le journal le dit.

Sur « Prendre soin de soi », trois fiches portent une photo de salle sous un
nom (Dominique Mennessier, Farah Quiroga, Yuv Baboolall). Le kit lui-même, sur
« Se ressourcer », place sous ces trois noms soha-portrait-*.webp : le script
aligne la fiche sur ce que Mala a déjà posé — aucune association nouvelle.
PORTRAITS_DEPUIS_7326 = False vide ces trois portraits au lieu de les aligner.

Ce qu'il refuse
---------------
Aucun texte, aucun ordre de widgets, aucune photo hors ces trois.

    python3 kit_fiches.py --kit <dossier> [--lire]
"""
import argparse, copy, glob, json, os, re

CIBLES = {"7326.json": "65e7c43e", "7339.json": "125c8de6"}
PORTRAITS_DEPUIS_7326 = True
DEBUT = "/* ==== soha-fiches début ==== */"; FIN = "/* ==== soha-fiches fin ==== */"
BLOC = DEBUT + """
/* ---- les fiches en liste · v01 : portrait | identité | propos ---- */
.soha-fiches{display:flex;flex-direction:column}
.soha-fiche{display:grid;grid-template-columns:200px minmax(0,280px) minmax(0,640px);column-gap:40px;
  align-items:start;border-top:1px solid #E0D8CA;padding:32px 0}
.soha-fiches > .soha-fiche:last-child{border-bottom:1px solid #E0D8CA}
.soha-fiche > .elementor-widget-image{grid-column:1;margin:0}
.soha-fiche > .e-con.soha-fiche-identite{grid-column:2}
.soha-fiche > .e-con.soha-fiche-propos{grid-column:3}
.soha-fiche .elementor-heading-title{margin-top:-4px}
/* les cartes étaient centrées ; une ligne se lit à gauche. Le portrait perd
   son médaillon (50 %) pour le seul rayon de la page, 2 px. */
.soha-fiche .soha-fiche-identite,.soha-fiche .soha-fiche-propos{align-items:flex-start}
.soha-fiche .soha-fiche-identite *,.soha-fiche .soha-fiche-propos *{text-align:left}
.soha-fiche .soha-fiche-identite .elementor-widget,.soha-fiche .soha-fiche-propos .elementor-widget{width:100%}
.soha-fiche .soha-fiche-identite ul{padding-left:1.1em;margin:0}
.soha-fiche .soha-fiche-identite dl.faits{display:grid;grid-template-columns:auto 1fr;column-gap:12px;row-gap:4px;margin:0}
.soha-fiche .soha-fiche-identite dl.faits dt{font-family:"DM Mono",ui-monospace,monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#5A6460;padding-top:3px}
.soha-fiche .soha-fiche-identite dl.faits dd{margin:0}
.soha-fiche .soha-fiche-propos .elementor-button-wrapper{justify-content:flex-start}
.soha-fiche .soha-fiche-portrait img{border-radius:2px;width:100%;height:auto;aspect-ratio:1/1;object-fit:cover}
@media (max-width:1024px){.soha-fiche{grid-template-columns:160px minmax(0,1fr);row-gap:16px}
  .soha-fiche > .e-con.soha-fiche-propos{grid-column:2}}
/* au téléphone : une colonne. Les sélecteurs portent la même spécificité que
   ceux du bureau (.e-con.soha-fiche-propos), sinon « propos » reste en
   colonne 2 et la piste 1 tombe à 0 px — mesuré : cols « 0px 348px ». */
@media (max-width:767px){.soha-fiche{grid-template-columns:1fr;row-gap:16px}
  .soha-fiche > .e-con.soha-fiche-identite,.soha-fiche > .e-con.soha-fiche-propos{grid-column:1}
  .soha-fiche > .elementor-widget-image{grid-column:1;width:160px;max-width:160px}}
""" + FIN + "\n"

def identite_ou_propos(w):
    t = w.get("widgetType"); s = w.get("settings") or {}
    if t == "heading": return "identite"
    if t == "text-editor":
        ed = s.get("editor") or ""
        texte = re.sub(r"<[^>]+>", "", ed).strip()
        if 'class="faits"' in ed or 'class="pratiques"' in ed: return "identite"
        if texte.startswith(("Reçoit", "Membre")): return "identite"
        if len(texte) < 90 and "<p" not in ed.replace("<p>", "", 1): return "identite"   # nom / titre pro : une ligne
        return "propos"
    return "propos"

def portraits_7326(kit):
    """nom affiché → url du portrait, tel que le kit le pose déjà sur 7326."""
    d = json.load(open(os.path.join(kit, "content/page/7326.json"), encoding="utf-8"))
    c = d["content"]; c = json.loads(c) if isinstance(c, str) else c
    table = {}
    def w(n):
        if n.get("elType") == "container":
            img = None; noms = []
            for e in n.get("elements") or []:
                if e.get("widgetType") == "image": img = (e["settings"].get("image") or {})
                if e.get("widgetType") == "text-editor": noms.append(re.sub(r"<[^>]+>", "", e["settings"].get("editor", "")).strip())
            if img and img.get("url") and "portrait" in img["url"]:
                for nom in noms: table[nom] = img
        for e in n.get("elements") or []: w(e)
    for x in c: w(x)
    return table

def convertir(grille, journal, page, portraits):
    gs = grille.setdefault("settings", {})
    gs["flex_direction"] = "column"; gs["flex_wrap"] = "nowrap"; gs["flex_gap"] = {"unit": "px", "size": 0, "column": "0", "row": "0", "isLinked": True}
    gs["_css_classes"] = " ".join(sorted(set((gs.get("_css_classes") or "").split()) | {"soha-fiches"}))
    n = 0
    for carte in grille.get("elements") or []:
        s = carte.setdefault("settings", {})
        if "soha-fiche" in (s.get("_css_classes") or "").split(): continue
        for k in ("width", "width_tablet", "width_mobile"): s[k] = {"unit": "%", "size": 100}
        for k in ("background_background", "background_color", "border_border", "border_width", "border_color", "border_radius", "overflow"): s.pop(k, None)
        s["padding"] = {"unit": "px", "top": "0", "bottom": "0", "left": "0", "right": "0", "isLinked": True}
        s["_css_classes"] = " ".join(sorted(set((s.get("_css_classes") or "").split()) | {"soha-fiche"}))
        enfants = carte.get("elements") or []
        if not enfants: continue
        img = enfants[0] if enfants[0].get("widgetType") == "image" else None
        reste = enfants[1:] if img else enfants
        if img:
            isg = img.setdefault("settings", {})
            isg["width"] = {"unit": "px", "size": 200}; isg["width_mobile"] = {"unit": "px", "size": 160}
            isg["_css_classes"] = " ".join(sorted(set((isg.get("_css_classes") or "").split()) | {"soha-fiche-portrait"}))
            url = ((isg.get("image") or {}).get("url") or "")
            if page == "7339.json" and "portrait" not in url:
                nom = next((re.sub(r"<[^>]+>", "", e["settings"].get("title") or e["settings"].get("editor", "")).strip()
                            for e in reste if e.get("widgetType") == "heading"), "")
                if PORTRAITS_DEPUIS_7326 and nom in portraits:
                    isg["image"] = copy.deepcopy(portraits[nom]); journal.append((page, carte.get("id"), "portrait aligné sur 7326 : %s" % nom))
                else:
                    isg["image"] = {"id": "", "url": ""}; journal.append((page, carte.get("id"), "photo de salle retirée sous %s" % nom))
        ident = {"id": (carte.get("id") or "f")[:6] + "i", "elType": "container", "isInner": True, "elements": [],
                 "settings": {"content_width": "full", "flex_direction": "column", "flex_gap": {"unit": "px", "size": 8, "column": "8", "row": "8", "isLinked": True}, "_css_classes": "soha-fiche-identite"}}
        propos = {"id": (carte.get("id") or "f")[:6] + "p", "elType": "container", "isInner": True, "elements": [],
                  "settings": {"content_width": "full", "flex_direction": "column", "flex_gap": {"unit": "px", "size": 12, "column": "12", "row": "12", "isLinked": True}, "_css_classes": "soha-fiche-propos"}}
        inconnus = 0
        for w in reste:
            ou = identite_ou_propos(w)
            if w.get("elType") == "container": ou = "propos"
            elif w.get("widgetType") not in ("heading", "text-editor"): inconnus += 1; ou = "propos"
            (ident if ou == "identite" else propos)["elements"].append(w)
        carte["elements"] = ([img] if img else []) + [ident, propos]
        n += 1
        if inconnus: journal.append((page, carte.get("id"), "%d widget(s) non reconnu(s) → propos" % inconnus))
    journal.append((page, grille.get("id"), "%d ligne(s)" % n))
    return n

def poser_style(kit):
    p = os.path.join(kit, "site-settings.json"); d = json.load(open(p, encoding="utf-8")); st = d.setdefault("settings", {})
    css = st.get("custom_css", "")
    if DEBUT in css: css = css[:css.index(DEBUT)] + css[css.index(FIN) + len(FIN):]
    st["custom_css"] = css + BLOC
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--kit", required=True); ap.add_argument("--lire", action="store_true"); a = ap.parse_args()
    journal = []; portraits = portraits_7326(a.kit)
    def find(n, i):
        if n.get("id") == i: return n
        for e in n.get("elements") or []:
            r = find(e, i)
            if r: return r
    for page, gid in CIBLES.items():
        p = os.path.join(a.kit, "content/page", page); d = json.load(open(p, encoding="utf-8"))
        c = d["content"]; brut = isinstance(c, str); arbre = json.loads(c) if brut else c
        g = next((find(x, gid) for x in arbre if find(x, gid)), None)
        if not g: journal.append((page, gid, "introuvable")); continue
        convertir(g, journal, page, portraits)
        if not a.lire:
            d["content"] = json.dumps(arbre, ensure_ascii=False) if brut else arbre
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    if not a.lire: poser_style(a.kit)
    for l in journal: print("  %-10s %-10s %s" % l)
if __name__ == "__main__": main()
