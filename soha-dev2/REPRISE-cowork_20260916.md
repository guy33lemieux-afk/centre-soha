# Centre Soha — dossier de reprise (à coller dans Cowork)
*État au 16 septembre 2026, 00 h UTC. Rédigé pour reprendre le travail sans relire la conversation.*

## 1. Le client, le projet, les règles qui ne bougent pas
- **Mala** tient le **Centre Soha**, 961 rue Rachel Est, Montréal (Plateau) : cours, soins, ateliers, salles et studio de balado à louer. Site WordPress/Elementor en développement sur `centresoha.com/dev` (racine WordPress : `/wpsoha/`). Toujours tutoyer Mala, en français, procédures détaillées, chiffres mesurés.
- **Deux pôles jamais mélangés.** L'autre pôle, **soha.live** (place de marché e-learning, trois écoles Soigner / Bâtir / Cultiver), **n'est jamais concerné**.
- **Règle apprise à la dure (15 sept.)** : les accents Soigner `#19A7DB`, Bâtir `#D29A4E`, Cultiver `#5E8C5A` sont **les couleurs des écoles de soha.live**. Le kit du Centre en employait 264. **Ils sont sortis du Centre, et n'y reviennent pas.** Les skills soha-design / soha-web disent encore « palette par école » : sur ce point la parole de Mala l'emporte.
- **Canon du Centre** : encre `#0E1A15` · ivoire `#F4F0E7` · papier `#FBF8F3` · sable `#F2ECE1` · filet `#E0D8CA` · gris `#3F4A45` / `#5A6460` · cramoisi `#AE1E3B` **réservé** au sceau. Rampe 12/14/16/19/24/32/48/72. Fraunces (titres) · Schibsted Grotesk (courant) · DM Mono (surtitres). Mouvement 140/280 ms, `cubic-bezier(.22,.61,.36,1)`, `prefers-reduced-motion`.
- **Verdict du conseil de la couleur (route A)** : le Centre **ne prend pas de teinte à lui**. Sa couleur = encre, ivoire, ses photographies. Mala autorise une teinte « s'il le faut » ; mesuré, il ne le faut pas — toute brique dérivée d'un mur échoue soit la lisibilité sur ivoire, soit la distance à Bâtir ou au cramoisi.
- **Interdits absolus** : inventer un nom d'artisan·e, un verbatim, une anecdote, une statistique, un visage ; réécrire un texte de Mala (on PROPOSE dans un fichier à part) ; un hex hors canon sans le déclarer comme proposition ; livrer sans avoir OUVERT les captures ; annoncer « vérifié » sur la foi d'une porte qu'on n'a pas vue échouer sur un état cassé.
- **Économie** : Mala surveille les tokens. Les workflows multi-agents ont épuisé la session **trois fois** en un jour sans produire ; la production s'est faite à la main, geste par geste. Ne pas relancer de flotte sans son accord explicite.

## 2. Où sont les choses
- **Dépôt** : `github.com/guy33lemieux-afk/centre-soha`, branche **`claude/dev2-duplicates-missing-plugins-nt2etp`**, dossier `soha-dev2/`. Tout est commité et poussé (dernier : `c3cdb39`). **Pas de PR sans demande.**
- **Trois couches** : KIT (Elementor, part dans WordPress) · GÉNÉRATEUR (`build_site.py` → site HTML de référence pour mesurer) · CONTENU (textes et photos de Mala — on ne touche pas).
- **Scripts du kit** (`kit_*.py --kit <dossier>`, idempotents, marqueur de version, docstring = constat / fait / refuse) : `kit_heros.py` v07 (héros en widget image, voile en cartel d'angle), `kit_cyan.py` (le cyan sort, fond par fond), `kit_fiches.py` (cartes → lignes), `kit_cibles.py` (44 px), `kit_entete.py` (en-tête téléphone 63 px), `kit_rythme.py` v02 (144/48/96), `kit_focus.py` v03, `kit_mouvement.py`, `kit_soigner.py`, `kit_meta.py`, `kit_favicon.py`, `kit_ariane.py`, `kit_accueil.py`, etc.
- **Portes** (à faire passer avant toute livraison) : `porte_du_contraste.py --site` (mesure TOUT texte, y compris sur photo ; cache les lettres par `color:transparent`) · `porte_du_regard.py --site` (30 pages, débordements 1440→390, liens, focus) · `porte_du_lcp.py` · `porte_de_la_nettete.py` · `porte_du_fichier_unique.py --fichier` (décode chaque image) · `porte_du_mouvement.py` · `porte_des_formulaires.py`.
- **Fabriquer** : `python3 build_site.py --kit <kit> --medias <medias> --polices <polices> --sortie <site>` puis `python3 build_site_unique.py --site <site> --sortie soha_site_AAAAMMJJ_vNN.html` (un seul fichier, 11,4 Mo, hors ligne, 29 pages, 86 fichiers embarqués).
- **Skill de jugement** : `soha-gout` — `scripts/slop.py <html>` (détecteur de tells d'IA, 0 trouvaille sur l'accueil) ; `scripts/regard.py <page> --out <dir> --plein` avec `PW_CHROMIUM=/opt/pw-browsers/chromium-1194/chrome-linux/chrome` ; grille sur 20 dans `references/grille-regard.md`. **L'auteur ne note pas sa propre sortie.**
- **Livrables envoyés à Mala** : `soha_site_20260915_v05.html` (le site), `NOTE-DE-LIVRAISON.md`, `verdict-couleur.md`, `proposition-legendes.md`, `proposition-voix.md` (les deux derniers sont dans le dépôt).

## 2 bis. Les photos et le kit média
- **Kit média** = ce qui doit être téléversé dans WordPress AVANT l'import du kit (`wp-content/uploads/2026/08/` et `/09/`). Source de travail : `scratchpad/medias15/2026/` — **74 fichiers, tous en WebP**, nommés `soha-<page>-<NNN>.webp` (convention `soha_<objet>_AAAAMMJJ_vNN` pour les livrables). Une liste `_medias.csv` dit lesquels téléverser avant import. Les zips de livraison sont dans le dépôt : `soha_kitdev_20260914_v18.zip` (kit), `soha_site-html_20260911_v16.zip` (site HTML), plus les trois extensions et les documents maison.
- **Ce qu'il y a, et à quelle taille** (mesuré) :
  - 7 héros `soha-hero-*.webp` : 1 500–1 800 px, 612 ko en tout ; le seul qui n'est pas le 961 : `soha-hero-journal.webp` (pissenlit, 1 500×400).
  - 16 studio `soha-studio-podcast-056…070.webp` : 1 000–1 100 px.
  - 13 journal `soha-journal-079…091.webp` : 300–2 400 px, 2,8 Mo — les originaux retrouvés par Mala (2020–2023) ; `086` reste à 300 px (introuvable dans 2020–2023, peut-être 2017–2019).
  - 17 portraits `soha-portrait-<prenom-nom>.webp` : 200–300 px — **trop petits pour plus qu'une ligne de 200 px**.
  - accueil 6 (900–1 400), espaces 5 (800–1 000), se-transformer 3 (640–800), prendre-soin 3 (300 !), contact 1 (900), événement 1 (800), logos 2 (300).
  - **Aucune photo du 961 lui-même ne dépasse 1 100 × 734 px.** C'est la limite dure de tout ce qui reste (aire, matière). Il faut les originaux — JPEG pleine taille ou RAW du shooting — ou une matinée de prises de vue.
- **Formats imposés par le générateur** (`build_site.py`) : chaque `<img>` porte `width`/`height` (anti-CLS) et `alt` dérivé du nom de fichier (`texte_alternatif()`) ; le héros et les vignettes du Journal portent un `srcset` aux **échelons 400 / 800 / 1 200 / 1 800 / 2 400 px** (`ECHELONS`), fabriqués à la volée en WebP q86, **jamais plus lourds que l'original** (sinon supprimés) ; `sizes` n'est écrit que là où la largeur d'affichage est connue (100vw pour le héros, colonnes déclarées pour la grille) ; le héros est préchargé avec `imagesrcset`. Le fichier unique retire les `srcset` et embarque le `src` seul en base64.
- **Retrouver un original** : `medias_originaux.py` apparie par empreinte perceptuelle (dHash 16×16, distance ≤ 24 sur 256 bits), refuse sous 400 px, plafonne à **2 400 px** de large (au-delà, le WebP dépasse 600 ko pour rien).
- **Le voile** n'existe plus comme réglage Elementor : c'est `.soha-hero-fond::after` (kit_heros.py v07), un dégradé d'encre masqué au bloc de texte. Pour changer une photo de héros : remplacer la clé `image` de la widget `soha-hero-fond` de la page, rien d'autre.
- **Favicon** : `kit_favicon.py` découpe l'anneau du O du logo (`soha_logo-site_20260828.webp`) en 32/180/192/512 + maskable ; à poser dans WordPress via Apparence → Personnaliser → Identité du site (voir `LISEZ-MOI.md` produit par le script). Le point cyan du logo est un fichier : il reste.

## 3. Ce qui est fait (mesuré, 15 septembre)
| | avant | après |
|---|---|---|
| Cyan de Soigner dans le kit | 264 | 0 (229 clés, 4 couleurs globales, 7 lignes du générateur) |
| Voile des héros | uniforme 0,68 | retiré de la photo ; dégradé masqué au bloc de texte, ferré à gauche (droite sur le studio) ; surface nue 20 → 42 % |
| Accueil téléphone, bande photo | 79 px | 405 px |
| En-tête téléphone | 166 px | 63 px |
| Cibles < 44 px | 40 | 1 |
| Thérapeutes et cours | 20 cartes, médaillons 132 px | 20 lignes portrait 200 · identité · propos |
| Intervalles entre sections | 120/168/144/216/96 | 96 / 144 / 192 |
| Menu | défilait | collé en haut |
| Journal téléphone | 941 ko | 422 ko |
| Contraste | — | 1 361 textes, aucun sous le seuil, pire cas 5,21 |
| Note du brief (grille /20) | 9 | à faire noter par un tiers |

## 4. Ce qui attend Mala (bloquant pour la suite)
1. **Les originaux du bâtiment** en pleine taille (brique, plancher, escalier, salles) — aucune photo du 961 lui-même ne dépasse 1100 × 734 px. Sans eux, la matière n'a pas d'aire.
2. **Le héros du Journal** est un pissenlit (seule ouverture qui n'est pas le 961) : remplacer par une photo du studio, ou garder ?
3. **Portraits** : sur « Prendre soin de soi », Dominique Mennessier, Farah Quiroga, Yuv Baboolall portent le portrait que « Se ressourcer » posait déjà sous leur nom. Confirmation écrite demandée.
4. **Six légendes** proposées dans `proposition-legendes.md`.
5. **Premier écran de l'accueil** : le soin (image la plus pâle) ou le mur de brique ?
Plus anciens : hiérarchie des 13 pages sans fil d'Ariane ; double signature des 13 articles ; accord de Yuv Baboolall pour la citation ; Mailchimp ; identifiants WP Mail SMTP ; DNS Cloudflare.

## 5. Prochaines étapes, dans l'ordre
1. Faire NOTER la v05 sur 20 par quelqu'un d'autre que l'auteur (grille `soha-gout`), captures ouvertes.
2. Accueil : diptyque asymétrique à la place des trois carrés (spécifié dans le journal du conseil, non produit).
3. Mesure des textes 45–75 ch partout, un seul rayon d'angle, trois familles.
4. Formulaires : `aria-live`, ids en double (pied de page), champs cachés de l'estimateur rendus visibles.
5. Légendes des planches (après réponse de Mala).
6. **Import du kit dans WordPress `/dev`** — la prochaine étape visible pour Mala ; le kit est prêt (SEO, favicon, `import-seo.php`).
