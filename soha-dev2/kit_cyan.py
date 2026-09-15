#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — le cyan de Soigner sort du Centre, fond par fond.

Le constat
----------
Le livre de bord de Mala : « Accent PAR ÉCOLE : Soigner #19A7DB · Bâtir
#D29A4E · Cultiver #5E8C5A » et « deux pôles jamais mélangés ». Les trois
écoles sont soha.live. Or le kit du Centre employait #19A7DB 264 fois — 59
fonds de bouton au survol, 56 bordures, 54 bordures de bouton au survol, 17
bordures d'élément, 7 titres, 5 bordures de bouton, 1 fond, et 12 fois dans
la feuille du kit. Toute la couleur du Centre était empruntée à une école de
l'autre pôle. Le conseil de la couleur (six regards, 15 septembre) : « le cyan
n'est pas l'accent du Centre, c'est son alibi ».

Ce que le script fait
---------------------
Il remonte le fond sous chaque élément (comme kit_soigner.py) et remplace
#19A7DB par la neutre du canon qui tient sur ce fond :
  · sur fond clair (ivoire, papier) : bordures et filets → encre #0E1A15
    (15,68) ; fond de bouton au survol → encre, et son texte → ivoire ;
  · sur fond sombre (encre, photo) : bordures et filets → ivoire #F4F0E7 ;
    fond de bouton au survol → ivoire, et son texte → encre.
La feuille du kit (custom_css) reçoit le même traitement, ligne par ligne.
Il ne pose aucun pigment : le Centre garde l'encre, l'ivoire, ses photos, et
le cramoisi du sceau. Le point cyan du logo est un FICHIER : il n'est pas touché.

Ce qu'il refuse
---------------
Toucher soha.live, un texte, une photo, ou proposer une teinte. Si une teinte
propre au Centre vient un jour, elle viendra d'un mur du 961, mesurée, décidée
par Mala — pas de ce script.

    python3 kit_cyan.py --kit <dossier> [--lire]
"""
import argparse, glob, json, os, re
from kit_soigner import clair

CYAN = "#19A7DB"; ENCRE = "#0E1A15"; IVOIRE = "#F4F0E7"
FONDS = ("background_color", "_background_color")
TEXTE_SURVOL = {"button_background_hover_color": "button_hover_color",
                "background_hover_color": "hover_color"}

def remplacer(s, fond, journal, page, eid):
    sombre = not clair(fond)
    n = 0
    for cle, val in list(s.items()):
        if isinstance(val, str) and val.upper() == CYAN:
            if cle in TEXTE_SURVOL:
                s[cle] = IVOIRE if sombre else ENCRE
                s[TEXTE_SURVOL[cle]] = ENCRE if sombre else IVOIRE
            elif cle in FONDS:
                s[cle] = ENCRE if not sombre else IVOIRE
                s["_soha_aplat_inverse"] = True       # marque : ses enfants changent de sol
            else:
                s[cle] = IVOIRE if sombre else ENCRE
            n += 1
    if n:
        journal.append((page, eid, "%d clé(s) · fond %s" % (n, fond or "ivoire")))
    return n

def en_ligne(s, fond, journal, page, eid):
    """Le cyan écrit EN DUR dans le HTML d'un widget (`style="background:#19A7DB"`,
    les tirets de 40×3 px, les filets de l'horaire, les soulignements du pied)
    reçoit la même neutre que le reste, selon le fond du widget."""
    neutre = IVOIRE if not clair(fond) else ENCRE
    n = 0
    def descendre(obj):
        nonlocal n
        if isinstance(obj, dict):
            for cle, val in list(obj.items()):
                if isinstance(val, str) and CYAN.lower() in val.lower():
                    obj[cle] = re.sub(re.escape(CYAN), neutre, val, flags=re.I); n += 1
                else:
                    descendre(val)
        elif isinstance(obj, list):
            for x in obj: descendre(x)
    descendre(s)
    if n:
        journal.append((page, eid, "%d chaîne(s) en ligne · fond %s" % (n, fond or "ivoire")))
    return n


def globales(kit, journal, ecrire):
    """Les couleurs globales du kit : « Cyan Soha » et ses dérivés ne désignent
    plus rien au Centre. Elles ne sont pas supprimées (une widget peut les
    référencer) : elles pointent vers une neutre du canon."""
    p = os.path.join(kit, "site-settings.json")
    d = json.load(open(p, encoding="utf-8")); st = d.setdefault("settings", {}); n = 0
    for liste in ("system_colors", "custom_colors"):
        for c in st.get(liste) or []:
            if (c.get("color") or "").upper() == CYAN:
                c["color"] = ENCRE; c["title"] = c.get("title", "") + " (retiré → encre)"; n += 1
            elif (c.get("color") or "").upper() == "#DDF0F5":
                c["color"] = "#FBF8F3"; c["title"] = c.get("title", "") + " (retiré → papier)"; n += 1
    if ecrire: json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    journal.append(("globales", "-", "%d couleur(s) globale(s) neutralisée(s)" % n))


TEXTES = ("title_color", "text_color", "button_text_color", "color", "heading_color",
          "description_color", "link_color", "meta_color", "excerpt_color", "icon_color")
BORDS = ("border_color", "_border_color", "button_border_color", "divider_color")

def inverser(noeud, journal, page):
    """Un aplat cyan sur page claire devient un aplat d'ENCRE : tout ce qu'il
    contenait en encre (lettres, filets) passe à l'ivoire, sinon encre sur
    encre — mesuré 1,00 sur « Retour à l'accueil » de la page introuvable."""
    n = 0
    s = noeud.get("settings") if isinstance(noeud.get("settings"), dict) else {}
    for cle in TEXTES + BORDS:
        if (s.get(cle) or "").upper() == ENCRE.upper():
            s[cle] = IVOIRE; n += 1
    for cle, val in list(s.items()):
        if isinstance(val, str) and cle not in TEXTES + BORDS and ENCRE.lower() in val.lower() and ("style=" in val or "{" in val):
            s[cle] = re.sub(re.escape(ENCRE), IVOIRE, val, flags=re.I); n += 1
    for e in noeud.get("elements") or []:
        n += inverser(e, journal, page)
    return n


def marcher(noeud, fond, journal, page):
    s = noeud.get("settings") if isinstance(noeud.get("settings"), dict) else {}
    ici = fond
    for f in FONDS:
        v = s.get(f)
        if isinstance(v, str) and v.startswith("#") and len(v) in (4, 7):
            ici = v
    if "soha-hero" in (s.get("_css_classes") or "").split() or isinstance(s.get("background_image"), dict):
        ici = ENCRE                                    # une photo voilée compte comme sombre
    n = remplacer(s, ici, journal, page, noeud.get("id"))
    for f in FONDS:                                   # le fond vient d'être remplacé : les enfants
        v = s.get(f)                                  # se posent sur la NOUVELLE valeur
        if isinstance(v, str) and v.startswith("#") and len(v) in (4, 7):
            ici = v
    n += en_ligne(s, ici, journal, page, noeud.get("id"))
    if s.pop("_soha_aplat_inverse", False):
        k = sum(inverser(e, journal, page) for e in noeud.get("elements") or [])
        if noeud.get("elType") == "widget":           # le fond est celui de la widget elle-même
            k += inverser(noeud, journal, page)
        journal.append((page, noeud.get("id"), "aplat → encre ; %d encre(s) → ivoire dessous" % k))
    for e in noeud.get("elements") or []:
        n += marcher(e, ici, journal, page)
    return n

def feuille(kit, journal, ecrire):
    p = os.path.join(kit, "site-settings.json")
    d = json.load(open(p, encoding="utf-8")); st = d.setdefault("settings", {})
    css = st.get("custom_css", ""); avant = css.count(CYAN) + css.count(CYAN.lower())
    # chaque règle : si elle vise un sol sombre (.soha-lieu, .soha-hero, encre) → ivoire, sinon encre
    def une(m):
        regle = m.group(0)
        sombre = any(k in regle for k in (".soha-lieu", ".soha-hero", "#0E1A15;", "background:#0E1A15"))
        return re.sub(re.escape(CYAN), IVOIRE if sombre else ENCRE, regle, flags=re.I)
    css = re.sub(r"[^{}]+\{[^}]*\}", une, css)
    st["custom_css"] = css
    if ecrire: json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    journal.append(("style", "-", "%d → %d occurrences" % (avant, css.upper().count(CYAN))))

def appliquer(kit, ecrire=True):
    journal, total = [], 0
    for f in sorted(glob.glob(os.path.join(kit, "content", "*", "*.json")) + glob.glob(os.path.join(kit, "templates", "*.json"))):
        doc = json.load(open(f, encoding="utf-8"))
        c = doc.get("content"); brut = isinstance(c, str); arbre = json.loads(c) if brut else c
        if not isinstance(arbre, list): continue
        n = sum(marcher(x, None, journal, os.path.basename(f)) for x in arbre)
        if n and ecrire:
            doc["content"] = json.dumps(arbre, ensure_ascii=False) if brut else arbre
            json.dump(doc, open(f, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        total += n
    feuille(kit, journal, ecrire)
    globales(kit, journal, ecrire)
    return journal, total

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--kit", required=True); ap.add_argument("--lire", action="store_true")
    a = ap.parse_args(); j, n = appliquer(a.kit, not a.lire)
    for l in j[-6:]: print("  %-14s %-10s %s" % l)
    print("%d clé(s) %s." % (n, "à changer" if a.lire else "changée(s)"))
