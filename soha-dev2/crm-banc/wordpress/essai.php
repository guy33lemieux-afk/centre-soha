<?php
/**
 * Le banc WordPress : on active l'extension pour de vrai, et on la pousse.
 * Rien n'est simulé côté WordPress — c'est un 6.8.3 complet sur SQLite.
 */
$_SERVER["HTTP_HOST"] = "127.0.0.1:8899";
$_SERVER["REQUEST_URI"] = "/wp-admin/";
$_SERVER["SERVER_NAME"] = "127.0.0.1";
$_SERVER["REQUEST_METHOD"] = "GET";
define('WP_ADMIN', true);
require __DIR__ . '/wordpress/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/user.php';
require_once __DIR__ . '/faux-mailchimp.php';

$ok = 0; $ko = 0;
function dit($quoi, $vrai, $detail = '') {
    global $ok, $ko;
    $vrai ? $ok++ : $ko++;
    printf("%s %-52s %s\n", $vrai ? ' ✓' : ' ✗', $quoi, $detail);
}

/* ---------------------------------------------------------------- activation */
/* Elle a été activée dans le processus précédent, comme le ferait WordPress. */
dit("l'extension est active", is_plugin_active('soha-crm/soha-crm.php'));
dit("le type de contenu « demande » est enregistré", (bool) get_post_type_object('soha_demande'));

/* ------------------------------------------------------------------- accès */
$admin = get_role('administrator');
dit("l'administratrice a la capacité", $admin && $admin->has_cap('soha_acceder_crm'));

$mala = get_user_by('login', 'mala');
wp_set_current_user($mala->ID);
dit("Mala (admin) peut ouvrir le CRM", current_user_can(soha_crm_capacite()));

$ids = array();
foreach (array('dominique' => 'editor', 'cassandra' => 'author', 'fred' => 'subscriber') as $login => $role) {
    $id = username_exists($login) ?: wp_insert_user(array(
        'user_login' => $login, 'user_pass' => wp_generate_password(),
        'user_email' => $login . '@exemple.test', 'display_name' => ucfirst($login), 'role' => $role,
    ));
    $ids[$login] = $id;
}
wp_set_current_user($ids['fred']);
dit("Fred (abonné) ne peut PAS ouvrir le CRM", !current_user_can(soha_crm_capacite()));
wp_set_current_user($ids['dominique']);
dit("Dominique (éditrice) ne peut PAS non plus, d'office", !current_user_can(soha_crm_capacite()));

foreach (array('dominique', 'cassandra', 'fred') as $login) {
    $u = get_userdata($ids[$login]);
    $u->add_cap('soha_acceder_crm');
}
foreach (array('dominique', 'cassandra', 'fred') as $login) {
    /* `wp_set_current_user` sort tout de suite si l'identifiant ne change pas :
       l'objet en mémoire, chargé avant qu'on donne la capacité, resterait
       périmé. On repasse donc par zéro. Ce n'est pas un détail d'essai —
       c'est pourquoi une permission accordée n'est visible qu'au chargement
       de page suivant. */
    clean_user_cache($ids[$login]);
    wp_set_current_user(0);
    wp_set_current_user($ids[$login]);
    dit("$login, une fois autorisé·e, entre", current_user_can(soha_crm_capacite()));
}
wp_set_current_user($ids['fred']);
$u = get_userdata($ids['fred']); $u->remove_cap('soha_acceder_crm');
clean_user_cache($ids['fred']); wp_set_current_user(0); wp_set_current_user($ids['fred']);
dit("le retrait de l'accès referme la porte", !current_user_can(soha_crm_capacite()));
$u->add_cap('soha_acceder_crm');

wp_set_current_user(0);
wp_set_current_user($mala->ID);
$acces = soha_crm_qui_a_acces();
dit("l'écran liste les personnes autorisées", count($acces) === 4, count($acces) . ' : ' .
    implode(', ', array_map(function ($u) { return $u->display_name; }, $acces)));

/* --------------------------------------------------------------- le registre */
$etat = soha_crm_registre_lire();
dit("registre vide au départ", '' === $etat['valeur'] && 0 === $etat['revision']);

$registre = array('contacts' => array(), 'reservations' => array(), 'ateliers' => array(), 'v' => 2);
$rev = soha_crm_registre_ecrire(wp_json_encode($registre));
dit("une écriture avance la révision", 1 === $rev, "revision=$rev");
/* WordPress 6.8 a remplacé « yes/no » par « on/off/auto-… » : on teste le sens,
   pas le mot, pour que l'essai survive à la prochaine version. */
$autoload = soha_autoload_de(SOHA_CRM_OPTION);
dit("l'option n'est PAS chargée automatiquement",
    in_array($autoload, array('no', 'off', 'auto-off'), true), "autoload=$autoload");

$d = soha_crm_dernier_auteur();
dit("on sait qui a écrit en dernier", 'mala' === strtolower($d['nom']), $d['nom']);

/* --------------------------------------------------------------- les routes */
$req = new WP_REST_Request('GET', '/soha-crm/v1/etat');
$rep = rest_do_request($req);
dit("GET /etat répond 200", 200 === $rep->get_status());
dit("GET /etat rend la révision", 1 === $rep->get_data()['revision']);

$req = new WP_REST_Request('POST', '/soha-crm/v1/etat');
$req->set_header('content-type', 'application/json');
$req->set_body(wp_json_encode(array('valeur' => wp_json_encode($registre), 'revision' => 1)));
$rep = rest_do_request($req);
dit("POST avec la bonne révision passe", 200 === $rep->get_status(), 'statut ' . $rep->get_status());

$req = new WP_REST_Request('POST', '/soha-crm/v1/etat');
$req->set_header('content-type', 'application/json');
$req->set_body(wp_json_encode(array('valeur' => wp_json_encode($registre), 'revision' => 1)));
$rep = rest_do_request($req);
dit("POST avec une révision périmée est refusé (409)", 409 === $rep->get_status(), 'statut ' . $rep->get_status());
$corps = $rep->get_data();
dit("le refus nomme la personne", !empty($corps['qui']), isset($corps['qui']) ? $corps['qui'] : '');

$req = new WP_REST_Request('POST', '/soha-crm/v1/etat');
$req->set_header('content-type', 'application/json');
$req->set_body(wp_json_encode(array('valeur' => 'ceci n\'est pas du JSON', 'revision' => 2)));
$rep = rest_do_request($req);
dit("un registre illisible est refusé (400)", 400 === $rep->get_status(), 'statut ' . $rep->get_status());

$req = new WP_REST_Request('POST', '/soha-crm/v1/etat');
$req->set_header('content-type', 'application/json');
$req->set_body(wp_json_encode(array('valeur' => wp_json_encode(array('x' => str_repeat('a', 6 * 1024 * 1024))), 'revision' => 2)));
$rep = rest_do_request($req);
dit("un envoi trop gros est refusé (413)", 413 === $rep->get_status(), 'statut ' . $rep->get_status());

wp_set_current_user(0);
$rep = rest_do_request(new WP_REST_Request('GET', '/soha-crm/v1/etat'));
dit("un visiteur non connecté est refusé (401/403)", in_array($rep->get_status(), array(401, 403), true), 'statut ' . $rep->get_status());
wp_set_current_user($mala->ID);

function soha_autoload_de($nom) {
    global $wpdb;
    return $wpdb->get_var($wpdb->prepare("SELECT autoload FROM {$wpdb->options} WHERE option_name = %s", $nom));
}


/* ========================================================================== */
/*  Phase 1 — ne plus rien perdre                                             */
/* ========================================================================== */

/**
 * Un faux enregistrement Elementor : la seule chose que le crochet reçoit est
 * un objet avec `get()`. On imite exactement ce que Elementor Pro passe, plutôt
 * que d'appeler nos fonctions internes — sinon on ne testerait que soi-même.
 */
class Faux_Record {
    private $champs; private $reglages;
    public function __construct($champs, $nom_form) {
        $this->champs = $champs;
        $this->reglages = array('form_name' => $nom_form);
    }
    public function get($quoi) {
        if ('fields' === $quoi) return $this->champs;
        if ('form_settings' === $quoi) return $this->reglages;
        return null;
    }
}

function envoi($nom_form, $champs) {
    do_action('elementor_pro/forms/new_record', new Faux_Record($champs, $nom_form), null);
}

envoi('Demande de location', array(
    'nom'        => array('title' => 'Nom complet',  'type' => 'text',  'value' => 'Camille Trottier'),
    'field_x1'   => array('title' => 'Courriel',     'type' => 'email', 'value' => 'camille@exemple.test'),
    'tel'        => array('title' => 'Téléphone',    'type' => 'tel',   'value' => '514 555 0142'),
    'espace'     => array('title' => 'Espace',       'type' => 'select','value' => 'Espace SÖHA'),
    'message'    => array('title' => 'Message',      'type' => 'textarea', 'value' => "Bonjour,\nj'aimerais réserver un samedi."),
    'vide'       => array('title' => 'Sans réponse', 'type' => 'text',  'value' => '   '),
    'consent'    => array('title' => "Je consens à recevoir l'infolettre", 'type' => 'acceptance', 'value' => 'on'),
));

$demandes = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => -1));
dit("l'envoi d'un formulaire est archivé", 1 === count($demandes), count($demandes) . ' demande(s)');

$d = $demandes[0];
dit("le nom est repéré",       'Camille Trottier' === get_post_meta($d->ID, '_soha_nom', true), get_post_meta($d->ID, '_soha_nom', true));
dit("le courriel est repéré",  'camille@exemple.test' === get_post_meta($d->ID, '_soha_courriel', true), get_post_meta($d->ID, '_soha_courriel', true));
dit("le téléphone est repéré", '514 555 0142' === get_post_meta($d->ID, '_soha_telephone', true), get_post_meta($d->ID, '_soha_telephone', true));
dit("le consentement infolettre est vu", 1 === (int) get_post_meta($d->ID, '_soha_consentement', true));
$champs = (array) get_post_meta($d->ID, '_soha_champs', true);
dit("les champs vides sont écartés", 6 === count($champs), count($champs) . ' champs gardés');
dit("le message multiligne est intact",
    false !== strpos(soha_crm_resumer($d->ID, 2000), "j'aimerais réserver un samedi"));
$type = get_post_type_object('soha_demande');
dit("le type de contenu n'est ni public ni interrogeable",
    $type && false === $type->public && false === $type->publicly_queryable
    && true === $type->exclude_from_search);

/* --- verser au répertoire ------------------------------------------------- */
$r = soha_crm_verser_au_repertoire($d->ID);
dit("la demande se verse au répertoire", !is_wp_error($r) && 'cree' === $r['geste'],
    is_wp_error($r) ? $r->get_error_message() : $r['geste']);

$reg = json_decode(soha_crm_registre_lire()['valeur'], true);
dit("le contact est dans le registre", 1 === count($reg['contacts']));
$c = $reg['contacts'][0];
dit("la fiche a la forme attendue par le CRM",
    isset($c['id'], $c['nom'], $c['type'], $c['statut'], $c['interactions'], $c['infolettre']['abonne']),
    implode(',', array_keys($c)));
dit("elle arrive en « prospect / Nouveau »", 'prospect' === $c['type'] && 'Nouveau' === $c['statut']);
dit("le consentement infolettre est daté",
    true === $c['infolettre']['abonne'] && '' !== $c['infolettre']['consentement'],
    $c['infolettre']['consentement']);
dit("l'échange est inscrit dans l'historique", 1 === count($c['interactions']));
dit("la demande est marquée traitée", 1 === (int) get_post_meta($d->ID, '_soha_traitee', true));
dit("verser deux fois est refusé", is_wp_error(soha_crm_verser_au_repertoire($d->ID)));

/* --- le même courriel ne crée pas de doublon ------------------------------ */
envoi('Contact', array(
    'n' => array('title' => 'Nom',      'type' => 'text',  'value' => 'Camille T.'),
    'c' => array('title' => 'Courriel', 'type' => 'email', 'value' => 'CAMILLE@exemple.test'),
    'm' => array('title' => 'Message',  'type' => 'textarea', 'value' => 'Je relance.'),
));
$deux = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => -1, 'orderby' => 'ID', 'order' => 'DESC'));
$r2 = soha_crm_verser_au_repertoire($deux[0]->ID);
$reg = json_decode(soha_crm_registre_lire()['valeur'], true);
dit("le même courriel ne crée PAS de doublon",
    !is_wp_error($r2) && 'fusionnee' === $r2['geste'] && 1 === count($reg['contacts']),
    count($reg['contacts']) . ' contact(s)');
dit("la relance s'ajoute à son historique", 2 === count($reg['contacts'][0]['interactions']));
dit("la casse du courriel n'y change rien", 1 === count($reg['contacts']));

/* --- une personne sans courriel ------------------------------------------- */
envoi('Contact', array(
    'n' => array('title' => 'Nom',     'type' => 'text',     'value' => 'Anonyme du 961'),
    'm' => array('title' => 'Message', 'type' => 'textarea', 'value' => 'Question sur les ateliers.'),
));
$trois = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => 1, 'orderby' => 'ID', 'order' => 'DESC'));
$r3 = soha_crm_verser_au_repertoire($trois[0]->ID);
$reg = json_decode(soha_crm_registre_lire()['valeur'], true);
dit("une demande sans courriel se verse quand même",
    !is_wp_error($r3) && 2 === count($reg['contacts']),
    is_wp_error($r3) ? $r3->get_error_message() : count($reg['contacts']) . ' contacts');
dit("et n'est pas abonnée à l'infolettre sans consentement",
    false === $reg['contacts'][0]['infolettre']['abonne']);

/* --- la purge des 24 mois -------------------------------------------------- */
$vieille = wp_insert_post(array(
    'post_type' => 'soha_demande', 'post_status' => 'publish',
    'post_title' => 'Vieille demande',
    'post_date' => gmdate('Y-m-d H:i:s', strtotime('-25 months')),
    'post_date_gmt' => gmdate('Y-m-d H:i:s', strtotime('-25 months')),
));
$recente = wp_insert_post(array(
    'post_type' => 'soha_demande', 'post_status' => 'publish',
    'post_title' => 'Demande de 23 mois',
    'post_date' => gmdate('Y-m-d H:i:s', strtotime('-23 months')),
    'post_date_gmt' => gmdate('Y-m-d H:i:s', strtotime('-23 months')),
));
$n = soha_crm_purger();
dit("la purge efface ce qui a plus de 24 mois", 1 === $n && !get_post($vieille), "$n effacée(s)");
dit("elle épargne ce qui a 23 mois", (bool) get_post($recente));
$restantes = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => -1));
dit("elle épargne toutes les autres", 4 === count($restantes), count($restantes) . ' restantes');
$p = get_option('soha_crm_derniere_purge');
dit("elle laisse une trace datée", !empty($p['quand']) && 1 === (int) $p['effacees']);
dit("la purge est planifiée tous les jours", 'daily' === wp_get_schedule('soha_crm_purge'), (string) wp_get_schedule('soha_crm_purge'));

/* --- ce que voit quelqu'un sans droits ------------------------------------ */
$sans = wp_insert_user(array('user_login' => 'passant', 'user_pass' => wp_generate_password(),
                             'user_email' => 'passant@exemple.test', 'role' => 'subscriber'));
wp_set_current_user(0); wp_set_current_user($sans);
dit("un abonné ne voit pas les demandes", !current_user_can(soha_crm_capacite()));
wp_set_current_user(0); wp_set_current_user($mala->ID);


/* ========================================================================== */
/*  Phase 2 — la demande devient une réservation                              */
/* ========================================================================== */

/* Le vrai formulaire du site : ses identifiants et ses libellés, tels que le
   kit v12 les définit. Si le formulaire change, cet essai doit tomber. */
function demande_de_location($extra = array()) {
    $champs = array(
        'vousetes'     => array('title' => 'Vous êtes',        'type' => 'select',   'value' => 'Praticien·ne / thérapeute'),
        'nom'          => array('title' => 'Nom complet',      'type' => 'text',     'value' => 'Léa Bouchard'),
        'courriel'     => array('title' => 'Courriel',         'type' => 'email',    'value' => 'lea@exemple.test'),
        'tel'          => array('title' => 'Téléphone',        'type' => 'tel',      'value' => '438 555 0199'),
        'espace'       => array('title' => 'Espace',           'type' => 'select',   'value' => 'Espace SÖHA (2200 pi²)'),
        'journee'      => array('title' => 'Type de journée',  'type' => 'radio',    'value' => 'Fin de semaine'),
        'plage'        => array('title' => 'Plage horaire',    'type' => 'radio',    'value' => 'Demi-journée'),
        'date'         => array('title' => 'Date souhaitée',   'type' => 'date',     'value' => '2026-10-17'),
        'frequence'    => array('title' => 'Fréquence',        'type' => 'select',   'value' => 'Ponctuel'),
        'usage'        => array('title' => 'Pour quoi faire',  'type' => 'select',   'value' => 'Cours ou atelier'),
        'details'      => array('title' => 'Détails',          'type' => 'textarea', 'value' => 'Une quinzaine de personnes.'),
        'estim_espace' => array('title' => 'Estimation — espace', 'type' => 'hidden', 'value' => 'Espace SÖHA'),
        'estim_jour'   => array('title' => 'Estimation — type de journée', 'type' => 'hidden', 'value' => 'Fin de semaine'),
        'estim_plage'  => array('title' => 'Estimation — plage', 'type' => 'hidden', 'value' => 'Demi-journée'),
        'estim_tarif'  => array('title' => 'Estimation — tarif affiché', 'type' => 'hidden', 'value' => '400 $ +tx'),
    );
    foreach ($extra as $k => $v) {
        if (null === $v) { unset($champs[$k]); } else { $champs[$k]['value'] = $v; }
    }
    return $champs;
}

/**
 * Toujours passer par le vrai chemin : l'envoi du formulaire, puis le
 * versement. Appeler `soha_crm_reservation_depuis()` sur le tableau brut d'un
 * formulaire donnerait un faux résultat — l'extension normalise les champs à
 * l'archivage, et c'est cette forme-là qu'elle relit ensuite.
 */
function verser_une_location($extra = array()) {
    envoi('Demande de location', demande_de_location($extra));
    $d = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => 1,
                         'orderby' => 'ID', 'order' => 'DESC'));
    $r = soha_crm_verser_au_repertoire($d[0]->ID);
    $reg = json_decode(soha_crm_registre_lire()['valeur'], true);
    return array($r, $reg, $reg['reservations'][0]);
}

/* La demande de la phase 1 portait déjà un espace : elle a donc, elle aussi,
   produit une réservation. On compte donc l'écart, pas le total. */
$avant_resa = count(json_decode(soha_crm_registre_lire()['valeur'], true)['reservations']);
list($r, $reg, $resa) = verser_une_location();

dit("verser une location crée aussi la réservation",
    $avant_resa + 1 === count($reg['reservations']),
    count($reg['reservations']) . ' au total');
dit("l'espace est celui du 961, sans la superficie", 'Espace SÖHA' === $resa['espace'], $resa['espace']);
dit("la date souhaitée est reprise", '2026-10-17' === $resa['date'], $resa['date']);
dit("le tarif affiché devient un prix", '400' === $resa['prix'], $resa['prix']);
dit("elle arrive en devis, jamais confirmée", 'devis' === $resa['paiement']);
dit("elle est rattachée à la fiche", !empty($resa['contactId'])
    && $resa['contactId'] === $reg['contacts'][0]['id']);
dit("l'heure exacte reste à convenir", '' === $resa['debut'] && '' === $resa['fin']);
dit("la plage et l'usage sont dans la note",
    false !== strpos($resa['note'], 'Demi-journée')
    && false !== strpos($resa['note'], 'Cours ou atelier'));
dit("l'écran annonce la réservation créée", !empty($r['reservation']), $r['reservation']);

/* --- les quatre espaces se traduisent tous ------------------------------- */
$traduits = array();
$i = 0;
foreach (soha_crm_espaces() as $du_site => $_) {
    list($_r, $_reg, $rr) = verser_une_location(array(
        'espace'       => $du_site,
        'estim_espace' => null,
        'courriel'     => 'espace' . (++$i) . '@exemple.test',
        'nom'          => 'Essai espace ' . $i,
    ));
    $traduits[] = $rr['espace'];
}
dit("les quatre espaces se traduisent", $traduits === array_values(soha_crm_espaces()),
    implode(' · ', $traduits));

/* --- « Récurrent (résident·e) » ne devient pas un rythme inventé ---------- */
list($_r, $_reg, $rr) = verser_une_location(array(
    'frequence' => 'Récurrent (résident·e)', 'courriel' => 'recurrent@exemple.test',
    'nom' => 'Essai récurrence'));
dit("« Récurrent » reste « Récurrent »", 'Récurrent' === $rr['recurrence'], $rr['recurrence']);

/* --- une date que le formulaire n'a pas su donner ------------------------- */
list($_r, $_reg, $rd) = verser_une_location(array(
    'date' => 'le 17 ou le 18', 'courriel' => 'date@exemple.test', 'nom' => 'Essai date'));
dit("une date non reconnue n'est pas devinée", '' === $rd['date'], $rd['date']);
dit("elle est dite dans la note", false !== strpos($rd['note'], 'le 17 ou le 18'));

/* --- une demande sans espace ne crée pas de réservation ------------------- */
$avant_resa = count(json_decode(soha_crm_registre_lire()['valeur'], true)['reservations']);
envoi('Demande de location', demande_de_location(array(
    'espace' => null, 'estim_espace' => null,
    'courriel' => 'sansespace@exemple.test', 'nom' => 'Essai sans espace')));
$d = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => 1, 'orderby' => 'ID', 'order' => 'DESC'));
$rs = soha_crm_verser_au_repertoire($d[0]->ID);
$reg = json_decode(soha_crm_registre_lire()['valeur'], true);
dit("un formulaire sans espace ne crée pas de réservation",
    $avant_resa === count($reg['reservations']) && empty($rs['reservation']));

/* --- une demande de contact non plus -------------------------------------- */
$avant_resa = count($reg['reservations']);
envoi('Contact', array(
    'n' => array('title' => 'Nom',      'type' => 'text',     'value' => 'Simon Pelletier'),
    'c' => array('title' => 'Courriel', 'type' => 'email',    'value' => 'simon@exemple.test'),
    'm' => array('title' => 'Message',  'type' => 'textarea', 'value' => 'Question sur les ateliers.'),
));
$ct = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => 1, 'orderby' => 'ID', 'order' => 'DESC'));
$rc = soha_crm_verser_au_repertoire($ct[0]->ID);
$reg = json_decode(soha_crm_registre_lire()['valeur'], true);
dit("une demande de contact ne crée pas de réservation",
    $avant_resa === count($reg['reservations']) && empty($rc['reservation']));

/* ========================================================================== */
/*  La sauvegarde                                                             */
/* ========================================================================== */

$avant = soha_crm_registre_lire();
$compte = soha_crm_compter();
dit("le compte affiché correspond au registre",
    $compte['contacts'] === count($reg['contacts'])
    && $compte['reservations'] === count($reg['reservations']),
    $compte['contacts'] . ' fiches · ' . $compte['reservations'] . ' réservations');

dit("un registre valide est reçu", soha_crm_registre_recevable($avant['valeur']));
dit("un JSON qui n'est pas un registre est refusé",
    !soha_crm_registre_recevable('{"nimporte":"quoi"}'));
dit("un registre sans réservations est refusé",
    !soha_crm_registre_recevable('{"contacts":[]}'));
dit("une fiche sans identifiant est refusée",
    !soha_crm_registre_recevable('{"contacts":[{"nom":"X"}],"reservations":[],"ateliers":[]}'));
dit("du texte qui n'est pas du JSON est refusé", !soha_crm_registre_recevable('bonjour'));
dit("un fichier trop gros est refusé",
    !soha_crm_registre_recevable(str_repeat('a', SOHA_CRM_TAILLE_MAX + 1)));

/* --- restaurer, puis revenir ---------------------------------------------- */
$vide = wp_json_encode(array('contacts' => array(), 'reservations' => array(), 'ateliers' => array(), 'v' => 2));
update_option(SOHA_CRM_AVANT, array('valeur' => $avant['valeur'], 'quand' => time()), false);
soha_crm_registre_ecrire($vide);
dit("on peut remplacer le registre", 0 === count(json_decode(soha_crm_registre_lire()['valeur'], true)['contacts']));

$conserve = get_option(SOHA_CRM_AVANT);
soha_crm_registre_ecrire($conserve['valeur']);
$revenu = json_decode(soha_crm_registre_lire()['valeur'], true);
dit("et revenir à l'état d'avant, intact",
    count($revenu['contacts']) === count($reg['contacts'])
    && count($revenu['reservations']) === count($reg['reservations']),
    count($revenu['contacts']) . ' fiches retrouvées');

/* ========================================================================== */
/*  Phase 3 — l'infolettre chez Mailchimp                                     */
/* ========================================================================== */

Faux_Mailchimp::brancher();

/* --- la clé --------------------------------------------------------------- */
dit("une clé sans centre de données est refusée",
    is_wp_error(soha_crm_info_appel('GET', '', null, 'clesansdc')));
dit("le centre de données se lit dans la clé",
    'us21' === soha_crm_info_centre('bonne-cle-us21')
    && '' === soha_crm_info_centre('nimportequoi'));
dit("une mauvaise clé est refusée par Mailchimp",
    is_wp_error(soha_crm_info_compte('mauvaise-cle-us21')));

$compte = soha_crm_info_compte('bonne-cle-us21');
dit("une bonne clé donne le nom du compte",
    !is_wp_error($compte) && 'Centre Soha' === $compte['compte'],
    is_wp_error($compte) ? $compte->get_error_message() : $compte['compte']);
$dernier = end(Faux_Mailchimp::$appels);
dit("l'authentification est bien du Basic",
    0 === strpos($dernier['entetes']['Authorization'], 'Basic '));

$auds = soha_crm_info_audiences('bonne-cle-us21');
dit("les audiences se listent", !is_wp_error($auds) && 2 === count($auds)
    && 'aud961' === $auds[0]['id'],
    is_wp_error($auds) ? $auds->get_error_message() : count($auds) . ' audiences');

/* --- rien ne part tant que ce n'est pas branché --------------------------- */
dit("sans liaison, rien n'est actif", !soha_crm_info_active());
$reg2 = json_decode(soha_crm_registre_lire()['valeur'], true);
$reg2['contacts'][0]['infolettre'] = array('abonne' => true, 'consentement' => '2026-09-10',
                                           'source' => 'manuel', 'desabonne' => false);
soha_crm_registre_ecrire(wp_json_encode($reg2));
dit("sans liaison, la file reste vide", 0 === count((array) get_option(SOHA_CRM_INFO_FILE, array())));

update_option(SOHA_CRM_INFO_CLE, 'bonne-cle-us21', false);
update_option(SOHA_CRM_INFO_LISTE, 'aud961', false);
dit("la liaison est en place", soha_crm_info_active());

/* --- cocher l'infolettre sur une fiche met en file ------------------------ */
$reg2 = json_decode(soha_crm_registre_lire()['valeur'], true);
$i = null;
foreach ($reg2['contacts'] as $k => $c) {
    if (!empty($c['courriel']) && empty($c['infolettre']['abonne'])) { $i = $k; break; }
}
$courriel_test = strtolower($reg2['contacts'][$i]['courriel']);
$reg2['contacts'][$i]['infolettre'] = array('abonne' => true, 'consentement' => '2026-09-10',
                                            'source' => 'manuel', 'desabonne' => false);
soha_crm_registre_ecrire(wp_json_encode($reg2));
$file = (array) get_option(SOHA_CRM_INFO_FILE, array());
dit("cocher l'infolettre met l'adresse en file",
    isset($file[$courriel_test]) && 'abonne' === $file[$courriel_test]['statut'],
    $courriel_test);
dit("un envoi est planifié, pas immédiat", false !== wp_next_scheduled('soha_crm_infolettre_traiter'));

/* --- l'envoi -------------------------------------------------------------- */
$attendues = count($file);
$n = soha_crm_info_vider_la_file();
dit("la file part chez Mailchimp", $attendues === $n, "$n envoyée(s)");
$m = Faux_Mailchimp::membre($courriel_test);
dit("la personne est inscrite", $m && 'subscribed' === $m['status'], $m ? $m['status'] : 'absente');
dit("son prénom est passé, coupé au premier espace",
    $m && '' !== $m['merge_fields']['FNAME'],
    $m ? $m['merge_fields']['FNAME'] . ' / ' . $m['merge_fields']['LNAME'] : '');
dit("son type et son école servent d'étiquettes", $m && !empty($m['tags']),
    $m ? implode(', ', array_column($m['tags'], 'name')) : '');
dit("la file est vidée", 0 === count((array) get_option(SOHA_CRM_INFO_FILE, array())));

$noms = soha_crm_info_nom('Marie-Claude Tremblay Roy');
dit("un nom composé se coupe une seule fois",
    array('Marie-Claude', 'Tremblay Roy') === $noms, implode(' | ', $noms));
dit("un prénom seul ne fabrique pas de nom", array('Camille', '') === soha_crm_info_nom('Camille'));

/* --- décocher désabonne --------------------------------------------------- */
$reg2 = json_decode(soha_crm_registre_lire()['valeur'], true);
$reg2['contacts'][$i]['infolettre']['abonne'] = false;
soha_crm_registre_ecrire(wp_json_encode($reg2));
soha_crm_info_vider_la_file();
$m = Faux_Mailchimp::membre($courriel_test);
dit("décocher désabonne chez Mailchimp", $m && 'unsubscribed' === $m['status'], $m ? $m['status'] : '');

/* --- et Mailchimp refuse de la réinscrire, ce qui est son droit ----------- */
$reg2 = json_decode(soha_crm_registre_lire()['valeur'], true);
$reg2['contacts'][$i]['infolettre']['abonne'] = true;
soha_crm_registre_ecrire(wp_json_encode($reg2));
soha_crm_info_vider_la_file();
$restante = (array) get_option(SOHA_CRM_INFO_FILE, array());
dit("un refus de réinscription est gardé et expliqué",
    isset($restante[$courriel_test]) && 1 === (int) $restante[$courriel_test]['essais']
    && false !== strpos($restante[$courriel_test]['erreur'], 'unsubscribed'),
    isset($restante[$courriel_test]) ? substr($restante[$courriel_test]['erreur'], 0, 48) : 'file vide');

/* --- un service qui ne répond pas ---------------------------------------- */
update_option(SOHA_CRM_INFO_FILE, array(), false);
soha_crm_info_enfiler('panne@exemple.test', 'abonne', 'Test Panne');
Faux_Mailchimp::$panne = true;
soha_crm_info_vider_la_file();
$f = (array) get_option(SOHA_CRM_INFO_FILE, array());
dit("une panne réseau ne perd pas l'adresse",
    isset($f['panne@exemple.test']) && 1 === (int) $f['panne@exemple.test']['essais']);
dit("le refus est conservé, en clair",
    isset($f['panne@exemple.test']) && false !== strpos($f['panne@exemple.test']['erreur'], 'timed out'),
    isset($f['panne@exemple.test']) ? substr($f['panne@exemple.test']['erreur'], 0, 44) : '');

for ($k = 0; $k < 5; $k++) { soha_crm_info_vider_la_file(); }
$f = (array) get_option(SOHA_CRM_INFO_FILE, array());
dit("après cinq essais on cesse d'insister",
    isset($f['panne@exemple.test']) && (int) $f['panne@exemple.test']['essais'] >= SOHA_CRM_INFO_ESSAIS,
    isset($f['panne@exemple.test']) ? $f['panne@exemple.test']['essais'] . ' essais' : '');
$j = (array) get_option(SOHA_CRM_INFO_JJ, array());
dit("et l'écran saura le dire", 1 === (int) $j['bloques'], $j['bloques'] . ' bloquée(s)');
Faux_Mailchimp::$panne = false;
update_option(SOHA_CRM_INFO_FILE, array(), false);

/* --- le formulaire inscrit sans attendre le versement ---------------------- */
envoi('Contact', array(
    'n' => array('title' => 'Nom',      'type' => 'text',       'value' => 'Ariane Dubé'),
    'c' => array('title' => 'Courriel', 'type' => 'email',      'value' => 'ariane@exemple.test'),
    'i' => array('title' => "Je consens à recevoir l'infolettre", 'type' => 'acceptance', 'value' => 'on'),
    'm' => array('title' => 'Message',  'type' => 'textarea',   'value' => 'Bonjour.'),
));
$f = (array) get_option(SOHA_CRM_INFO_FILE, array());
dit("cocher l'infolettre sur le formulaire inscrit tout de suite",
    isset($f['ariane@exemple.test']), implode(', ', array_keys($f)));
soha_crm_info_vider_la_file();
dit("elle est chez Mailchimp sans que Mala ait rien fait",
    (bool) Faux_Mailchimp::membre('ariane@exemple.test'));

/* --- un formulaire sans consentement n'inscrit personne ------------------- */
envoi('Contact', array(
    'n' => array('title' => 'Nom',      'type' => 'text',     'value' => 'Hugo Sansconsentement'),
    'c' => array('title' => 'Courriel', 'type' => 'email',    'value' => 'hugo@exemple.test'),
    'm' => array('title' => 'Message',  'type' => 'textarea', 'value' => 'Bonjour.'),
));
soha_crm_info_vider_la_file();
dit("sans case cochée, personne n'est inscrit",
    null === Faux_Mailchimp::membre('hugo@exemple.test'));

/* --- le retour de Mailchimp ------------------------------------------------ */
$secret = soha_crm_info_secret();
dit("l'adresse de retour porte un secret",
    false !== strpos(soha_crm_info_adresse_retour(), $secret) && strlen($secret) >= 24);

$req = new WP_REST_Request('POST', '/soha-crm/v1/infolettre/retour');
$req->set_param('type', 'unsubscribe');
$req->set_param('data', array('email' => 'ariane@exemple.test'));
$rep = rest_do_request($req);
dit("sans le secret, le retour est refusé", in_array($rep->get_status(), array(401, 403), true),
    'statut ' . $rep->get_status());

$req->set_param('cle', 'mauvais-secret');
$rep = rest_do_request($req);
dit("avec un mauvais secret aussi", in_array($rep->get_status(), array(401, 403), true),
    'statut ' . $rep->get_status());

$reg2 = json_decode(soha_crm_registre_lire()['valeur'], true);
array_unshift($reg2['contacts'], array(
    'id' => wp_generate_uuid4(), 'nom' => 'Ariane Dubé', 'type' => 'prospect', 'ecole' => '',
    'courriel' => 'ariane@exemple.test', 'telephone' => '', 'statut' => 'Nouveau',
    'etiquettes' => array(), 'note' => '', 'interactions' => array(), 'ajoute' => '2026-09-10',
    'infolettre' => array('abonne' => true, 'consentement' => '2026-09-10',
                          'source' => 'formulaire', 'desabonne' => false),
));
soha_crm_registre_ecrire(wp_json_encode($reg2), 0, false);
$avant_file = count((array) get_option(SOHA_CRM_INFO_FILE, array()));

$req->set_param('cle', $secret);
$rep = rest_do_request($req);
dit("avec le bon secret, le retour passe", 200 === $rep->get_status(), 'statut ' . $rep->get_status());
$reg2 = json_decode(soha_crm_registre_lire()['valeur'], true);
$ariane = null;
foreach ($reg2['contacts'] as $c) {
    if (!empty($c['courriel']) && 'ariane@exemple.test' === strtolower($c['courriel'])) { $ariane = $c; }
}
dit("le désabonnement revient marquer la fiche",
    $ariane && !empty($ariane['infolettre']['desabonne']) && empty($ariane['infolettre']['abonne']));
dit("et ne repart pas chez Mailchimp",
    $avant_file === count((array) get_option(SOHA_CRM_INFO_FILE, array())));

$req2 = new WP_REST_Request('POST', '/soha-crm/v1/infolettre/retour');
$req2->set_param('cle', $secret);
$req2->set_param('type', 'profile');
$req2->set_param('data', array('email' => 'ariane@exemple.test'));
dit("un autre type d'événement est ignoré poliment",
    200 === rest_do_request($req2)->get_status());

/* --- remettre une sauvegarde ne réinscrit pas tout le monde ---------------- */
update_option(SOHA_CRM_INFO_FILE, array(), false);
soha_crm_registre_ecrire(soha_crm_registre_lire()['valeur'], 0, false);
dit("une restauration ne réinscrit personne",
    0 === count((array) get_option(SOHA_CRM_INFO_FILE, array())));

/* --- le paragraphe de la politique ---------------------------------------- */
$para = soha_crm_info_paragraphe();
dit("le paragraphe de la politique nomme Intuit et les États-Unis",
    false !== strpos($para, 'Intuit') && false !== strpos($para, 'États-Unis'));
dit("il dit ce qui NE part pas", false !== strpos($para, 'demeure au Québec'));

Faux_Mailchimp::oublier();
remove_filter('pre_http_request', array('Faux_Mailchimp', 'repondre'), 10);


/* --- désactivation --------------------------------------------------------- */
$avant_desactivation = count(get_posts(array('post_type' => 'soha_demande',
                                             'posts_per_page' => -1, 'post_status' => 'any')));
deactivate_plugins('soha-crm/soha-crm.php');
dit("la désactivation arrête la purge", false === wp_next_scheduled('soha_crm_purge'));
$apres = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => -1, 'post_status' => 'any'));
dit("la désactivation ne perd RIEN",
    '' !== (string) get_option(SOHA_CRM_OPTION, '') && count($apres) === $avant_desactivation,
    count($apres) . ' demandes, registre ' . strlen((string) get_option(SOHA_CRM_OPTION, '')) . ' octets');


echo "\n", str_repeat('─', 72), "\n";
printf("%d réussites, %d échecs\n", $ok, $ko);
exit($ko > 0 ? 1 : 0);
