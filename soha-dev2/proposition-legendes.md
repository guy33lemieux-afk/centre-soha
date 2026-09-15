# Propositions de légendes et de textes alternatifs — Centre Soha

Fichier à part, pour Mala. **Rien de ce qui suit n'est appliqué.** Chaque ligne montre la
version actuelle en regard. Tu valides, tu corriges, ou tu laisses vide : une image sans
légende reste un `<img>` nu, au pixel près.

Règle d'écriture tenue ici : une légende ne dit que ce que la photo **montre** ou ce que la
page **dit déjà**. Aucune heure (« un matin »), aucun prénom, aucun nombre, aucun nom de
salle qui n'est pas écrit sur la page. Une triade au plus par page. Le séparateur des
cartels est le point médian « · » déjà employé sur le site (« 45,52° N · 73,57° O »,
« Salles 1 · 2 · 3 »), pas le cadratin.

## A. Les six légendes (widgets image, champ Elementor `caption`)

| # | Page · widget | Photo (fichier) | Ce qu'on voit | Actuel | Proposé |
|---|---|---|---|---|---|
| 1 | Accueil · cartel 6d51147a sur 78dd0b | soha-accueil-plate | une personne allongée sous un drap, une autre debout, mains au-dessus ; mur blanc, macramé | « Planche 01 — Un soin, un matin au 961 » (écrit par l'agence, pas par toi) | « Planche 01 · Un soin, sur rendez-vous. » |
| 2 | Accueil · image 1cd86c62 | soha-accueil-001 | des personnes allongées sur des tapis, une debout | (aucune) | « Un cours, en salle. » |
| 3 | Accueil · image 2a8cb9b1 | soha-accueil-003 | une personne debout, mains au-dessus d'une autre allongée ; mur de brique | (aucune) | « Un soin, devant la brique. » |
| 4 | Espaces · texte 481bc087 sous la planche | soha-espaces-professionnels-plate | une salle vide, tapis au sol, mur de brique | « La grande salle du 961, telle qu'elle est un matin de semaine. » | « Une salle du 961, vide, telle qu'elle est. » — ou, si tu confirmes que c'est bien l'Espace Soha : « L'Espace Soha, vide, tel qu'il est. » |
| 5 | Studio podcast · héros f… (soha-hero-studio-podcast) | soha-hero-studio-podcast | le studio : table, fauteuils, éclairages, mur de brique | (aucune, alt « Le Centre Soha — studio podcast ») | « Le studio. Tout est prêt. » (reprend ton « Tu arrives, tout est prêt ») |
| 6 | Se ressourcer · héros | soha-hero-se-ressourcer | une personne debout, une dizaine allongées sur des tapis, plancher de bois | (aucune) | « Un cours, en salle, au 961. » |

Question ouverte, pas une légende : la photo du héros « Prendre soin de soi »
(soha-hero-prendre-soin) montre un groupe sur des tapis, une personne qui recouvre quelqu'un
d'une couverture — pas un soin en cabinet, alors que la page dit « au 957, à l'étage, sur
rendez-vous ». Une légende ne peut pas réparer ça. Veux-tu une autre photo, ou garder celle-ci ?
Même question pour le cartel 1 : le texte de l'accueil dit « Le 957 […] pour les soins, à
l'étage » ; l'ancien cartel disait « un soin au 961 ». Le proposé ne nomme plus le numéro.

## B. Les textes alternatifs (attribut `alt`, lu par les lecteurs d'écran et par Google)

Aujourd'hui le kit porte **0 alt sur 62 images** : mon générateur les fabrique depuis le nom
de fichier, et chez toi Elementor prendra le champ vide de la médiathèque. Résultat mesuré :
« Le Centre Soha — studio podcast » ×16 sur une seule page, et un alt qui invente une
personne — « Portrait de Dominique Animatrices Invitees » (nom de fichier découpé). Un alt
décrit ce qui est visible, sans heure, sans prénom que la page ne nomme pas.

| Fichier | Alt actuel (généré) | Alt proposé |
|---|---|---|
| soha-accueil-plate | Le Centre Soha — accueil | Un soin sur table : une personne allongée sous un drap, une autre debout, les mains au-dessus |
| soha-accueil-001 | Le Centre Soha — accueil | Un cours au sol : des personnes allongées sur des tapis, une personne debout qui guide |
| soha-accueil-003 | Le Centre Soha — accueil | Un soin devant un mur de brique : une personne allongée, une autre debout, mains ouvertes |
| soha-accueil-005 | Le Centre Soha — accueil | Une formation : des personnes assises, de dos, face à une personne debout et un écran |
| soha-accueil-007 | Le Centre Soha — accueil | Le studio : deux fauteuils, une table, des éclairages, un mur de brique |
| soha-accueil-009 | Le Centre Soha — accueil | Une grande salle vide, plancher de bois, murs blancs |
| soha-hero-se-ressourcer | Le Centre Soha — se ressourcer | Un cours : une dizaine de personnes allongées sur des tapis bleus, une personne debout en robe blanche |
| soha-hero-prendre-soin | Le Centre Soha — prendre soin | Sur des tapis, une personne recouvre une autre d'une couverture ; bols et coussins au sol |
| soha-hero-espaces-professionnels | Le Centre Soha — espaces professionnels | Une grande salle vide : plancher de bois clair, mur de bois avec écran, plafonniers |
| soha-hero-studio-podcast | Le Centre Soha — studio podcast | Le studio : table ronde, fauteuils, deux éclairages sur pied, caméra, mur de brique |
| soha-portrait-dominique-animatrices-invitees | Portrait de Dominique Animatrices Invitees, au Centre Soha | Un cercle de personnes allongées au sol, têtes au centre, qui rient |
| soha-prendre-soin-028 (sous « Dominique Mennessier ») | Le Centre Soha — prendre soin | Ce fichier n'est pas un portrait : c'est une salle. Le portrait soha-portrait-dominique-mennessier existe — confirmes-tu que c'est bien elle ? Sans ton oui, aucun visage sous un nom. |
| portraits soha-portrait-*.webp (17) | Portrait de <nom de fichier> | « Portrait de <nom exact du h3 voisin> » — et seulement si tu confirmes fichier par fichier |
| logo (×2 par page) | Centre Soha | Centre Soha (inchangé) |

## C. Ce que ce fichier ne fait pas

- Il n'écrit aucun verbatim, aucune anecdote, aucun détail que la photo ne montre pas.
- Il ne touche à aucun de tes textes : les descriptions des cours et des thérapeutes restent
  mot pour mot.
- Tant qu'une ligne n'est pas validée, le champ reste vide.
