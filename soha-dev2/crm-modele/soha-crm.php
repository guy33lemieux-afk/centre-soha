<?php
/**
 * Plugin Name:       Centre Soha — CRM
 * Plugin URI:        https://centresoha.com/
 * Description:       Le CRM du Centre Soha : l'interface React de Mala, adossée à la base de données de WordPress. Ajoute un écran « CRM Soha » dans l'administration et deux routes REST pour lire et écrire l'état du registre.
 * Version:           1.0.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Centre Soha
 * Text Domain:       soha-crm
 *
 * -----------------------------------------------------------------------------
 *  Ce qu'elle fait, et ce qu'elle ne fait pas
 * -----------------------------------------------------------------------------
 *
 *  L'interface React appelle `window.storage.get()` et `window.storage.set()`.
 *  Aucun navigateur ne fournit cet objet : toutes les écritures partaient dans
 *  le vide, et le `try {} catch (e) {}` de la source rendait la panne muette.
 *  Cette extension fournit cet objet (voir `assets/adaptateur.js`) et le branche
 *  sur `wp_options`. L'interface n'est pas modifiée : son JSX d'origine est
 *  conservé dans `source/`.
 *
 *  Pas de purge automatique. La règle des 24 mois annoncée dans la politique de
 *  confidentialité porte sur les *demandes reçues par formulaire*, pas sur le
 *  registre des personnes qui fréquentent le centre. Supprimer d'office la
 *  fiche d'une personne qui vient depuis trois ans serait une faute, pas une
 *  conformité. La suppression reste un geste : celui de Mala, dans l'interface.
 *
 *  Pas de table dédiée non plus. Un registre de quelques centaines de fiches
 *  tient dans une option ; une table se justifiera quand il faudra chercher,
 *  trier et recouper côté serveur — phase 2. Deux garde-fous en attendant :
 *  l'option n'est jamais chargée automatiquement (`autoload` à `false`), et sa
 *  taille est plafonnée, pour qu'un envoi aberrant soit refusé net plutôt que
 *  d'engorger la base.
 * -----------------------------------------------------------------------------
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SOHA_CRM_VERSION', '1.0.0');

/** L'option qui porte l'état du registre (jamais en autoload). */
define('SOHA_CRM_OPTION', 'soha_crm_etat');

/** Le compteur de révisions : il sert à refuser une écriture périmée. */
define('SOHA_CRM_REVISION', 'soha_crm_revision');

/** 5 Mo — large pour le registre, étroit pour un accident. */
define('SOHA_CRM_TAILLE_MAX', 5 * 1024 * 1024);

/**
 * Qui a le droit d'ouvrir le CRM.
 *
 * `edit_pages` vise l'administratrice et les éditeurs, pas les auteurs ni les
 * abonnés. Un filtre, pour que l'accès se resserre ou s'élargisse depuis le
 * thème sans toucher à cette extension.
 */
function soha_crm_capacite() {
    return apply_filters('soha_crm_capacite', 'edit_pages');
}

/* -------------------------------------------------------------------------- */
/*  L'écran                                                                    */
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
});

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
       adresse IP de visiteur ne part chez un tiers (Loi 25). */
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
/*  Les routes                                                                 */
/* -------------------------------------------------------------------------- */

add_action('rest_api_init', function () {
    $garde = function () {
        return current_user_can(soha_crm_capacite());
    };

    register_rest_route('soha-crm/v1', '/etat', array(
        array(
            'methods'             => WP_REST_Server::READABLE,
            'callback'            => 'soha_crm_lire',
            'permission_callback' => $garde,
        ),
        array(
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => 'soha_crm_ecrire',
            'permission_callback' => $garde,
        ),
    ));
});

function soha_crm_lire() {
    return new WP_REST_Response(array(
        'valeur'   => (string) get_option(SOHA_CRM_OPTION, ''),
        'revision' => (int) get_option(SOHA_CRM_REVISION, 0),
    ), 200);
}

function soha_crm_ecrire(WP_REST_Request $requete) {
    $corps = $requete->get_json_params();

    if (!is_array($corps) || !array_key_exists('valeur', $corps) || !is_string($corps['valeur'])) {
        return new WP_Error(
            'soha_crm_corps',
            __("L'envoi doit contenir « valeur », une chaîne JSON.", 'soha-crm'),
            array('status' => 400)
        );
    }

    $valeur = $corps['valeur'];

    if (strlen($valeur) > SOHA_CRM_TAILLE_MAX) {
        return new WP_Error(
            'soha_crm_taille',
            sprintf(
                /* translators: %s : la taille maximale, déjà formatée. */
                __('Le registre dépasse la taille permise (%s).', 'soha-crm'),
                size_format(SOHA_CRM_TAILLE_MAX)
            ),
            array('status' => 413)
        );
    }

    /* On n'enregistre pas un JSON qu'on ne saurait pas relire. Le CRM écrit un
       objet ; une chaîne ou un nombre signalerait un envoi malformé. */
    $decode = json_decode($valeur, true);
    if (null === $decode && 'null' !== trim($valeur)) {
        return new WP_Error(
            'soha_crm_json',
            __("Le registre envoyé n'est pas du JSON valide ; rien n'a été enregistré.", 'soha-crm'),
            array('status' => 400)
        );
    }
    if (!is_array($decode)) {
        return new WP_Error(
            'soha_crm_forme',
            __("Le registre envoyé n'a pas la forme attendue ; rien n'a été enregistré.", 'soha-crm'),
            array('status' => 400)
        );
    }

    /* Deux personnes peuvent avoir le CRM ouvert. Celle qui enregistre à partir
       d'un état périmé écraserait le travail de l'autre : on refuse, et on lui
       rend l'état courant pour qu'elle puisse se rattraper. */
    $revision = (int) get_option(SOHA_CRM_REVISION, 0);
    $envoyee  = isset($corps['revision']) ? (int) $corps['revision'] : $revision;

    if ($envoyee !== $revision) {
        return new WP_REST_Response(array(
            'code'     => 'soha_crm_revision',
            'message'  => __("Quelqu'un d'autre a enregistré depuis ton dernier chargement.", 'soha-crm'),
            'valeur'   => (string) get_option(SOHA_CRM_OPTION, ''),
            'revision' => $revision,
        ), 409);
    }

    /* Réécrire à l'identique n'est pas une erreur : `update_option` renvoie
       `false` dans ce cas comme en cas d'échec. On distingue les deux en
       relisant, plutôt que d'annoncer une panne qui n'existe pas. */
    $ecrit = update_option(SOHA_CRM_OPTION, $valeur, false);
    if (!$ecrit && (string) get_option(SOHA_CRM_OPTION, '') !== $valeur) {
        return new WP_Error(
            'soha_crm_ecriture',
            __("La base de données a refusé l'enregistrement.", 'soha-crm'),
            array('status' => 500)
        );
    }

    $revision++;
    update_option(SOHA_CRM_REVISION, $revision, false);

    return new WP_REST_Response(array(
        'revision' => $revision,
        'taille'   => strlen($valeur),
    ), 200);
}

/* -------------------------------------------------------------------------- */
/*  Activation                                                                 */
/* -------------------------------------------------------------------------- */

register_activation_hook(__FILE__, function () {
    /* `add_option` avec `autoload` à `false` : le registre ne sera pas chargé
       à chaque page du site public, où il n'a rien à faire. */
    add_option(SOHA_CRM_OPTION, '', '', false);
    add_option(SOHA_CRM_REVISION, 0, '', false);
});

/* La désactivation ne supprime rien : on ne perd pas un registre parce qu'on a
   décoché une case. La suppression se fait à la désinstallation seulement, et
   c'est `uninstall.php` qui s'en charge — volontairement séparé, pour qu'il
   faille vraiment supprimer l'extension pour perdre les données. */
