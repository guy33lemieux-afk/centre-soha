#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la porte des formulaires et des mauvais chemins (états · v01).

Constat du 15 septembre 2026, captures regard_etats/ ouvertes : sur les 30 pages
de site29, 0 `role="alert"`, 0 `aria-live` ; un envoi vide ne dit rien et ne
bouge le focus nulle part. Sur contact, espaces-professionnels, studio-podcast
et reservation, deux champs portent le même id (« courriel », « consentement »)
parce que le pied de page répète les custom_id de la page. Sur reservation, les
quatre champs `hidden` de l'estimateur sont rendus comme des champs texte
visibles. Le libellé de consentement est un flex : le lien « politique de
confidentialité » se détache en colonne et la parenthèse reste seule.

Ce que cette porte mesure, page par page, à 360 et à 1440 (Chromium) :
  1. ids en double                                  → 0
  2. champs visibles sans <label for=…> lié         → 0 (hidden exclus)
  3. type="hidden" du kit rendu visible             → 0
  4. cibles : champ ≥ 44 px de haut, police ≥ 16 px → 0 défaut
  5. case de consentement non pré-cochée, un lien vers confidentialite → 0 défaut
  6. envoi vide : ≥ 1 role="alert"/aria-live visible, focus sur le premier
     champ invalide, aria-describedby posé sur lui  → 0 défaut
  7. 404 : page-introuvable.html a ≥ 1 <img> avec width/height/alt,
     ≥ 5 liens de sortie dans <main>, 1 seul rayon   → 0 défaut
Sort 1 au premier défaut. Elle DOIT échouer sur site29 tel quel (état cassé
connu) avant qu'on croie son zéro.

Ce qu'elle refuse de faire : juger le contraste (porte_du_contraste.py),
tester WordPress lui-même (elle lit le site de référence ; le kit est la source).

Usage :
    PW_CHROMIUM=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \\
    python3 porte_des_formulaires.py --site <dossier site29> [--pages contact,reservation]
"""
import argparse, os, sys, json

PAGES = ["contact", "reservation", "espaces-professionnels", "studio-podcast", "page-introuvable"]

JS = r"""
() => {
  const q = s => [...document.querySelectorAll(s)];
  const vis = e => { const r = e.getBoundingClientRect(); const c = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && c.display !== 'none'; };
  const d = {defauts: []};
  // 1. ids en double
  const ids = q('[id]').map(e => e.id), seen = {}, dup = new Set();
  ids.forEach(i => { if (seen[i]) dup.add(i); seen[i] = 1; });
  d.ids_double = [...dup]; if (dup.size) d.defauts.push('ids en double : ' + [...dup].join(', '));
  // 2-4. champs
  const champs = q('form input, form select, form textarea').filter(e => e.type !== 'submit');
  d.champs = champs.length;
  champs.forEach(e => {
    const t = (e.getAttribute('type') || e.tagName).toLowerCase();
    if (t === 'hidden') return;
    if (/^estim_/.test(e.name) && vis(e)) d.defauts.push('champ caché rendu visible : ' + e.name);
    const lab = (e.id && document.querySelector('label[for="' + CSS.escape(e.id) + '"]')) || e.closest('label');
    if (!lab) d.defauts.push('champ sans label : ' + (e.name || e.id));
    if (t === 'checkbox' || t === 'radio') {
      if (t === 'checkbox' && e.checked) d.defauts.push('case pré-cochée : ' + e.name);
      const boite = (e.closest('label') || e).getBoundingClientRect();
      if (boite.height < 24) d.defauts.push('case < 24 px : ' + e.name);
      return;
    }
    const r = e.getBoundingClientRect(), fs = parseFloat(getComputedStyle(e).fontSize);
    if (r.height < 44) d.defauts.push('champ < 44 px : ' + e.name + ' (' + Math.round(r.height) + ')');
    if (fs < 16) d.defauts.push('police < 16 px : ' + e.name + ' (' + fs + ')');
  });
  // 5. consentement
  q('form').forEach((f, i) => {
    const cases = q('input[type=checkbox]', f).filter(c => /consent/.test(c.name));
    if (!cases.length) return;
    const lien = cases.some(c => (c.closest('label') || c.parentElement).querySelector('a[href*="confidentialite"]'));
    if (!lien) d.defauts.push('consentement sans lien confidentialité (formulaire ' + i + ')');
  });
  // 6. envoi vide sur le premier formulaire de <main>
  const f = document.querySelector('main form');
  if (f) {
    const btn = f.querySelector('button[type=submit], [type=submit]');
    if (btn) btn.click();
    const alertes = q('[role=alert],[aria-live]').filter(vis);
    d.alertes_visibles = alertes.length;
    if (!alertes.length) d.defauts.push('envoi vide : aucune erreur annoncée (role=alert / aria-live visible)');
    const actif = document.activeElement;
    const premier = q('[required]', f).find(e => !e.checkValidity || !e.checkValidity());
    if (premier && actif !== premier) d.defauts.push('envoi vide : le focus n\'est pas sur le premier champ invalide (' + (premier.name || premier.id) + ')');
    if (premier && !premier.getAttribute('aria-describedby')) d.defauts.push('envoi vide : aria-describedby absent sur ' + (premier.name || premier.id));
  }
  // 7. 404
  if (document.body.classList.contains('soha-page-page-introuvable')) {
    const imgs = q('main img');
    if (!imgs.length) d.defauts.push('404 : aucune photo du 961');
    imgs.forEach(im => { if (!im.getAttribute('width') || !im.getAttribute('height') || !im.getAttribute('alt')) d.defauts.push('404 : img sans width/height/alt'); });
    const sorties = new Set(q('main a[href]').map(a => a.getAttribute('href')));
    d.sorties = [...sorties];
    if (sorties.size < 5) d.defauts.push('404 : ' + sorties.size + ' sortie(s), il en faut ≥ 5');
    const rayons = new Set(q('main a, main button').map(e => getComputedStyle(e).borderRadius).filter(r => r !== '0px'));
    if (rayons.size > 1 || (rayons.size === 1 && ![...rayons][0].startsWith('2px'))) d.defauts.push('404 : rayons ' + [...rayons].join(' '));
  }
  return d;
}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--pages", default=",".join(PAGES))
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    chrome = os.environ.get("PW_CHROMIUM")
    total = 0
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome) if chrome else p.chromium.launch()
        for page in a.pages.split(","):
            f = os.path.join(os.path.abspath(a.site), page + ".html")
            if not os.path.exists(f):
                print("ABSENT  ", page); total += 1; continue
            for w in (360, 1440):
                pg = b.new_page(viewport={"width": w, "height": 900})
                pg.goto("file://" + f); pg.wait_for_timeout(300)
                d = pg.evaluate(JS); pg.close()
                etat = "OK    " if not d["defauts"] else "DÉFAUT"
                print("%s %-24s @%-4d champs=%s alertes=%s ids_double=%s" % (
                    etat, page, w, d.get("champs"), d.get("alertes_visibles"), d.get("ids_double")))
                for x in d["defauts"]:
                    print("        - " + x)
                total += len(d["defauts"])
        b.close()
    print("\n%d défaut(s)" % total)
    sys.exit(1 if total else 0)

if __name__ == "__main__":
    main()
