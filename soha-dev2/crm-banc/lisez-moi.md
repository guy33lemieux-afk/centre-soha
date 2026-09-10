# Le banc d'essai du CRM

Trois pièces pour voir, avant de livrer, ce que l'extension fait vraiment :

- `serveur.py` — imite les deux routes REST de l'extension, sur un vrai HTTP :
  jeton exigé, garde de révision, plafond de taille. `fetch` part pour de bon.
  Deux routes de banc en `PUT` : `/banc/journal` (ce qui s'est passé) et
  `/banc/avancer` (faire vieillir la révision pour provoquer un conflit).
- `crm.html` — la page hôte. Elle porte les classes `wp-admin wp-core-ui` du
  body de WordPress, parce que c'est là que se verrait une collision de CSS, et
  fabrique `window.wp.element` à partir de React et ReactDOM.
- `regard.py` — onze mesures : le montage, la lecture au chargement, l'écriture
  d'un vrai contact, sa survie à un rechargement, la bande de conflit, la bande
  de panne réseau, et l'absence de requête extérieure.
- `cloison.py` — deux autres : l'étanchéité du CSS (on pose `.card`, `.badge`,
  `.btn` *hors* de la racine et on vérifie qu'ils restent nus) et le débordement
  horizontal, gouttière du menu de WordPress comprise.

## Pour le lancer

    cd <un dossier de travail>
    npm install react@18.3.1 react-dom@18.3.1
    mkdir -p banc/vendor && cp serveur.py crm.html regard.py cloison.py banc/
    cp node_modules/react/umd/react.development.js \
       node_modules/react-dom/umd/react-dom.development.js banc/vendor/
    cp -r <sortie de build_crm.py>/soha-crm/assets banc/assets
    cd banc && python3 regard.py . && python3 cloison.py .

Chromium est appelé par son chemin explicite dans les deux scripts : à ajuster
selon la machine.

## Ce que ce banc a trouvé

Que toute la mise en page pour petits écrans était morte. Le cloisonnement du
CSS préfixait `@media (max-width:860px)` comme s'il s'agissait d'un sélecteur —
`#soha-crm-racine @media (…)`. Un navigateur jette une règle comme celle-là sans
rien dire. `build_crm.py` refuse maintenant de fabriquer une extension où cela
se reproduirait.
