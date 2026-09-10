# Centre Soha — cycle du 10 septembre 2026

## Ce qui a été livré
- `soha_kitdev_20260910_v05.zip` — kit Elementor corrigé (base : kit v04 du 7 sept).
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
| Boutons sans page cible, repointés vers `#evenements` | 5 |
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
