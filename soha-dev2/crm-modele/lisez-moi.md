# Centre Soha — CRM · extension WordPress v1.2.0

## Ce que c'est

Trois choses, dans une seule extension.

**Le répertoire.** L'interface React du CRM, inchangée, posée sur la base de
données de WordPress. Elle appelait `window.storage` — un objet qu'aucun
navigateur ne fournit. Toutes les écritures partaient dans le vide, et le
`try { } catch (e) { }` de la source rendait la panne muette : on croyait
enregistrer, rien n'était gardé. L'extension fournit cet objet. Le JSX d'origine
est conservé tel quel dans `source/crm-interface-origine.jsx`.

**Les demandes.** Chaque envoi de formulaire du site est écrit en base **avant**
que le courriel parte. Le courriel devient l'avis ; la base devient la mémoire.
Une demande se verse au répertoire en un clic, sans créer de doublon si la
personne y est déjà — et **si c'est une location, la réservation est créée en
même temps**, avec l'espace, la date et le tarif que la personne avait sous les
yeux dans l'estimateur.

**La sauvegarde.** Le registre entier tient dans une option : c'est ce qui le
rend simple, et c'est un seul endroit où tout perdre. Un écran pour le
télécharger, le remettre, et un état d'avant conservé pour défaire une fois.

**Les accès.** Une permission à part, donnée à des personnes nommées, avec un
écran pour la donner et la retirer.

## Installation

1. Extensions → Ajouter → Téléverser une extension → ce fichier `.zip` → Installer.
2. Activer.
3. Un menu **CRM Soha** apparaît dans la colonne de gauche, en troisième
   position, avec quatre entrées : **Répertoire**, **Demandes**, **Sauvegarde**
   et **Accès**.

## Le premier jour, dans cet ordre

1. **Ouvre « Accès »** et coche Mala, Dominique, Cassandra et Fred. Les comptes
   administrateurs y sont d'office : leur ligne est grisée, et c'est en leur
   retirant le rôle qu'on leur retire le CRM.
2. **Ouvre « Répertoire »**, crée un contact d'essai, **recharge la page**.
   S'il est encore là, le CRM garde — ce qu'il ne faisait pas avant.
3. **Envoie un formulaire de location depuis le site**, en passant par
   l'estimateur. Regarde « Demandes » : elle doit y être. Clique **Verser au
   répertoire** — tu dois obtenir la fiche *et* la réservation en devis, avec le
   bon espace, la bonne date et le montant que tu avais vu à l'écran.
4. **Télécharge une première sauvegarde** depuis l'écran « Sauvegarde », et
   range-la ailleurs que sur le serveur.

> **Les cinq artisanes déjà présentes ne sont pas des données d'exemple.**
> Dominique Mennessier, Ève Morin, Jeimy Oviedo, Julie Habart et Marjolaine
> Blouin viennent du prototype avec leurs matricules réels. Ce sont de vraies
> personnes du centre : garde-les, complète-les, ne les efface pas.

## Ce qu'il faut savoir

- **Vous êtes quatre.** Si quelqu'un a enregistré depuis ton chargement, une
  bande ambre te le dit **avec son nom** et te demande de recharger. Elle
  protège son travail ; ne l'ignore pas.
- **La sauvegarde.** Tout vit dans la base du site : le répertoire comme les
  demandes. C'est donc UpdraftPlus qui les sauvegarde — à condition que ses
  sauvegardes partent sur une destination hors serveur.
- **Les quatre espaces.** Le CRM nommait « Grande salle · Studio · Petite
  salle » ; le site, l'estimateur et le formulaire nomment **Studio · Espace
  SÖHA · Salle 4 · Salles 1·2·3**. Le CRM parle maintenant la même langue —
  deux vocabulaires pour un même lieu, c'est une réservation mal saisie par mois
  et un revenu qu'on ne sait plus attribuer.
- **Rien n'est deviné.** Une date que le formulaire n'a pas su donner reste
  vide et part dans la note. L'heure de début et de fin reste vide : elle se
  convient au téléphone. Une réservation arrive toujours en **devis**, jamais
  confirmée — c'est toi qui confirmes.
- **La conservation.** Les demandes reçues par formulaire sont effacées
  automatiquement après **24 mois**, comme l'annonce la politique de
  confidentialité. Le passage se fait une fois par jour, et l'écran « Demandes »
  affiche la date du dernier.
- **Le répertoire, lui, n'est jamais purgé.** Les 24 mois portent sur les
  demandes, pas sur les personnes qui fréquentent le centre. Effacer d'office la
  fiche de quelqu'un qui vient depuis trois ans serait une faute, pas une
  conformité. Supprimer reste un geste : le tien.
- **Ce qui n'est pas gardé** : ni adresse IP, ni empreinte de navigateur. On
  garde ce que la personne a écrit, rien de ce qu'elle n'a pas choisi de dire.
- **La désactivation ne perd rien.** L'effacement n'a lieu qu'à la suppression
  de l'extension, par `uninstall.php`.

## Ce qu'il y a dedans

    soha-crm.php                      l'en-tête, les constantes, l'écran du CRM
    inc/acces.php                     la permission, et l'écran qui la donne
    inc/registre.php                  le registre et ses deux routes REST
    inc/demandes.php                  la capture, la purge, le versement
    inc/locations.php                 la demande de location devient réservation
    inc/ecran-demandes.php            l'écran des demandes et l'export CSV
    inc/sauvegarde.php                télécharger, remettre, défaire une fois
    uninstall.php                     l'effacement, à la suppression seulement
    assets/adaptateur.js              `window.storage`, adossé à la base
    assets/crm.js                     l'interface compilée
    assets/polices.css  + polices/    les trois familles du canon, servies d'ici
    source/crm-interface-origine.jsx  le JSX d'origine, intact

## Pour la personne qui reprendra le code

- La permission est `soha_acceder_crm`. Pour la resserrer sans toucher à
  l'extension : `add_filter('soha_crm_capacite', fn() => 'manage_options');`
- La durée de conservation : `add_filter('soha_crm_conservation_mois', fn() => 12);`
- Les espaces du 961, si un cinquième s'ouvre : `add_filter('soha_crm_espaces', …)`
  — la table associe le libellé du formulaire au nom court du CRM.
- Après l'archivage d'une demande : `do_action('soha_crm_demande_archivee', $id, $champs)`.
- Le registre est une option, `soha_crm_etat`, jamais chargée automatiquement,
  plafonnée à 5 Mo, avec un compteur de révisions qui refuse une écriture
  périmée. Une table dédiée viendra quand il faudra chercher et recouper côté
  serveur ; à quelques centaines de fiches, elle ne se justifie pas.

Aucun appel à un serveur extérieur : ni Google Fonts, ni CDN. Mesuré à zéro dans
un WordPress réel.
