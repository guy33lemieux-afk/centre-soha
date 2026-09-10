# Centre Soha — cycle du 10 septembre 2026

## Ce qui a été livré
- `soha_kitdev_20260910_v06.zip` — kit Elementor corrigé (base : kit v04 du 7 sept).
- `soha_extensionestimateur_20260910_v201.zip` — estimateur, bouton final recâblé.
- `base-neuve.html` — analyse + marche à suivre en 7 étapes.

## Cause racine, établie par comparaison de fichiers
Le kit v04 (7 sept) référence 59 images aux noms nets. L'export réel du site
(9 sept) référence les **mêmes 59 images**, toutes renommées `-1`. 59/59, sans
exception.

→ Mécanique : les médias étaient **téléversés avant l'import**. L'import
retélécharge chaque image depuis sa propre adresse, WordPress trouve le nom pris,
ajoute `-1`, et recâble les pages vers la copie. D'où les doublons d'images ET,
par le même geste répété, les 24 pages (12 × 2), les 2 menus, les 2 en-têtes,
les 2 pieds de page, les 14 gabarits TEC.

**La consigne « téléverser AVANT import » du `_medias.csv` est la cause, pas le
remède.** Nouvelle règle : médiathèque vide, aucun téléversement, l'import va
chercher les images sur le `/dev` qui reste en ligne.

## Correctifs appliqués dans le kit v05
| Correctif | Nombre |
|---|---|
| Liens de page recâblés `/dev/` → `/dev2/` | 73 |
| Boutons d'atelier recâblés vers leur vrai événement | 5 |
| Ancre morte `#horaire` → `#soha-semaine` | 1 |
| Conteneur vide retiré de l'en-tête | 1 |
| Adresses d'images laissées sur `/dev` (source de l'import) | 65 |

Tous les JSON du kit se relisent sans erreur. `php -l` passe sur l'extension.

## Audit, en chiffres
- 107 liens et boutons relevés sur 12 pages + en-tête + pied de page.
- Vues du kit : téléphone < 768, tablette 768–1024, ordi ≥ 1025 ; cadre 1200 px.
- 0 élément masqué sur une vue, 0 rangée qui refuse de s'empiler.
- 21 largeurs figées en px = portraits 132 px + logo de pied 120 px (sans danger).
- CSS global : `clamp()` sur h1/h2/h3, `safe-area-inset`, cibles 44 px ≤ 1024 px.
- Manque de fond : `prefers-reduced-motion` déclaré nulle part.

## Extensions maison — ce qui agit vraiment
- **Estimateur** : `[soha_estimateur]`, présent une fois (Espaces professionnels). Requis.
- **Finition** : aucun raccourci, agit partout (a11y, alt, LCP, témoins). Requis.
- **Praticien·nes (CMS)** et **Centre (shortcodes)** : 8 raccourcis déclarés,
  **aucun présent dans le kit**. Les installer ne rend rien visible. Dormantes.

## Reste à trancher
1. Trois ateliers annoncés sans fiche (`activation-de-lenergie-sacree`,
   `atelier-decriture-spontanee`, `core-energetics-coeur-et-bassin`).
2. Quatre `.mp4` de visite virtuelle présents seulement sur `/dev` (`uploads/2026/06/`).
3. Contact et Première visite absents du menu (pied de page seulement).

## La leçon pour le prochain cycle
Avant toute procédure d'installation, **comparer deux exports successifs**. C'est la
comparaison — pas la lecture d'un seul export — qui a désigné le geste fautif en une
ligne. Et un correctif ne vaut que s'il supprime une étape manuelle : ce cycle retire
le téléversement des médias.


---

# Complément du 10 septembre — cinq fichiers de plus

Reçus après la première livraison : `soha_event.zip`, trois pages du /dev
sauvegardées en HTML, et le jeu de polices Schibsted Grotesk v7.

## Les trois « pages manquantes » n'en étaient pas
`soha_event.zip` contient les quatre fiches d'atelier. Ce sont des **événements
du site de production**, pas des pages de /dev :

| slug attendu par le kit | vraie adresse |
|---|---|
| `activation-de-lenergie-sacree` | `centresoha.com/event/activation-energie-sacree-kundalini/` |
| `atelier-decriture-spontanee` | `centresoha.com/event/atelier-decriture-spontanee/` |
| `core-energetics-coeur-et-bassin` | `centresoha.com/event/atelier-core-energetics-sexualite-union-coeur-bassin/` |

→ Kit **v06** : les 5 boutons pointent vers ces adresses réelles, en nouvel
onglet (`is_external: on`). Le repli vers `#evenements` du v05 est retiré.
**107 liens relevés, 0 cassé.**

## Les trois pages HTML sont une AUTRE génération du /dev
IDs 884–1015, slugs `le-studio-podcast`, `les-espaces`, `prendre-soin-de-soi` —
distincts du kit (7319–7388) et de l'export dev_2 (208–317). Trois générations
coexistent donc dans l'historique du /dev.

Défauts de cette génération, que le kit a déjà corrigés :
- **aucun H1** sur *Les Espaces* et *Prendre soin de soi* (le héros est un h2) ;
- **trois H1 sur le Studio**, et ce sont les trois prix (`300 $`, `360 $`, `420 $`) ;
- 21 éléments masqués par `elementor-hidden-tablet` / `-mobile` (en-tête/pied) ;
- images sans `width`/`height` (10/20 sur Espaces) → risque de CLS ;
- 10 images sans attribut `alt` du tout sur Espaces.

Contrôle du kit v06 : **un seul H1 par page, sur les douze**, texte juste à
chaque fois. Ordre des titres propre (h6 surtitre → h1 → h2 → h3).

Seule perte de contenu réelle : le bloc **partenaires** (« Ils nous font
confiance ») de l'ancienne page Espaces. Les témoignages ont survécu, reformulés.

## Polices : le zip ne couvre qu'un tiers du besoin
Familles demandées par le kit : **Schibsted Grotesk** ×395 (300/400/500/600/700/800),
**Fraunces** ×151 (300/400/500/**600 ×128**/700 + italique), **DM Mono** ×32 (400/500).

Le zip fourni ne contient que Schibsted (400/500/600/700/italique).
**Rien n'a été câblé, volontairement** : héberger Schibsted seul pendant que
Fraunces vient encore de Google ferait charger la police deux fois — plus lent,
et zéro gain Loi 25 puisque l'appel à Google subsiste.

À demander : Fraunces (300/400/500/600/700 + italique) et DM Mono (400/500) en
`.woff2`. Les trois se câblent alors d'un coup dans l'extension Finition.

## Leçon du complément
Un lien « mort » n'est pas toujours une page manquante : vérifier le **type de
contenu** avant de conclure. Trois fiches d'atelier existaient depuis le début,
sous `/event/`. Et avant de livrer un demi-correctif (une police sur trois),
mesurer s'il ne dégrade pas ce qu'il prétend améliorer.

---

# Complément 2 du 10 septembre — le site en HTML

Reçus : `soha_generateur_20260825_v10.zip` (6 scripts), `soha_pagesjson_20260825_v02.zip`
(28 pages), les deux pages d'accueil sauvegardées, et de nouveau l'estimateur v2.0.0.

## Pourquoi le site est bâti depuis le kit, pas depuis pagesjson
`pagesjson v02` contient 28 pages (dont les 13 articles et les 4 ateliers) — mais
ses 95 images portent des noms à empreinte (`soha-accueil-picto-0def2c.webp`) qui
**n'existent dans aucun kit fourni : zéro correspondance** avec le kit médias.
Le kit v06/v07, lui, référence 65 images qui correspondent toutes. Bâtir depuis
pagesjson aurait donné 95 carrés gris.

## Le générateur : `build_site.py`
Lit le kit + le kit médias → 25 pages HTML autonomes (12 pages + 13 articles tirés
du WXR). Rend le **balisage réel d'Elementor** et applique le CSS global du kit tel
quel : ce qui est rendu est ce que WordPress rendra.

    python3 build_site.py --kit <kit> --medias <medias> [--polices <woff2>] --sortie site

Couvre conteneur, titre, texte, image, bouton, séparateur, formulaire, accordéon,
témoignage, liste d'articles, menu — et porte l'estimateur en statique (24 tarifs).

## Ce que la mesure au navigateur a trouvé (100 rendus : 25 pages × 4 largeurs)
Quatre défauts invisibles à la lecture des fichiers, tous corrigés **dans le CSS
global du kit** pour que WordPress en profite aussi :

| Défaut | Mesure | Correctif |
|---|---|---|
| Case de consentement | 13 × 13 px (min. WCAG 2.5.8 : 24) | `flex:none` + 24 × 24 |
| Liens du pied de page | 14 px de haut sur téléphone | `min-height:44px` sous 767 px |
| Adresse web de 96 car. | débordement de 22 px à 360 px | `overflow-wrap:break-word` |
| Dates des 13 articles | toutes à 2026-08-29 (date d'import) | vraies dates 2021-2023 rétablies |

La case de consentement rétrécissait parce qu'elle est un élément flexible à côté
d'un long texte : fixer `width` ne suffit pas, il faut `flex:none`.

Résultat final : **0 débordement horizontal sur 100 rendus, 0 image en échec sur
127, un seul H1 sur chacune des 25 pages, 608 liens internes vérifiés sans un seul
cassé.**

## Réserve
Le site appelle encore Google pour Fraunces et DM Mono. Schibsted Grotesk est
auto-hébergée (fichier fourni). Il manque les deux autres familles en `.woff2`.

## Leçon
**Lire les fichiers ne remplace pas le rendu.** Les quatre défauts de ce cycle —
dont une case de consentement sous le minimum légal — étaient invisibles dans le
JSON et évidents dès la première mesure au navigateur. Toute livraison web passe
désormais par la porte du regard : capturer, mesurer, puis seulement conclure.

---

# Complément 3 du 10 septembre — l'ordre, et deux corrections

Reçus : 30 envois au total (20 archives + 10 documents seuls), soit 20 textes
plus le matériel du site. Périmètre rappelé par Mala : **Centre Soha seulement**,
pas soha.live.

## L'ordre (livrable `ordre.html`)
Les 30 envois classés en 5 états — autorité / matière / à corriger / périmé /
hors périmètre — répartis en 6 familles, avec l'arborescence de rangement.
Règle : **un rôle, un seul fichier vivant** ; le reste descend dans `_archive`.

## Les sept verdicts du Grand Conseil (mesurés, pas supposés)
1. **Infolettre v04 = 809 Ko.** Gmail coupe à 102 Ko. Les images encodées
   commencent à 788 Ko et **le lien de désabonnement est à 808 Ko** — donc
   invisible. Ce n'est pas un problème de poids mais de Loi 25. → garder la
   v01 du 7 sept (6 Ko).
2. **Le nom composé à la main** (« Centre S<o coloré>ha ») dans 3 documents.
   Canon : câbler le logo hébergé, jamais recomposer le nom.
3. **Un second cyan** `#046C86` : 17× page Ateliers, 65× kit. → corrigé.
4. **Quatre documents HTML composés en Inter** — la maison écrit sa charte
   dans une police qui n'est pas la sienne.
5. **La page Ateliers ne mène nulle part** : 6 boutons vers `#`, 6 liens vers
   des pages inexistantes, 8 visuels en réserve. Et elle double « Se transformer ».
6. **Deux consentements** dans la recette /reservation/ : juste, à ne pas
   simplifier. Et j'avais dévié une décision déjà prise (voir plus bas).
7. **Contre-verdict** : la police Georgia/Arial de l'infolettre n'est PAS une
   faute — les clients mail ne chargent pas les polices web, et le guide
   l'explique. Ne pas « corriger » ce qui est bien fait.

## Corrections livrées
- **Kit v08** : `#046C86` → `#19A7DB`, 65 remplacements dans 13 fichiers.
  Plus 3 dans le socle du générateur. Il n'en reste aucun nulle part.
- **Estimateur v2.0.2** : destination rendue à `/reservation/`, conformément à
  la décision de l'index du 7 sept. Ma v2.0.1 l'avait détournée vers `#demande`
  parce que la page n'existait pas — c'était la page à monter, pas la
  destination à changer. Le vrai défaut de la v2.0.0 (chemin racine `/reservation/`
  qui pointait la production depuis un sous-dossier) est corrigé par `home_url()`.
- **Page `/reservation/` montée** d'après la recette : 13 champs dans l'ordre,
  2 consentements distincts, aucun pré-coché. Kit → 13 pages, site → 26 pages.

Contrôles : 628 liens internes, 0 cassé · 155 ressources, 0 manquante ·
0 débordement horizontal · un seul H1 par page.

## Leçon
**Le dossier de décisions prime sur mon raisonnement.** J'avais tranché seul une
destination déjà arbitrée. Lire l'index avant d'agir, pas après. Et un contrôle
automatique ne remplace pas le jugement : la « faute » de police de l'infolettre
était la bonne décision.

---

# Complément 4 du 10 septembre — « go pour tout »

## Les trois ateliers sont des pages (kit v09)
Montés depuis `pagesjson v02` : palette remise au canon (46 corrections :
`#16241F`→`#0E1A15`, `#FAFAF8`→`#F4F0E7`, `#046C86`→`#19A7DB`), 11 liens
recâblés vers `/dev2/`, identifiants d'éléments réattribués, un H1 juste par
page. Une seule des trois images existait dans le kit médias
(`soha-evenement-atelier-core-energetics-107.webp`) ; les deux autres widgets
image sont retirés plutôt que laissés cassés.

Les 5 boutons « Voir le détail / Voir l'atelier » pointent maintenant vers ces
pages internes. **Plus aucun lien ne sort vers `centresoha.com/event/`.**

Kit : 16 pages · Site : 29 pages (16 + 13 articles).

## La feuille de maison (`build_documents.py`)
Un outil, une feuille de style, sept documents recomposés dans le canon v06.
Rendu Markdown maison (titres, listes, tableaux, citations, code, filets) — zéro
dépendance. Plus une ligne d'Inter : seules `--serif`, `--sans`, `--mono` sont
déclarées, en clair et en sombre.

## Métas SEO posées
Les 15 titres + descriptions rédigés sont câblés page par page dans le
générateur. Confidentialité et Page introuvable restent sans méta marketing.

## Décision tranchée : la page Ateliers est retirée
« Se transformer » vit. Elle est dans le menu, dans le kit, et elle a désormais
trois vraies fiches derrière elle. La maquette Ateliers promettait exactement ce
que Se transformer livre maintenant, mais avec 12 liens morts et 8 visuels en
réserve. Son bon apport — les filtres par type — est noté pour un cycle ultérieur.

## Un défaut trouvé par la mesure, corrigé à la source
Les trois pages d'atelier débordaient à **768 px** : un conteneur de 900 px de
large sans palier tablette. Le correctif n'est pas sur ces pages mais dans le
générateur — toute largeur figée est désormais bornée par
`max-width:min(<largeur>, 100%)`. La règle protège toutes les pages, y compris
celles à venir.

**Porte finale : 116 rendus (29 pages × 4 largeurs), 0 débordement, 0 image en
échec sur 136, un seul H1 partout, 702 liens internes sans un cassé.**

## Ce qui reste bloqué, et pourquoi
- **Fraunces + DM Mono en `.woff2`** : je ne peux pas les fabriquer. Sans elles,
  le site appelle encore Google et la Loi 25 reste en suspens sur ce point.
- **Deux champs de la politique de confidentialité** : WP Mail SMTP et
  l'extension Newsletter sont dans la liste des extensions, mais on ne publie
  pas une politique sur une vraisemblance, et une durée de conservation ne
  s'invente pas.

## Leçon
**Un correctif se pose à la source, pas sur le symptôme.** Le débordement à
768 px venait de trois pages ; la règle qui l'empêche vit maintenant dans le
générateur et couvre tout ce qui sera produit ensuite. Même logique pour la
feuille de maison : on ne répare pas quatre documents, on écrit l'outil qui
fait que le cinquième naît déjà juste.

---

# Complément 5 du 10 septembre — les polices, et la fin de l'appel à Google

Reçus : Fraunces v38 (deux archives **complémentaires**, pas des doublons : les
graisses d'un côté, l'italique de l'autre), DM Mono v16, Schibsted Grotesk v7.
Douze fichiers `.woff2`, 276 Ko au total.

## Couverture réelle
| Famille | Usages couverts | Manque |
|---|---|---|
| Schibsted Grotesk | 119 / 124 | 300 (×3), 800 (×2) |
| Fraunces | 136 / 145 | 300 (×9) |
| DM Mono | 31 / 31 | — |

286 des 300 usages. Les 14 restants sont approchés par le navigateur depuis la
graisse voisine ; l'écart n'est pas perceptible à ces volumes.

## Trois endroits câblés
1. **Le site HTML** — `build_site.py` copie les 12 fichiers, écrit les 12
   `@font-face`, précharge les deux faces du premier écran, et le gabarit
   n'appelle plus Google.
2. **Les documents** — `build_documents.py` fait pareil.
3. **WordPress** — extension **Finition v1.2.2** :
   `add_filter('elementor/frontend/print_google_fonts', '__return_false')`,
   déqueue tout style du thème qui viserait `fonts.googleapis.com`, et sert les
   mêmes 12 fichiers depuis le dossier de l'extension. 100 % réversible :
   désactiver l'extension rend l'état d'avant.

Au passage, les 3 dernières occurrences du cyan retiré `#046C86` sont corrigées
dans l'extension elle-même.

## Un défaut trouvé par la mesure
Le contrôle au navigateur a relevé **2 requêtes sortantes** malgré tout :
`soha-accueil-plate-b4c136c1.webp` et `soha-hero-espaces-professionnels.webp`.
Ce sont des **images de fond** (`background_image`) — le générateur les écrivait
telles quelles au lieu de les rapatrier comme les `<img>`. Corrigé : les fonds
passent par le même résolveur. Images copiées 66 → **74**, soit la totalité du
kit médias.

**Vérification finale, mesurée au navigateur :**
- **0 requête vers l'extérieur** — pages et documents.
- 12 faces déclarées, 6 à 9 chargées par page (celles réellement utilisées).
- Corps rendu en Schibsted Grotesk, titres en Fraunces.
- Porte : 116 rendus (29 pages × 4 largeurs), 0 débordement, 0 image en échec
  sur 136, un seul H1 par page.

## Leçon
**« Zéro appel externe » se mesure, ne se déduit pas.** Le CSS ne contenait plus
une seule URL Google — et pourtant deux requêtes sortaient encore, par un chemin
que je n'avais pas couvert. Écouter le trafic réel du navigateur, pas seulement
relire le code.
