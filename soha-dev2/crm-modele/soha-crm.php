<?php
/**
 * Plugin Name:       Centre Soha — CRM
 * Plugin URI:        https://centresoha.com/
 * Description:       Le CRM du Centre Soha : l'interface React de Mala adossée à la base de données de WordPress, l'archivage de chaque demande reçue par formulaire, sa transformation en fiche et en réservation, et la gestion nominative des accès.
 * Version:           1.2.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Centre Soha
 * Text Domain:       soha-crm
 *
 * -----------------------------------------------------------------------------
 *  Ce qu'elle fait, et ce qu'elle ne fait pas
 * -----------------------------------------------------------------------------
 *
 *  Trois choses, chacune dans son fichier :
 *
 *  `inc/acces.php`     — une capacité à part, `soha_acceder_crm`, donnée à des
 *                        personnes nommées. Le CRM tient des coordonnées de gens
 *                        réels : y entrer ne doit pas être l'effet de bord du
 *                        droit de corriger une page.
 *
 *  `inc/registre.php`  — le registre du CRM et ses deux routes REST. L'interface
 *                        React appelle `window.storage`, un objet qu'aucun
 *                        navigateur ne fournit : ses écritures partaient dans le
 *                        vide, et un `try {} catch (e) {}` rendait la panne
 *                        muette. `assets/adaptateur.js` fournit cet objet. Le
 *                        JSX d'origine est conservé intact dans `source/`.
 *
 *  `inc/demandes.php`  — chaque envoi de formulaire est écrit en base **avant**
 *                        que le courriel parte, et peut être versé au répertoire
 *                        en un geste, sans doublon. Purge à 24 mois.
 *
 *  `inc/locations.php` — une demande de location porte déjà l'espace, la date et
 *                        le tarif que la personne avait sous les yeux. Verser la
 *                        demande crée donc aussi la réservation, en devis. Rien
 *                        n'est inventé : ce qui n'a pas été demandé reste vide.
 *
 *  `inc/sauvegarde.php`— le registre entier tient dans une option : c'est ce qui
 *                        le rend simple, et c'est un seul endroit où tout
 *                        perdre. Un fichier qu'on télécharge, qu'on remet, et un
 *                        état d'avant conservé pour défaire une fois.
 *
 *  Deux choses qu'elle ne fait pas, et c'est voulu :
 *
 *  Pas de purge du répertoire. Les 24 mois annoncés dans la politique portent
 *  sur les *demandes reçues par formulaire*, pas sur les personnes qui
 *  fréquentent le centre. Effacer d'office la fiche de quelqu'un qui vient
 *  depuis trois ans serait une faute, pas une conformité.
 *
 *  Pas de table dédiée pour le registre. Une option suffit à quelques centaines
 *  de fiches ; elle n'est jamais chargée automatiquement et sa taille est
 *  plafonnée. La table viendra quand il faudra chercher et recouper côté
 *  serveur.
 * -----------------------------------------------------------------------------
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SOHA_CRM_VERSION', '1.2.0');

/** L'option qui porte l'état du registre (jamais en autoload). */
define('SOHA_CRM_OPTION', 'soha_crm_etat');

/** Le compteur de révisions : il sert à refuser une écriture périmée. */
define('SOHA_CRM_REVISION', 'soha_crm_revision');

/** Qui a écrit en dernier, et quand — pour que le conflit ait un visage. */
define('SOHA_CRM_DERNIER', 'soha_crm_dernier');

/** 5 Mo — large pour le registre, étroit pour un accident. */
define('SOHA_CRM_TAILLE_MAX', 5 * 1024 * 1024);

require_once plugin_dir_path(__FILE__) . 'inc/acces.php';
require_once plugin_dir_path(__FILE__) . 'inc/registre.php';
require_once plugin_dir_path(__FILE__) . 'inc/locations.php';
require_once plugin_dir_path(__FILE__) . 'inc/demandes.php';
require_once plugin_dir_path(__FILE__) . 'inc/ecran-demandes.php';
require_once plugin_dir_path(__FILE__) . 'inc/sauvegarde.php';

/* -------------------------------------------------------------------------- */
/*  L'écran du CRM                                                             */
/* -------------------------------------------------------------------------- */

add_action('admin_menu', function () {
    add_menu_page(
        __('CRM — Centre Soha', 'soha-crm'),
        __('CRM Soha', 'soha-crm'),
        soha_crm_capacite(),
        'soha-crm',
        'soha_crm_ecran',
        'dashicons-groups',
        3
    );
    /* WordPress nomme le premier sous-menu comme le menu ; on le renomme pour
       que « Répertoire », « Demandes » et « Accès » se lisent côte à côte. */
    add_submenu_page('soha-crm', __('Le répertoire', 'soha-crm'), __('Répertoire', 'soha-crm'),
                     soha_crm_capacite(), 'soha-crm', 'soha_crm_ecran');
}, 5);

function soha_crm_ecran() {
    if (!current_user_can(soha_crm_capacite())) {
        wp_die(esc_html__("Tu n'as pas accès au CRM du Centre Soha.", 'soha-crm'));
    }
    /*
     * Une seule div. Tout le reste est monté par React.
     * Le message de repli n'apparaît que si le script ne se charge pas : c'est
     * le seul cas où l'écran resterait blanc, et un écran blanc n'explique rien.
     */
    echo '<div class="wrap" style="margin:0;padding:0">';
    echo '<div id="soha-crm-racine"><noscript>'
       . esc_html__('Le CRM a besoin de JavaScript pour fonctionner.', 'soha-crm')
       . '</noscript></div>';
    echo '</div>';
}

/* -------------------------------------------------------------------------- */
/*  Les fichiers                                                               */
/* -------------------------------------------------------------------------- */

add_action('admin_enqueue_scripts', function ($page) {
    if ('toplevel_page_soha-crm' !== $page) {
        return;
    }

    $base = plugin_dir_url(__FILE__);

    /* Les trois familles du canon, servies d'ici. Jamais Google : aucune
       adresse IP ne part chez un tiers (Loi 25). */
    wp_enqueue_style('soha-crm-polices', $base . 'assets/polices.css', array(), SOHA_CRM_VERSION);

    /* L'adaptateur d'abord : il doit avoir posé `window.storage` avant que
       l'interface ne cherche à lire. */
    wp_enqueue_script('soha-crm-adaptateur', $base . 'assets/adaptateur.js', array(), SOHA_CRM_VERSION, true);
    wp_localize_script('soha-crm-adaptateur', 'SOHA_CRM', array(
        'racine' => esc_url_raw(rest_url('soha-crm/v1/etat')),
        'jeton'  => wp_create_nonce('wp_rest'),
    ));

    /* `wp-element`, c'est React tel que WordPress le fournit déjà : rien à
       télécharger en plus, et une seule copie de React sur la page. */
    wp_enqueue_script('soha-crm', $base . 'assets/crm.js', array('wp-element', 'soha-crm-adaptateur'), SOHA_CRM_VERSION, true);
});

/* -------------------------------------------------------------------------- */
/*  Activation et désactivation                                                */
/* -------------------------------------------------------------------------- */

register_activation_hook(__FILE__, 'soha_crm_activer');

function soha_crm_activer() {
    /* `autoload` à `false` : le registre ne sera pas chargé à chaque page du
       site public, où il n'a rien à faire. */
    add_option(SOHA_CRM_OPTION, '', '', false);
    add_option(SOHA_CRM_REVISION, 0, '', false);

    soha_crm_poser_la_capacite();

    if (!wp_next_scheduled('soha_crm_purge')) {
        wp_schedule_event(time() + HOUR_IN_SECONDS, 'daily', 'soha_crm_purge');
    }
}

register_deactivation_hook(__FILE__, function () {
    /* On arrête la purge — mais on ne supprime rien : on ne perd pas un
       registre parce qu'on a décoché une case. L'effacement est dans
       `uninstall.php`, et il faut vraiment supprimer l'extension pour
       l'atteindre. */
    $prochaine = wp_next_scheduled('soha_crm_purge');
    if ($prochaine) {
        wp_unschedule_event($prochaine, 'soha_crm_purge');
    }
});
