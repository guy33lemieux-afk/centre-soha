<?php
/**
 * Centre Soha — CRM : le registre et ses deux routes.
 *
 * Le registre est l'état complet du CRM, tel que l'interface React l'écrit :
 * une chaîne JSON. Il vit dans une option, jamais chargée automatiquement.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** Le registre tel qu'il est en base, et le numéro de sa dernière écriture. */
function soha_crm_registre_lire() {
    return array(
        'valeur'   => (string) get_option(SOHA_CRM_OPTION, ''),
        'revision' => (int) get_option(SOHA_CRM_REVISION, 0),
    );
}

/**
 * Écrit le registre et avance la révision.
 *
 * Renvoie la nouvelle révision, ou un `WP_Error` si la base a refusé. Le cas
 * « rien n'a changé » n'est pas une erreur : `update_option` renvoie `false`
 * aussi bien pour une écriture identique que pour un échec, alors on relit.
 */
function soha_crm_registre_ecrire($valeur, $qui = 0) {
    $ecrit = update_option(SOHA_CRM_OPTION, $valeur, false);
    if (!$ecrit && (string) get_option(SOHA_CRM_OPTION, '') !== $valeur) {
        return new WP_Error('soha_crm_ecriture', __("La base de données a refusé l'enregistrement.", 'soha-crm'));
    }

    $revision = (int) get_option(SOHA_CRM_REVISION, 0) + 1;
    update_option(SOHA_CRM_REVISION, $revision, false);
    update_option(SOHA_CRM_DERNIER, array(
        'qui'   => $qui ? (int) $qui : get_current_user_id(),
        'quand' => time(),
    ), false);

    return $revision;
}

/** Qui a écrit en dernier, et quand — pour que le conflit ait un visage. */
function soha_crm_dernier_auteur() {
    $d = get_option(SOHA_CRM_DERNIER, array());
    if (empty($d['qui'])) {
        return array('nom' => '', 'quand' => 0);
    }
    $user = get_userdata((int) $d['qui']);
    return array(
        'nom'   => $user ? $user->display_name : '',
        'quand' => isset($d['quand']) ? (int) $d['quand'] : 0,
    );
}

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
            'callback'            => 'soha_crm_route_lire',
            'permission_callback' => $garde,
        ),
        array(
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => 'soha_crm_route_ecrire',
            'permission_callback' => $garde,
        ),
    ));
});

function soha_crm_route_lire() {
    return new WP_REST_Response(soha_crm_registre_lire(), 200);
}

function soha_crm_route_ecrire(WP_REST_Request $requete) {
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

    /* On n'enregistre pas un JSON qu'on ne saurait pas relire. */
    $decode = json_decode($valeur, true);
    if (!is_array($decode)) {
        return new WP_Error(
            'soha_crm_json',
            __("Le registre envoyé n'est pas lisible ; rien n'a été enregistré.", 'soha-crm'),
            array('status' => 400)
        );
    }

    /* Ils sont quatre à pouvoir ouvrir le CRM. Celui ou celle qui enregistre à
       partir d'un état périmé écraserait le travail d'un autre : on refuse, on
       dit qui a écrit, et on rend l'état courant. */
    $etat     = soha_crm_registre_lire();
    $revision = $etat['revision'];
    $envoyee  = isset($corps['revision']) ? (int) $corps['revision'] : $revision;

    if ($envoyee !== $revision) {
        $dernier = soha_crm_dernier_auteur();
        return new WP_REST_Response(array(
            'code'     => 'soha_crm_revision',
            'message'  => $dernier['nom']
                ? sprintf(
                    /* translators: %s : le nom de la personne. */
                    __('%s a enregistré depuis ton dernier chargement.', 'soha-crm'),
                    $dernier['nom']
                )
                : __("Quelqu'un d'autre a enregistré depuis ton dernier chargement.", 'soha-crm'),
            'qui'      => $dernier['nom'],
            'valeur'   => $etat['valeur'],
            'revision' => $revision,
        ), 409);
    }

    $nouvelle = soha_crm_registre_ecrire($valeur);
    if (is_wp_error($nouvelle)) {
        return new WP_Error(
            $nouvelle->get_error_code(),
            $nouvelle->get_error_message(),
            array('status' => 500)
        );
    }

    return new WP_REST_Response(array(
        'revision' => $nouvelle,
        'taille'   => strlen($valeur),
    ), 200);
}
