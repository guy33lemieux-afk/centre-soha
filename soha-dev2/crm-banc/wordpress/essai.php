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

/* --- désactivation --------------------------------------------------------- */
deactivate_plugins('soha-crm/soha-crm.php');
dit("la désactivation arrête la purge", false === wp_next_scheduled('soha_crm_purge'));
$apres = get_posts(array('post_type' => 'soha_demande', 'posts_per_page' => -1, 'post_status' => 'any'));
dit("la désactivation ne perd RIEN",
    '' !== (string) get_option(SOHA_CRM_OPTION, '') && 4 === count($apres),
    count($apres) . ' demandes, registre ' . strlen((string) get_option(SOHA_CRM_OPTION, '')) . ' octets');

echo "\n", str_repeat('─', 72), "\n";
printf("%d réussites, %d échecs\n", $ok, $ko);
exit($ko > 0 ? 1 : 0);
