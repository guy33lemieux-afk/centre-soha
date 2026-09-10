#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la politique dit vrai sur l'acheminement des courriels.

Constat du 10 septembre 2026, capture d'écran à l'appui : dans WP Mail SMTP,
**« Service d'envoi actuel : Par défaut (aucun) »**. Rien n'est configuré. Les
courriels de formulaire partent donc par la fonction d'envoi de PHP, c'est-à-dire
par le serveur de messagerie de l'hébergeur — celui de Toronto, déjà nommé juste
au-dessus dans la politique.

La phrase existante disait « le message transite par le service de messagerie
configuré ». Ce n'était pas faux au sens strict, c'était creux : elle laissait
croire qu'un service tiers avait été choisi et vérifié. La nouvelle nomme la
réalité, et elle a l'avantage d'être la plus rassurante des trois possibles —
aucun tiers ne voit passer le message.

Le jour où un relais est configuré (Brevo, SendLayer, le SMTP de l'hébergeur…),
cette phrase doit changer : le texte de remplacement est dans le lisez-moi qui
accompagne ce script, et il nomme le fournisseur et son pays.

Usage :
    python3 kit_messagerie.py --kit <dossier du kit>
"""

import argparse
import json
import os
import sys

PAGE = "7386"        # Politique de confidentialité

AVANT = ("<li><strong>WP Mail SMTP</strong> — achemine les formulaires vers notre boîte "
         "de courriel. Le message transite par le service de messagerie configuré, "
         "puis nous parvient.</li>")

APRES = ("<li><strong>La messagerie du site</strong> — les demandes envoyées par nos "
         "formulaires nous sont expédiées par le serveur de messagerie de notre "
         "hébergeur, à Toronto. <strong>Aucun service d'envoi tiers n'intervient</strong> : "
         "votre message ne transite par aucune autre entreprise que celle qui héberge "
         "le site. Votre demande est par ailleurs conservée dans la base de données du "
         "site, pour qu'elle ne se perde pas si un courriel n'arrive jamais.</li>")


def remplacer(noeud, avant, apres):
    n = 0
    for e in (noeud if isinstance(noeud, list) else noeud.get("elements", [])):
        for cle, valeur in (e.get("settings") or {}).items():
            if isinstance(valeur, str) and avant in valeur:
                e["settings"][cle] = valeur.replace(avant, apres)
                n += 1
        n += remplacer(e, avant, apres)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kit", required=True, help="dossier du kit Elementor")
    a = ap.parse_args()

    chemin = os.path.join(a.kit, "content", "page", PAGE + ".json")
    if not os.path.isfile(chemin):
        raise SystemExit("Page introuvable : %s" % chemin)

    page = json.load(open(chemin, encoding="utf-8"))
    n = remplacer(page.get("content", page), AVANT, APRES)
    if n != 1:
        raise SystemExit("La phrase de la messagerie : %d occurrence(s) au lieu d'une." % n)
    json.dump(page, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("   la politique nomme la messagerie de l'hébergeur, sans tiers")

    texte = open(chemin, encoding="utf-8").read()
    if "Aucun service d'envoi tiers" not in texte:
        raise SystemExit("La relecture ne retrouve pas le texte écrit.")
    if "WP Mail SMTP" in texte:
        raise SystemExit("Le nom d'une extension traîne encore dans la politique : "
                         "une personne qui lit n'a pas à connaître nos extensions.")
    print("   relu, et plus aucun nom d'extension dans la politique")
    return 0


if __name__ == "__main__":
    sys.exit(main())
