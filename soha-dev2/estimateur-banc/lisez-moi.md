# Le banc de l'estimateur

    sh ../crm-banc/wordpress/preparer.sh        # le même WordPress jetable
    cp -r ../estimateur-modele wordpress/wp-content/plugins/soha-estimateur
    sh banc.sh

**36 vérifications** — 22 sur le rendu, 14 au navigateur.

Le banc ouvre la page **deux fois** : une fois avec JavaScript, une fois sans.
Les deux comptent autant l'une que l'autre. Sans JavaScript, on éprouve ce que
voit quelqu'un dont le script n'a pas tourné — Rocket Loader, une erreur
ailleurs sur la page, une connexion coupée au mauvais moment. Le bouton doit
alors mener quelque part de juste, même figé sur la sélection de départ.

Il fait aussi le tour complet de la grille : **les 24 combinaisons** d'espace,
de type de journée et de plage sont cliquées, et le prix affiché est comparé à
celui que le PHP déclare. Une grille et un affichage qui divergent, c'est un
tarif annoncé qu'on ne pourra pas tenir.

## Ce que ce banc a trouvé

**Le bouton ne menait nulle part avant que le JavaScript ne tourne.** Il partait
avec `href="#"` et n'obtenait sa vraie destination qu'une fois le script
exécuté. Sur un site servi derrière Rocket Loader, la personne pouvait cliquer
« Demander cette réservation » et rester exactement où elle était. Aucune
erreur, aucune trace : juste une demande de location perdue.

Trois autres, du même passage : le prix de départ était écrit en dur (450 $) au
lieu d'être tiré de la grille, les boutons ne disaient pas aux lecteurs d'écran
lequel était choisi, et le script n'était pas à l'abri de Rocket Loader.
