# Les deux bancs d'essai du CRM

## `wordpress/` — l'extension dans un vrai WordPress

Un WordPress 6.8.3 complet sur SQLite : aucune base de données à installer,
aucun serveur à configurer. Rien n'y ressemble à l'hébergement du Centre Soha —
c'est voulu. Si l'extension passe ici **et** là, elle ne dépend d'aucune
particularité de l'un ni de l'autre.

    sh wordpress/preparer.sh                       # monte le WordPress jetable
    cp -r <sortie>/soha-crm wordpress/wordpress/wp-content/plugins/
    sh wordpress/banc.sh

Trois suites, chacune sur une base fraîche — un essai qui hérite de la veille ne
prouve rien :

- `essai.php` — l'activation, la permission donnée et retirée, le registre, les
  deux routes REST (200, 400, 409, 413, 401), la capture d'un envoi de
  formulaire Elementor, le versement au répertoire, l'absence de doublon sur un
  même courriel, la purge des 24 mois, et le fait que la désactivation ne perde
  rien.
- `ecrans.php` — les trois écrans rendus pour de vrai, avec `WP_DEBUG` allumé :
  toute notice de PHP sortirait dans la page et ferait tomber l'essai. On y
  vérifie aussi l'échappement (un nom contenant `<b>` doit ressortir échappé) et
  que rien ne se charge sur les autres écrans de l'administration.
- `navigateur.py` — Chromium se connecte à `wp-login.php` comme Mala, ouvre le
  CRM, crée un contact, et on va relire la base en PHP pour vérifier qu'il y est.
  Puis on recharge : c'est la seule mesure qui prouve quelque chose.

`activer.php` existe pour une raison : activer et vérifier dans la même
exécution donne un faux résultat, parce que le crochet `init` est déjà passé et
que le type de contenu ne serait jamais enregistré.

## `serveur.py` + `crm.html` + `regard.py` + `cloison.py` — l'interface seule

Plus léger, sans WordPress : un serveur qui imite les deux routes REST, et une
page hôte portant les classes `wp-admin wp-core-ui` du body de WordPress —
c'est là que se verrait une collision de CSS. Sert à mesurer ce que le banc
WordPress ne mesure pas : le groupement des écritures, la bande de conflit, la
bande de panne réseau, l'étanchéité du CSS et le débordement horizontal.

    npm install react@18.3.1 react-dom@18.3.1
    mkdir -p banc/vendor && cp serveur.py crm.html regard.py cloison.py banc/
    cp node_modules/react/umd/react.development.js \
       node_modules/react-dom/umd/react-dom.development.js banc/vendor/
    cp -r <sortie>/soha-crm/assets banc/assets
    cd banc && python3 regard.py . && python3 cloison.py .

Chromium est appelé par son chemin explicite dans les scripts : à ajuster selon
la machine.

## Ce que ces bancs ont trouvé

**Que toute la mise en page pour petits écrans était morte.** Le cloisonnement
du CSS préfixait `@media (max-width:860px)` comme s'il s'agissait d'un
sélecteur — `#soha-crm-racine @media (…)`. Un navigateur jette une règle comme
celle-là sans rien dire. `build_crm.py` refuse maintenant de fabriquer une
extension où cela se reproduirait.

**Qu'une permission accordée n'est visible qu'au chargement suivant.**
`wp_set_current_user` sort immédiatement si l'identifiant ne change pas : l'objet
en mémoire reste celui d'avant. Ce n'est pas un défaut de l'extension, mais il
faut le savoir avant de croire qu'un accès n'a pas été donné.
