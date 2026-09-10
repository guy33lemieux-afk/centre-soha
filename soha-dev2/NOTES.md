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

---

# Complément 6 du 10 septembre — la politique de confidentialité bouclée

Faits fournis par Mala : **WP Mail SMTP** pour les formulaires, **Newsletter**
pour l'infolettre, **24 mois** de conservation.

## Deux politiques existaient — la bonne n'était pas celle qu'on croyait
`soha_confidentialite_20260903_v01.html` (fichier isolé) nomme **Cyberimpact**
comme plateforme d'envoi et laisse le responsable en `[Nom du·de la responsable]`.
La page **7386 du kit** — celle qui est réellement publiée — est bien meilleure :
elle nomme Dominique Mennessier, couvre les formulaires ET l'infolettre, et
signale honnêtement ses trois points en suspens.

→ Le fichier isolé du 3 septembre est **périmé**. C'est la page du kit qui vit.
   Et sa mention de Cyberimpact contredisait la réalité : à corriger si ce
   fichier resurgit.

## Une phrase que le travail d'aujourd'hui a rendue fausse
La politique disait : *« Une seule ressource est chargée depuis l'extérieur :
les polices Google Fonts, qui reçoivent de ce fait votre adresse IP. »*
Depuis l'auto-hébergement des polices, c'est faux. Réécrit en : **aucune
ressource n'est chargée depuis l'extérieur**, avec la date du changement.

*Un correctif technique peut périmer un texte juridique. Vérifier les deux.*

## Kit v10 — les quatre blocs réécrits
1. Préambule : les « trois précisions à fixer » sont fixées, l'encadré disparaît.
2. Polices : plus aucun appel externe.
3. Fournisseurs nommés : l'hébergeur ; **WP Mail SMTP** (achemine les
   formulaires) ; **l'extension Newsletter** (envoie l'infolettre, et tourne sur
   le serveur du site — la liste ne part pas chez un tiers).
4. Conservation : **24 mois** après le dernier échange pour les formulaires ;
   jusqu'à désinscription pour l'infolettre, avec la trace minimale du retrait.

Les deux encadrés « À compléter » sont retirés. Date portée au 10 septembre 2026.
Vérifié sur la page publiée : 0 « À compléter », 0 « Google Fonts ».

## La question qui reste, et elle est réelle
WP Mail SMTP n'envoie rien par lui-même : il **relaie** vers un service
configuré (Gmail, SendGrid, Mailgun, un SMTP d'hébergeur…). La Loi 25 demande
de nommer qui traite les renseignements **et de dire s'ils sortent du Québec**.
Il faut donc savoir : (a) quel service est configuré dans WP Mail SMTP, (b) où
sont les serveurs de l'hébergeur. Sans ces deux réponses, la section 4 nomme le
mécanisme mais pas la destination finale.

---

# Complément 7 du 10 septembre — les formulaires n'avaient pas de destinataire

Mala a collé le réglage « From Email » de WP Mail SMTP : `admin@centresoha.com`.
Ce n'est pas le service de relais (la question posée), mais ça a fait sortir
autre chose.

## Le défaut
Les **quatre formulaires du kit** — Contact, Studio podcast, Espaces
professionnels, et la nouvelle page /reservation/ — n'avaient **aucun
`email_to` défini**. Elementor Pro retombe alors sur l'adresse d'administration
de WordPress, soit très vraisemblablement `admin@centresoha.com`.

Or le site dit d'écrire à `info@centresoha.com` — **32 fois**.

Conséquence : chaque demande de location, chaque demande de studio, chaque
message de contact arrivait dans une boîte que le site ne mentionne jamais. Si
personne ne surveille `admin@`, la demande est perdue. Sur les pages qui portent
le revenu du Centre.

## Le correctif (kit v11)
Sur les quatre formulaires :
- `email_to` → **info@centresoha.com**
- `email_subject` → distinct par formulaire, pour trier d'un coup d'œil
- `email_from` → `admin@centresoha.com` (l'expéditeur de WP Mail SMTP, pour que
  l'authentification du domaine reste valide)
- `email_from_name` → « Site du Centre Soha »
- `email_reply_to` → `[field id="courriel"]` — **répondre au courriel écrit
  directement au visiteur**, sans copier-coller son adresse

## Ce qui reste
Le **service de relais** configuré dans WP Mail SMTP. « From Email » dit d'où
part le courriel, pas par qui il transite. Le nom est dans WP Mail SMTP →
Réglages → section « Programme de messagerie » (la rangée de logos). La Loi 25
demande de nommer qui traite les renseignements et de dire s'ils sortent du
Québec — il faut donc aussi savoir où sont les serveurs de l'hébergeur.

## Leçon
**Une réponse à côté de la question vaut mieux qu'un silence.** L'adresse
d'expéditeur n'était pas ce que je demandais, mais la regarder a révélé un
défaut plus grave que celui que je cherchais. Ne pas écarter ce qui arrive hors
cadre : le lire d'abord.

---

# Complément 8 du 10 septembre — le CRM

Mala : « c'est la partie à monter avec un bon CRM sur mesure, besoin d'aide pour
configurer tout ça ».

## Le défaut central du CRM v02, mesuré
Le fichier enregistre à travers **`window.storage`** — un objet **qui n'existe
pas dans un navigateur**. Chaque appel est enveloppé dans un `try` qui avale
l'erreur. Donc : rien n'échoue, rien n'avertit, **rien n'est écrit**.

Mesuré dans Chromium sur une vraie page :

    window.storage        undefined
    window.localStorage   object
    window.indexedDB      object
    le garde-fou du CRM   ne fait rien, sans erreur

On ajoute un contact, il s'affiche, on ferme l'onglet — il n'a jamais existé.
La pire panne : celle qui a l'air de marcher.

## Quatre défauts de plus, même réparé
1. Un navigateur, un appareil : ni téléphone, ni deuxième personne, ni sauvegarde.
2. Aucun lien avec le site : les 4 formulaires n'alimentent rien.
3. Vocabulaire discordant : CRM « Grande salle · Studio · Petite salle » contre
   estimateur/formulaire « Studio · Espace SÖHA · Salle 4 · Salles 1·2·3 ».
4. Import Cyberimpact, alors que l'infolettre passe par l'extension Newsletter.

## Recommandation : le CRM vit dans WordPress
Les formulaires y arrivent déjà, UpdraftPlus sauvegarde déjà, l'accès
multi-appareil et multi-personne existe déjà, zéro abonnement, rien ne sort du
Québec de plus qu'aujourd'hui. Le modèle de données du v02 est bon et se reprend
tel quel. Trois types de contenu : `contact`, `reservation`, `atelier`.

Montage en 3 temps, chacun utile seul :
1. **Ne plus rien perdre** — archiver chaque envoi en base avant l'envoi du
   courriel, purge à 24 mois.
2. **Contacts et réservations** — les 3 CPT, import du JSON exporté par le v02.
3. **Tableau de bord et infolettre** — jonction avec l'extension Newsletter.

## Livré aujourd'hui : le pont estimateur → formulaire
L'estimateur passait déjà `?espace=&jour=&plage=&tarif=` à `/reservation/`, mais
rien ne les recueillait : la personne refaisait son choix à la main et le montant
qu'elle avait vu n'arrivait jamais au Centre.

- **Kit v12** : 4 champs cachés sur le formulaire (`estim_espace`, `estim_jour`,
  `estim_plage`, `estim_tarif`).
- **Finition v1.2.3** : recopie les paramètres d'URL dedans, en clair.

Testé au navigateur : `?espace=soha&jour=fds&plage=demi&tarif=400` donne
« Espace SÖHA · Fin de semaine · Demi-journée · 400 $ +tx ». `php -l` et
`node --check` passent.

## Décisions attendues
1. D'accord pour que le CRM vive dans WordPress ? (commande tout le reste)
2. Qui doit y accéder — Mala seule, Dominique aussi, la réception ?
3. Le service de relais WP Mail SMTP (bloque encore la section 4 de la politique).

## Leçon
**Un `try/catch` vide transforme une panne en illusion.** Le CRM avait l'air de
fonctionner parce que l'échec d'écriture était avalé. Avant de croire qu'un
stockage marche, l'ouvrir, écrire, recharger, relire.

---

# Cycle 9 · L'extension CRM v1.0.0 — l'interface de Mala, branchée sur WordPress

Décision prise : *« garde mon interface React et branche-la sur WordPress »*. Les
897 lignes du v02 ne sont donc pas réécrites. Ce qui change, c'est le sol : au
lieu d'appeler un `window.storage` qui n'existe pas, elles appellent un
`window.storage` que l'extension fournit, adossé à `wp_options`.

## Ce qui est livré
`soha_extensioncrm_20260910_v100.zip` — 23 fichiers, 284 Ko.

    soha-crm.php                      l'écran d'administration, deux routes REST
    uninstall.php                     l'effacement, à la suppression seulement
    assets/adaptateur.js              `window.storage` → la base
    assets/crm.js                     l'interface compilée, 64 Ko
    assets/polices.css + polices/     les 3 familles du canon, 12 fontes
    source/crm-interface-origine.jsx  le JSX d'origine, intact
    lisez-moi.md                      l'installation et les 5 choses à savoir

Dans le dépôt : `build_crm.py` (la fabrique), `crm-modele/` (tout ce qui est
écrit à la main), `crm-banc/` (le banc d'essai).

## Les quatre soins de l'adaptateur
1. **Plus rien ne se perd en silence.** Le CRM n'attend jamais `set()` : un échec
   resterait invisible. L'adaptateur affiche une bande rouge et ne se tait pas.
2. **Écritures groupées sur 800 ms**, vidées quand l'onglet passe en arrière-plan
   et par `sendBeacon` à la fermeture. Mesuré : créer un contact = 1 écriture.
3. **Garde de révision.** Deux personnes à la fois : celle qui enregistre sur un
   état périmé reçoit un 409 et une bande ambre, au lieu d'écraser l'autre.
4. **Rien ne sort.** Polices servies par l'extension, aucun CDN. Mesuré à zéro
   requête extérieure.

## Trois défauts trouvés, dont un grave
1. **Grave — toute la mise en page pour petits écrans était morte.** Le
   cloisonnement du CSS préfixait l'en-tête `@media (max-width:860px)` comme un
   sélecteur : `#soha-crm-racine @media (…)`. Un navigateur jette une règle comme
   celle-là *sans rien dire*. Le test `@` se faisait à la position exacte du
   curseur, où il n'y a qu'un saut de ligne et deux espaces. Corrigé, et
   `build_crm.py` refuse désormais de fabriquer une extension où cela
   réapparaîtrait. 136 sélecteurs cloisonnés avant, 148 après : les 12 manquants
   étaient tous ceux de la `@media`.
2. **L'interface annonçait « Données gardées dans ton navigateur. »** C'était
   vrai du prototype, et c'était le défaut lui-même. Corrigé à la fabrication :
   « Données gardées dans la base du site, sauvegardées avec elle. » Le JSX
   d'origine reste intact dans `source/`.
3. **Le PHP et l'adaptateur ne vivaient que dans le dossier de sortie**, et une
   reconstruction les avait effacés. Tout ce qui est écrit à la main est
   maintenant dans `crm-modele/`, recopié par la fabrique en dernier.

## Mesuré au navigateur (13 points, banc d'essai sur vrai HTTP)
Montage 63 nœuds · GET au chargement · écriture du semis · un contact créé par
l'interface retrouvé en base · survit au rechargement · bande de conflit sur 409 ·
bande de panne quand le serveur tombe · 0 requête extérieure · 0 erreur console ·
`.card`, `.badge`, `.btn`, `.soha h2` restent nus hors de la racine · aucun
débordement horizontal de 1440 px à 390 px, gouttière wp-admin comprise (ce qui
dépasse est *dans* la barre latérale, qui défile de son propre aveu).

## Choix assumés
- **Pas de purge automatique.** Les 24 mois portent sur les demandes reçues par
  formulaire, pas sur le registre des personnes du centre. Supprimer d'office la
  fiche de quelqu'un qui vient depuis trois ans serait une faute, pas une
  conformité.
- **Pas de table dédiée.** Une option suffit à quelques centaines de fiches ;
  `autoload` à `false` et plafond de 5 Mo. La table viendra avec la phase 2,
  quand il faudra chercher et recouper côté serveur.
- **`edit_pages` comme droit d'accès**, filtrable par `soha_crm_capacite`.

## Avant d'y mettre de vraies personnes — les 3 préconditions tiennent
1. 2FA posée, et les **deux gestionnaires de fichiers retirés** (`fileorganizer`,
   `wp-file-manager`).
2. UpdraftPlus vérifié, avec une destination **hors serveur**.
3. Les 5 fiches d'exemple du prototype supprimées.

## Décisions toujours attendues
1. Qui accède au CRM — Mala seule, Dominique aussi, la réception ?
2. Le service de relais de WP Mail SMTP (bloque la section 4 de la politique).
3. Où sont les serveurs de l'hébergeur (même section).

## Leçon
**Une règle CSS invalide ne lève aucune erreur.** `php -l`, `node --check` et
esbuild ont tous dit oui à un fichier dont un tiers de la mise en page était
inerte. Le compteur de sélecteurs aussi disait 136 sans broncher. Seul l'œil
posé sur l'écran à 390 px l'a vu. Ce qui se mesure, on le mesure ; ce qui ne se
mesure pas encore, on écrit le garde-fou avant de passer à la suite.

---

# Cycle 10 · CRM v1.1.0 — quatre personnes, et plus rien qui se perd

Réponse de Mala : **Mala, Dominique, Cassandra et Fred**. Quatre accès.

## Correction d'une erreur du cycle 9
J'avais écrit, dans le lisez-moi et dans le document, que les cinq fiches
présentes au premier chargement étaient « les seules données fictives » et
qu'il fallait les supprimer. **C'est faux.** Le `seed()` du v02 contient
Dominique Mennessier, Ève Morin, Jeimy Oviedo, Julie Habart et Marjolaine
Blouin, avec leurs matricules A·002 à A·011 : ce sont de vraies artisanes du
961, et Dominique est la co-associée que Mala vient de nommer pour l'accès.
Suivre mon instruction aurait détruit de vraies données. Corrigé partout.

## Ce que le cycle ajoute
**Les accès.** Une permission à part, `soha_acceder_crm`, plutôt que
`edit_pages`. Le CRM tient des coordonnées de personnes réelles : y entrer ne
doit pas être l'effet de bord du droit de corriger une page. Les administrateurs
l'ont par leur rôle ; les autres la reçoivent nominativement, sur un écran
« Accès » réservé à `promote_users`.

**Le conflit a un visage.** Ils sont quatre : « quelqu'un d'autre a enregistré »
ne suffit plus, il faut savoir à qui aller parler. Le serveur retient qui a écrit
en dernier et le renvoie avec le 409 ; la bande ambre le nomme.

**Phase 1 — ne plus rien perdre.** Chaque envoi de formulaire est écrit en base
*avant* que le courriel parte, sur `elementor_pro/forms/new_record` en priorité 5.
Le courriel devient l'avis, la base devient la mémoire. Un écran « Demandes »
avec pastille de compte, filtre en attente / toutes, détail dépliable, export CSV.
Purge automatique à 24 mois, une fois par jour, avec la date du dernier passage
affichée. Ni adresse IP, ni empreinte de navigateur : on garde ce que la personne
a écrit, rien de ce qu'elle n'a pas choisi de dire.

**Le pont entre les deux.** « Verser au répertoire » transforme une demande en
fiche contact — type `prospect`, statut `Nouveau`, consentement infolettre daté
si la case était cochée, et la demande inscrite dans l'historique. Si le courriel
est déjà connu, **pas de deuxième fiche** : l'échange s'ajoute à celle qui
existe. C'est exactement le doublon qui a coûté cher sur les médias de ce site ;
on ne le refait pas ici.

## Un vrai WordPress au banc
WordPress 6.8.3 complet sur SQLite (`crm-banc/wordpress/`), monté depuis GitHub
— wordpress.org est bloqué par le mandataire. Trois suites, chacune sur une base
fraîche, **87 vérifications, 0 échec** :

- `essai.php` (52) : activation, permission donnée et retirée, registre,
  autoload à `off`, routes 200/400/409/413/401, capture d'un envoi Elementor,
  versement, absence de doublon (casse du courriel comprise), demande sans
  courriel, purge à 24 mois qui épargne 23, désactivation qui ne perd rien.
- `ecrans.php` (20) : les trois écrans rendus avec `WP_DEBUG` allumé — toute
  notice sortirait dans la page ; échappement d'un nom contenant `<b>` ; rien
  ne se charge sur les autres écrans de l'administration.
- `navigateur.py` (15) : Chromium se connecte comme Mala, ouvre le CRM, crée
  un contact, et on relit la base en PHP pour vérifier qu'il y est. Puis on
  recharge.

Plus l'ancien banc sans WordPress (12 + 6) : groupement des écritures, bande de
conflit **nommée**, bande de panne, étanchéité du CSS, débordement horizontal.

## Une observation à passer à Mala
L'administration de WordPress appelle `secure.gravatar.com` pour les avatars —
six requêtes par page. Ce n'est pas l'extension, et ça ne concerne que les
comptes du personnel, pas les visiteurs. Réglages → Discussion permet de les
couper si le centre le souhaite.

## Trois pièges rencontrés, tous instructifs
1. `wp_set_current_user` sort immédiatement si l'identifiant ne change pas :
   l'objet en mémoire garde les anciennes capacités. D'où le fait qu'une
   permission accordée ne soit visible qu'au chargement suivant.
2. Activer et vérifier dans la même exécution donne un faux résultat : `init`
   est déjà passé, donc le type de contenu n'est jamais enregistré et on croit
   qu'il manque. L'activation a maintenant son propre processus, comme dans la
   vraie vie.
3. WordPress 6.8 a remplacé `autoload = yes/no` par `on/off/auto-…`. L'essai
   teste le sens, pas le mot.

## Décisions toujours attendues
1. Le service de relais de WP Mail SMTP (bloque la section 4 de la politique).
2. Où sont les serveurs de l'hébergeur (même section).

## Leçon
**Une donnée d'exemple n'est une donnée d'exemple que si on l'a lue.** J'avais
appelé « fictives » cinq fiches qui portaient des noms et des matricules réels,
et demandé leur suppression. Le code était sous mes yeux : `seed()` tenait la
liste. Avant de dire à quelqu'un d'effacer quelque chose, ouvrir la chose.

---

# Cycle 11 · CRM v1.2.0 — phase 2 : la demande devient une réservation

## Le défaut le plus coûteux du CRM n'était pas technique
Le CRM disait « Grande salle · Studio · Petite salle ». Le site, l'estimateur et
le formulaire de réservation disent **Studio · Espace SÖHA · Salle 4 ·
Salles 1·2·3**. Deux vocabulaires pour un même lieu : une réservation mal
saisie par mois, et un revenu qu'on ne sait plus attribuer à un espace. Corrigé
à la fabrication, comme la phrase de stockage — le JSX d'origine reste intact
dans `source/`.

`build_crm.py` tient maintenant une table `RETOUCHES` : chaque retouche porte sa
raison en clair, et **doit** trouver sa cible exactement une fois, sinon la
fabrication s'arrête. Trois aujourd'hui : la phrase de stockage, les espaces,
et l'ajout de « Récurrent » aux récurrences.

## Le pont estimateur → formulaire → CRM est complet
Il manquait le dernier maillon. L'estimateur affichait un prix, le formulaire le
transportait dans ses quatre champs cachés, la phase 1 l'archivait — et Mala
ressaisissait tout à la main. Maintenant, « Verser au répertoire » crée aussi la
réservation :

| ce que la personne a choisi | où ça va |
|---|---|
| `espace` (ou `estim_espace`) | l'espace, sans sa superficie |
| `date` | la date, si elle est en AAAA-MM-JJ |
| `estim_tarif` « 400 $ +tx » | le prix, 400 |
| `frequence` | Ponctuel, ou Récurrent |
| `journee`, `plage`, `usage`, `vousetes`, `details` | la note, en clair |

**Rien n'est deviné.** Une date que le formulaire n'a pas su donner reste vide et
part dans la note. Les heures de début et de fin restent vides : elles se
conviennent au téléphone. Le paiement arrive toujours en `devis`. Et
« Récurrent (résident·e) » devient « Récurrent », pas « Hebdomadaire » — choisir
un rythme à la place de Mala, ce serait inventer.

Contact et réservation sont écrits **en une seule écriture** : soit les deux
arrivent, soit ni l'un ni l'autre. Une fiche sans sa réservation serait pire que
rien — on la croirait traitée.

## La sauvegarde du registre
Le registre tient dans une option. C'est ce qui le rend simple, et c'est un seul
endroit où tout perdre. Nouvel écran : télécharger un JSON daté avec son en-tête,
en remettre un (administratrice seulement, case à cocher obligatoire), et
**revenir en arrière une fois** — l'état d'avant est conservé et les deux
s'échangent. Un fichier qui n'a pas la forme d'un registre est refusé avant
d'avoir touché quoi que ce soit.

## Mesuré : 128 vérifications, 0 échec
Trois suites sur WordPress 6.8.3 (76 + 30 + 22), chacune sur base fraîche. Les
plus parlantes, au navigateur : une demande de location arrive du site, Mala
clique une fois, et la réservation apparaît dans l'onglet Location du CRM au bon
espace, à la bonne date, au bon prix, en devis. Puis la sauvegarde se télécharge
et le fichier est relu pour vérifier qu'il contient bien fiches et réservations.
Plus l'ancien banc sans WordPress (12 + 6).

Deux erreurs d'essai instructives, corrigées :
1. J'appelais `soha_crm_reservation_depuis()` sur le tableau brut d'un
   formulaire. L'extension normalise les champs à l'archivage : l'essai testait
   une forme qui n'existe nulle part. Tous les essais passent désormais par le
   vrai chemin — envoi, puis versement.
2. Une demande versée est marquée traitée, donc elle **quitte** la liste
   d'attente. Mon essai la cherchait dans la vue par défaut. C'est devenu une
   vérification à part entière plutôt qu'un essai corrigé en douce.

## Décisions attendues
1. Le service de relais de WP Mail SMTP — Mala ne sait pas lequel est
   sélectionné. Le chemin le plus sûr n'est pas la rangée de logos :
   `Outils → Santé du site → Infos → WP Mail SMTP` l'écrit en toutes lettres.
2. Où sont les serveurs de l'hébergeur.

## Leçon
**Un essai qui n'emprunte pas le vrai chemin ne mesure que lui-même.** Passer
directement le tableau brut à la fonction interne donnait un joli faux vert au
premier abord, puis un faux rouge — dans les deux cas, il ne disait rien du
comportement réel. Entrer par la porte, toujours : le formulaire, puis le clic.
