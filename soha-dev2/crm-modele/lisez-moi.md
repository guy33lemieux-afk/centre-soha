# Centre Soha — CRM · extension WordPress v1.0.0

## Ce que c'est

L'interface React du CRM, inchangée, posée sur la base de données de WordPress.
Elle appelait `window.storage` — un objet qu'aucun navigateur ne fournit. Toutes
les écritures partaient dans le vide, et le `try { } catch (e) { }` de la source
rendait la panne muette : on croyait enregistrer, rien n'était gardé.

L'extension fournit cet objet. Le JSX d'origine est conservé tel quel dans
`source/crm-interface-origine.jsx`.

## Installation

1. Extensions → Ajouter → Téléverser une extension → ce fichier `.zip` → Installer.
2. Activer.
3. Un menu **CRM Soha** apparaît dans la colonne de gauche, en troisième position.

## Ce qu'il faut savoir le premier jour

- **Cinq fiches d'exemple** apparaissent au premier chargement : elles viennent du
  prototype. Supprime-les — ce sont les seules données fictives.
- **Qui y a accès** : toute personne pouvant modifier les pages (administratrice,
  éditeurs). Pour resserrer à l'administratrice seule, ajouter au thème :
  `add_filter('soha_crm_capacite', fn() => 'manage_options');`
- **La sauvegarde** : le registre vit dans la base du site. Il est donc inclus
  dans les sauvegardes UpdraftPlus — à condition que celles-ci partent sur une
  destination hors serveur. C'est à vérifier avant d'entrer de vraies personnes.
- **Deux personnes en même temps** : si quelqu'un d'autre a enregistré depuis ton
  chargement, une bande ambre te demande de recharger. Elle protège le travail de
  l'autre ; ne l'ignore pas.
- **Pas de suppression automatique.** La règle des 24 mois de la politique de
  confidentialité porte sur les demandes reçues par formulaire, pas sur le
  registre des personnes qui fréquentent le centre. Supprimer est un geste, le
  tien, dans l'interface.

## Ce qu'il y a dedans

    soha-crm.php                      l'extension : l'écran, les deux routes REST
    uninstall.php                     l'effacement, à la suppression seulement
    assets/adaptateur.js              `window.storage`, adossé à la base
    assets/crm.js                     l'interface compilée (64 Ko)
    assets/polices.css  + polices/    les trois familles du canon, servies d'ici
    source/crm-interface-origine.jsx  le JSX d'origine, intact

Aucun appel à un serveur extérieur : ni Google Fonts, ni CDN. Mesuré à zéro.
