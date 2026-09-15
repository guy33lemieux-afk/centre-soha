# Les photos du Journal — ce qu'il faut, fichier par fichier

> **MISE À JOUR du 15 septembre, après la page blogue envoyée par Mala.**
>
> Le diagnostic change. Les originaux **existent**, sur le WordPress de
> centresoha.com, et ils sont **plus grands que ce que le kit médias
> transporte**. La page blogue sauvegardée porte des `srcset` qui les
> annoncent :
>
> | article | dans le kit | sur WordPress |
> |---|---|---|
> | De l'assise cambrée à la vibration de la voix | 800 px | **1920 px** |
> | Le Yoga Nidra | 800 px | **1080 px** |
>
> Même proportion, même photo : le kit médias a été exporté **redimensionné à
> 800 px**. Ce n'est donc pas un problème de photos manquantes, c'est un
> problème d'export.
>
> **Ce qu'il faut faire, et c'est plus simple que de chercher des originaux :**
> ré-exporter le kit médias sans la réduction — ou, plus direct, récupérer les
> treize fichiers dans `wp-content/uploads/` de centresoha.com. Les noms y sont
> les noms d'origine (`caroline-veronez-…unsplash.jpg`), pas les
> `soha-journal-0XX.webp` du kit : c'est l'export qui les a renommés.
>
> Je ne peux pas aller les chercher moi-même — le réseau vers centresoha.com
> est fermé depuis cet environnement (test : aucune connexion).
>
> Le tableau ci-dessous reste valable comme liste de ce qu'il faut ; la colonne
> « il faut » est un plancher, pas un plafond. Si l'original fait 1920, prends
> 1920.


Mesuré le 15 septembre 2026 sur le kit médias v04 (celui que tu viens de
renvoyer — il est identique au bit près à celui avec lequel je travaille).

**Le fait.** Sur sa page d'article, chaque photo est affichée exactement à sa
largeur native. Sur un écran à haute densité — tous les téléphones, la plupart
des portables — il en faut le double. Les treize sont donc molles, à des degrés
divers. Trois sont petites même à densité 1.

**Ce qu'il faut :** l'original, ou un export à au moins la largeur demandée
ci-dessous, sur le côté long. Format indifférent (JPEG de qualité, PNG, TIFF) —
je m'occupe de la conversion et du recadrage.

| fichier actuel | taille | il faut | article |
|---|---|---|---|
| `soha-journal-079.webp` | 800 × 532 | **1600 px** | De l’assise cambrée à la vibration de la voix |
| `soha-journal-080.webp` | 800 × 800 | **1600 px** | Le Yoga Nidra |
| `soha-journal-081.webp` | 800 × 533 | **1600 px** | Le chant comme antidote contre le stress ? |
| `soha-journal-082.webp` | 800 × 532 | **1600 px** | Soins du visage et acupuncture : Le lifting acupunctural |
| `soha-journal-083.webp` | 800 × 533 | **1600 px** | Remède du mois : allons jouer dehors! |
| `soha-journal-084.webp` | 800 × 532 | **1600 px** | Apiculture Urbaine |
| `soha-journal-085.webp` | 500 × 625 | **1000 px** | Le cri; et si j&#x27;osais |
| `soha-journal-086.webp` | 300 × 300 | **600 px** | La boîte de Pandore et le corps oublié |
| `soha-journal-087.webp` | 800 × 532 | **1600 px** | L’art de perdre |
| `soha-journal-088.webp` | 800 × 533 | **1600 px** | Gâteau pour oiseaux |
| `soha-journal-089.webp` | 800 × 600 | **1600 px** | Biscuits au tahini |
| `soha-journal-090.webp` | 720 × 540 | **1600 px** | Soupe aux pois |
| `soha-journal-091.webp` | 500 × 324 | **1000 px** | Le Kampo |

## Les trois urgentes

Elles sont petites même sans tenir compte de la densité :

- `soha-journal-086.webp` — **300 × 300**
- `soha-journal-091.webp` — **500 × 324**
- `soha-journal-085.webp` — **500 × 625**

## Et une chose que la résolution ne réglera pas

Les treize photos ont **sept proportions différentes** : 1:1, 3:2, 4:3,
1,54:1, 0,8:1 (portrait)… La grille du Journal les recadre déjà en carré,
donc elle tient. Mais sur les pages d'article, chaque photo impose sa forme,
et c'est ça qui se voit comme un manque d'harmonie.

Deux façons de s'en sortir, et c'est une décision, pas un correctif :

1. **Recadrer tout le Journal sur une seule proportion** (3:2 est la plus
   représentée : sept photos sur treize). Je peux le faire depuis les
   originaux sans rien redessiner.
2. **Assumer les formes** et donner à chaque photo la même LARGEUR plutôt que
   la même hauteur — la page respire différemment, mais elle est cohérente.

Sans les originaux, ni l'une ni l'autre n'est possible : recadrer un 300 px
ne fait pas apparaître des pixels.