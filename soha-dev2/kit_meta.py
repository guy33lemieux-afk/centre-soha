#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — les 14 titres SEO entrent dans le kit.

Le constat, confirmé par trois sceptiques
-----------------------------------------
`build_site.py` porte une table METAS de 14 paires titre/description, écrites
à la main, bonnes. Elles ne servent QUE mon site de référence : les 16 pages
du kit portent toutes `"metadata": []`. Le manifeste liste pourtant Rank Math
comme extension installée.

Autrement dit : le travail est fait, et il ne part pas chez Mala. C'est
l'erreur de couche à l'état pur.

Le geste
--------
Les paires entrent dans le `metadata` de chaque page, aux clés Rank Math.
L'identifiant du fichier EST la clé de METAS : l'appariement est direct, sans
correspondance à deviner.

Le kit ne garantit pas la restauration des post_meta à l'import. Le script
écrit donc aussi `import-seo.php`, à passer une fois si les champs arrivent
vides — plutôt que 14 saisies à la main dans l'éditeur Rank Math.

    python3 kit_meta.py --kit <dossier> [--lire]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import METAS          # une seule source pour les 14 paires


def appliquer(kit, ecrire=True):
    journal, poses, deja = [], 0, 0
    for pid, (titre, desc) in sorted(METAS.items()):
        chemin = os.path.join(kit, "content", "page", "%d.json" % pid)
        if not os.path.exists(chemin):
            journal.append("meta : page %d absente du kit — ignorée" % pid)
            continue
        d = json.load(open(chemin, encoding="utf-8"))
        meta = d.get("metadata") or []
        cles = {m.get("key") for m in meta if isinstance(m, dict)}
        if "rank_math_title" in cles:
            deja += 1
            continue
        meta = [m for m in meta
                if not (isinstance(m, dict) and m.get("key", "").startswith("rank_math_"))]
        meta += [{"key": "rank_math_title", "value": titre},
                 {"key": "rank_math_description", "value": desc}]
        d["metadata"] = meta
        if ecrire:
            json.dump(d, open(chemin, "w", encoding="utf-8"),
                      ensure_ascii=False, separators=(",", ":"))
        poses += 1
    journal.append("meta : %d page(s) reçoivent titre + description, %d déjà là"
                   % (poses, deja))

    # Le filet de sécurité : si l'import ne restaure pas les post_meta.
    php = ["<?php",
           "/**",
           " * Centre Soha — les 14 titres et descriptions SEO.",
           " *",
           " * À passer UNE FOIS, et seulement si les champs Rank Math arrivent",
           " * vides après l'import du kit : un kit Elementor ne garantit pas la",
           " * restauration des post_meta. Les identifiants sont ceux du kit ;",
           " * si WordPress les a renumérotés à l'import, corriger la table.",
           " *",
           " *   wp eval-file import-seo.php      (ou coller dans un snippet, une fois)",
           " */",
           "",
           "$soha_seo = array("]
    for pid, (titre, desc) in sorted(METAS.items()):
        e = lambda s: s.replace("\\", "\\\\").replace("'", "\\'")
        php.append("    %d => array('%s', '%s')," % (pid, e(titre), e(desc)))
    php += [");",
            "",
            "foreach ($soha_seo as $id => $paire) {",
            "    if (!get_post($id)) {",
            "        printf(\"page %d introuvable — ignorée\\n\", $id);",
            "        continue;",
            "    }",
            "    update_post_meta($id, 'rank_math_title', $paire[0]);",
            "    update_post_meta($id, 'rank_math_description', $paire[1]);",
            "    printf(\"page %d : titre et description posés\\n\", $id);",
            "}",
            ""]
    chemin_php = os.path.join(kit, "import-seo.php")
    if ecrire:
        open(chemin_php, "w", encoding="utf-8").write("\n".join(php))
    journal.append("meta : import-seo.php écrit (%d paires)" % len(METAS))
    return journal


def main():
    ap = argparse.ArgumentParser(description="Les titres SEO entrent dans le kit.")
    ap.add_argument("--kit", required=True)
    ap.add_argument("--lire", action="store_true")
    a = ap.parse_args()
    for l in appliquer(a.kit, ecrire=not a.lire):
        print("   " + l)
    print("Terminé%s." % ("" if not a.lire else " (rien écrit)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
