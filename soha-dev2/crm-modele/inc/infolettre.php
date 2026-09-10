<?php
/**
 * Centre Soha — CRM, phase 3 : l'infolettre, sans double saisie.
 *
 * Le consentement est coché sur le formulaire du site, ou par Mala sur une
 * fiche. À partir de là, plus personne ne recopie une adresse à la main : le
 * CRM et Mailchimp se tiennent au courant l'un l'autre.
 *
 * -----------------------------------------------------------------------------
 *  Trois choix de fond
 * -----------------------------------------------------------------------------
 *
 *  1. **Aucun script Mailchimp sur le site.** Leurs formulaires embarqués
 *     posent un traceur sur chaque page qui les affiche. Tout passe donc par
 *     le serveur : le visiteur ne parle jamais à Mailchimp, seul WordPress le
 *     fait. La promesse « zéro appel externe » du site reste vraie.
 *
 *  2. **La preuve du consentement reste au 961.** Mailchimp reçoit une adresse
 *     et un prénom, rien d'autre. La date du consentement, le formulaire qui l'a
 *     recueilli et le texte qui était affiché restent dans la base du site —
 *     c'est là qu'il faudra les retrouver si on les demande un jour, et un
 *     compte chez un tiers n'est pas un registre de preuve.
 *
 *  3. **Rien ne part en direct.** Une écriture dans le CRM ne doit pas attendre
 *     un serveur à l'autre bout du continent. Les changements entrent dans une
 *     file, une tâche planifiée les envoie, et ce qui échoue est réessayé puis
 *     dit à l'écran plutôt qu'oublié.
 * -----------------------------------------------------------------------------
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SOHA_CRM_INFO_CLE',    'soha_crm_infolettre_cle');     // la clé d'API
define('SOHA_CRM_INFO_LISTE',  'soha_crm_infolettre_liste');   // l'audience choisie
define('SOHA_CRM_INFO_DOUBLE', 'soha_crm_infolettre_double');  // double opt-in ?
define('SOHA_CRM_INFO_FILE',   'soha_crm_infolettre_file');    // la file d'attente
define('SOHA_CRM_INFO_JJ',     'soha_crm_infolettre_journal'); // le dernier passage
define('SOHA_CRM_INFO_SECRET', 'soha_crm_infolettre_secret');  // pour le retour de Mailchimp

/** Combien d'adresses par passage : assez pour avancer, assez peu pour ne pas expirer. */
define('SOHA_CRM_INFO_LOT', 25);

/** Après cinq échecs, on cesse d'insister et on le dit. */
define('SOHA_CRM_INFO_ESSAIS', 5);

/* -------------------------------------------------------------------------- */
/*  La liaison                                                                 */
/* -------------------------------------------------------------------------- */

/** La liaison est-elle en place ? */
function soha_crm_info_active() {
    return '' !== (string) get_option(SOHA_CRM_INFO_CLE, '')
        && '' !== (string) get_option(SOHA_CRM_INFO_LISTE, '');
}

/**
 * Le centre de données se lit dans la clé elle-même : `…-us21`.
 *
 * C'est ainsi que Mailchimp répartit ses comptes. Une clé sans suffixe n'est
 * pas une clé Mailchimp, et il vaut mieux le dire tout de suite que d'appeler
 * une adresse qui n'existe pas.
 */
function soha_crm_info_centre($cle) {
    $bouts = explode('-', (string) $cle);
    $dc = end($bouts);
    return preg_match('/^[a-z]{2}\d+$/', (string) $dc) ? $dc : '';
}

/**
 * Un appel à l'API de Mailchimp.
 *
 * @param string $methode GET, POST, PUT, PATCH…
 * @param string $chemin  Après `/3.0/`, sans barre oblique initiale.
 * @param array|null $corps
 * @return array|WP_Error ('statut', 'corps')
 */
function soha_crm_info_appel($methode, $chemin, $corps = null, $cle = null) {
    $cle = null === $cle ? (string) get_option(SOHA_CRM_INFO_CLE, '') : $cle;
    if ('' === $cle) {
        return new WP_Error('soha_crm_info_cle', __("Aucune clé d'API enregistrée.", 'soha-crm'));
    }
    $dc = soha_crm_info_centre($cle);
    if ('' === $dc) {
        return new WP_Error('soha_crm_info_cle', __(
            "Cette clé ne ressemble pas à une clé Mailchimp : il lui manque son centre de données (le « -us21 » à la fin).",
            'soha-crm'
        ));
    }

    $args = array(
        'method'  => $methode,
        'timeout' => 15,
        'headers' => array(
            'Authorization' => 'Basic ' . base64_encode('soha:' . $cle),
            'Content-Type'  => 'application/json',
            'Accept'        => 'application/json',
        ),
    );
    if (null !== $corps) {
        $args['body'] = wp_json_encode($corps);
    }

    $url = 'https://' . $dc . '.api.mailchimp.com/3.0/' . ltrim($chemin, '/');
    $rep = wp_remote_request($url, $args);
    if (is_wp_error($rep)) {
        return $rep;
    }

    $lu = json_decode((string) wp_remote_retrieve_body($rep), true);
    return array(
        'statut' => (int) wp_remote_retrieve_response_code($rep),
        'corps'  => is_array($lu) ? $lu : array(),
    );
}

/** Le message que Mailchimp donne quand il refuse, ou un mot à nous. */
function soha_crm_info_pourquoi($reponse) {
    if (is_wp_error($reponse)) {
        return $reponse->get_error_message();
    }
    $c = isset($reponse['corps']) ? $reponse['corps'] : array();
    if (!empty($c['detail'])) {
        return (string) $c['detail'];
    }
    if (!empty($c['title'])) {
        return (string) $c['title'];
    }
    return sprintf(
        /* translators: %d : le code de réponse HTTP. */
        __('Mailchimp a répondu %d, sans explication.', 'soha-crm'),
        isset($reponse['statut']) ? (int) $reponse['statut'] : 0
    );
}

/** Le compte au bout de la clé : sert au bouton « Tester la liaison ». */
function soha_crm_info_compte($cle = null) {
    $r = soha_crm_info_appel('GET', '', null, $cle);
    if (is_wp_error($r)) {
        return $r;
    }
    if (200 !== $r['statut']) {
        return new WP_Error('soha_crm_info', soha_crm_info_pourquoi($r));
    }
    return array(
        'compte' => isset($r['corps']['account_name']) ? (string) $r['corps']['account_name'] : '',
        'courriel' => isset($r['corps']['email']) ? (string) $r['corps']['email'] : '',
    );
}

/** Les audiences du compte, pour que Mala choisisse la bonne dans une liste. */
function soha_crm_info_audiences($cle = null) {
    $r = soha_crm_info_appel('GET', 'lists?count=50&fields=lists.id,lists.name,lists.stats.member_count', null, $cle);
    if (is_wp_error($r)) {
        return $r;
    }
    if (200 !== $r['statut']) {
        return new WP_Error('soha_crm_info', soha_crm_info_pourquoi($r));
    }
    $out = array();
    foreach ((array) (isset($r['corps']['lists']) ? $r['corps']['lists'] : array()) as $l) {
        $out[] = array(
            'id'      => isset($l['id']) ? (string) $l['id'] : '',
            'nom'     => isset($l['name']) ? (string) $l['name'] : '',
            'membres' => isset($l['stats']['member_count']) ? (int) $l['stats']['member_count'] : 0,
        );
    }
    return $out;
}

/* -------------------------------------------------------------------------- */
/*  La file                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * Le prénom et le nom, à partir du seul champ que le CRM tient.
 *
 * On coupe au premier espace. « Marie-Claude Tremblay » donne Marie-Claude et
 * Tremblay ; « Camille » donne Camille et rien. C'est imparfait et c'est assumé :
 * mieux vaut un prénom juste dans neuf cas sur dix qu'un champ vide partout.
 */
function soha_crm_info_nom($complet) {
    $complet = trim((string) $complet);
    if ('' === $complet) {
        return array('', '');
    }
    $bouts = preg_split('/\s+/u', $complet, 2);
    return array($bouts[0], isset($bouts[1]) ? $bouts[1] : '');
}

/** Ajoute ou remplace une entrée dans la file — une seule par adresse. */
function soha_crm_info_enfiler($courriel, $statut, $nom = '', $etiquettes = array()) {
    $courriel = strtolower(trim((string) $courriel));
    if (!is_email($courriel)) {
        return false;
    }
    $file = (array) get_option(SOHA_CRM_INFO_FILE, array());
    $file[$courriel] = array(
        'courriel'   => $courriel,
        'statut'     => 'desabonne' === $statut ? 'desabonne' : 'abonne',
        'nom'        => (string) $nom,
        'etiquettes' => array_values(array_filter((array) $etiquettes)),
        'essais'     => 0,
        'quand'      => time(),
        'erreur'     => '',
    );
    update_option(SOHA_CRM_INFO_FILE, $file, false);

    if (!wp_next_scheduled('soha_crm_infolettre_traiter')) {
        wp_schedule_single_event(time() + 30, 'soha_crm_infolettre_traiter');
    }
    return true;
}

/**
 * Compare deux états du registre et met en file ce qui a changé.
 *
 * C'est le seul endroit où la synchronisation se décide, et c'est voulu : que le
 * consentement vienne d'un formulaire, d'un versement ou d'une case cochée à la
 * main dans le CRM, il finit toujours par une écriture du registre. Un seul
 * point de passage, donc aucun chemin oublié.
 */
function soha_crm_info_comparer($avant, $apres) {
    if (!soha_crm_info_active()) {
        return 0;
    }

    $etat = function ($contacts) {
        $out = array();
        foreach ((array) $contacts as $c) {
            if (empty($c['courriel']) || !is_email($c['courriel'])) {
                continue;
            }
            $i = isset($c['infolettre']) && is_array($c['infolettre']) ? $c['infolettre'] : array();
            $abonne = !empty($i['abonne']) && empty($i['desabonne']);
            $out[strtolower(trim($c['courriel']))] = array(
                'abonne'     => $abonne,
                'nom'        => isset($c['nom']) ? $c['nom'] : '',
                'etiquettes' => array_values(array_filter(array(
                    isset($c['type']) ? $c['type'] : '',
                    isset($c['ecole']) ? $c['ecole'] : '',
                ))),
            );
        }
        return $out;
    };

    $a = $etat(isset($avant['contacts']) ? $avant['contacts'] : array());
    $b = $etat(isset($apres['contacts']) ? $apres['contacts'] : array());

    $n = 0;
    foreach ($b as $courriel => $neuf) {
        $vieux = isset($a[$courriel]) ? $a[$courriel] : null;
        if (null === $vieux) {
            /* Une fiche qui arrive déjà abonnée : on l'inscrit. Une fiche qui
               arrive non abonnée n'a rien à dire à Mailchimp. */
            if ($neuf['abonne']) {
                soha_crm_info_enfiler($courriel, 'abonne', $neuf['nom'], $neuf['etiquettes']);
                $n++;
            }
            continue;
        }
        if ($vieux['abonne'] !== $neuf['abonne']) {
            soha_crm_info_enfiler($courriel, $neuf['abonne'] ? 'abonne' : 'desabonne',
                                  $neuf['nom'], $neuf['etiquettes']);
            $n++;
        }
    }

    /* Une fiche supprimée du CRM n'est pas un désabonnement : la personne n'a
       rien demandé. On ne touche pas à Mailchimp — c'est à Mala de la
       désabonner d'abord si c'est ce qu'elle veut. */

    return $n;
}

/* -------------------------------------------------------------------------- */
/*  L'envoi                                                                    */
/* -------------------------------------------------------------------------- */

add_action('soha_crm_infolettre_traiter', 'soha_crm_info_vider_la_file');
add_action('soha_crm_infolettre_reprise', 'soha_crm_info_vider_la_file');

function soha_crm_info_vider_la_file() {
    if (!soha_crm_info_active()) {
        return 0;
    }
    $file = (array) get_option(SOHA_CRM_INFO_FILE, array());
    if (!$file) {
        return 0;
    }

    $faits = 0;
    $reste = $file;
    $i = 0;
    foreach ($file as $courriel => $item) {
        if (++$i > SOHA_CRM_INFO_LOT) {
            break;
        }
        $r = soha_crm_info_envoyer($item);
        if (true === $r) {
            unset($reste[$courriel]);
            $faits++;
            continue;
        }
        $reste[$courriel]['essais'] = (int) $item['essais'] + 1;
        $reste[$courriel]['erreur'] = is_wp_error($r) ? $r->get_error_message() : (string) $r;
    }

    update_option(SOHA_CRM_INFO_FILE, $reste, false);
    update_option(SOHA_CRM_INFO_JJ, array(
        'quand'  => time(),
        'faits'  => $faits,
        'reste'  => count($reste),
        'bloques' => count(array_filter($reste, function ($x) {
            return (int) $x['essais'] >= SOHA_CRM_INFO_ESSAIS;
        })),
    ), false);

    /* S'il reste du travail qui peut encore réussir, on repasse. */
    $encore = array_filter($reste, function ($x) {
        return (int) $x['essais'] < SOHA_CRM_INFO_ESSAIS;
    });
    if ($encore && !wp_next_scheduled('soha_crm_infolettre_traiter')) {
        wp_schedule_single_event(time() + 300, 'soha_crm_infolettre_traiter');
    }
    return $faits;
}

/** Une adresse, chez Mailchimp. @return true|WP_Error */
function soha_crm_info_envoyer($item) {
    if ((int) $item['essais'] >= SOHA_CRM_INFO_ESSAIS) {
        return new WP_Error('soha_crm_info_abandon', __('Abandonné après cinq essais.', 'soha-crm'));
    }

    $liste = (string) get_option(SOHA_CRM_INFO_LISTE, '');
    $hash  = md5(strtolower($item['courriel']));
    list($prenom, $nom) = soha_crm_info_nom($item['nom']);

    if ('desabonne' === $item['statut']) {
        /* On désabonne, on ne supprime pas : effacer la personne de Mailchimp
           effacerait aussi la trace de son désabonnement, et elle pourrait se
           faire réinscrire par un import. */
        $r = soha_crm_info_appel('PATCH', 'lists/' . $liste . '/members/' . $hash,
                                 array('status' => 'unsubscribed'));
        if (is_wp_error($r)) {
            return $r;
        }
        if (404 === $r['statut']) {
            return true;      // elle n'y a jamais été : c'est le résultat voulu
        }
        if ($r['statut'] < 200 || $r['statut'] >= 300) {
            return new WP_Error('soha_crm_info', soha_crm_info_pourquoi($r));
        }
        return true;
    }

    $double = (bool) get_option(SOHA_CRM_INFO_DOUBLE, false);
    $corps = array(
        'email_address'  => $item['courriel'],
        'status_if_new'  => $double ? 'pending' : 'subscribed',
        'merge_fields'   => array('FNAME' => $prenom, 'LNAME' => $nom),
    );
    /* On ne réabonne pas d'office quelqu'un qui s'est désabonné chez Mailchimp :
       `status` n'est envoyé que pour les nouvelles inscriptions, via
       `status_if_new`. Le respect d'un désabonnement passe avant notre registre. */

    $r = soha_crm_info_appel('PUT', 'lists/' . $liste . '/members/' . $hash, $corps);
    if (is_wp_error($r)) {
        return $r;
    }
    if ($r['statut'] < 200 || $r['statut'] >= 300) {
        return new WP_Error('soha_crm_info', soha_crm_info_pourquoi($r));
    }

    /* Les étiquettes : utiles pour segmenter, jamais bloquantes. */
    if (!empty($item['etiquettes'])) {
        $tags = array();
        foreach ($item['etiquettes'] as $t) {
            $tags[] = array('name' => (string) $t, 'status' => 'active');
        }
        soha_crm_info_appel('POST', 'lists/' . $liste . '/members/' . $hash . '/tags',
                            array('tags' => $tags));
    }

    return true;
}

/* -------------------------------------------------------------------------- */
/*  Le retour de Mailchimp                                                     */
/* -------------------------------------------------------------------------- */

/** Le secret qui protège l'adresse de retour ; créé au besoin. */
function soha_crm_info_secret() {
    $s = (string) get_option(SOHA_CRM_INFO_SECRET, '');
    if ('' === $s) {
        $s = wp_generate_password(32, false, false);
        update_option(SOHA_CRM_INFO_SECRET, $s, false);
    }
    return $s;
}

function soha_crm_info_adresse_retour() {
    /* On assemble à la main plutôt qu'avec `add_query_arg` : celui-ci réencode
       les paramètres déjà présents, et avec des permaliens simples l'adresse
       devient `rest_route=%2Fsoha-crm%2Fv1%2F…`. Ça fonctionne, mais Mala doit
       pouvoir reconnaître ce qu'elle colle dans Mailchimp. */
    $base = rest_url('soha-crm/v1/infolettre/retour');
    $sep  = (false === strpos($base, '?')) ? '?' : '&';
    return $base . $sep . 'cle=' . rawurlencode(soha_crm_info_secret());
}

add_action('rest_api_init', function () {
    register_rest_route('soha-crm/v1', '/infolettre/retour', array(
        /* Mailchimp valide l'adresse par un GET avant de s'en servir. */
        array(
            'methods'             => WP_REST_Server::READABLE,
            'callback'            => function () { return new WP_REST_Response(array('ok' => true), 200); },
            'permission_callback' => 'soha_crm_info_retour_permis',
        ),
        array(
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => 'soha_crm_info_retour',
            'permission_callback' => 'soha_crm_info_retour_permis',
        ),
    ));
});

/**
 * Mailchimp ne signe pas ses appels : le seul contrôle possible est un secret
 * dans l'adresse. On le compare en temps constant, et on ne dit rien de plus
 * qu'un refus — une adresse de retour n'a pas à être bavarde.
 */
function soha_crm_info_retour_permis(WP_REST_Request $r) {
    $donne = (string) $r->get_param('cle');
    return '' !== $donne && hash_equals(soha_crm_info_secret(), $donne);
}

/**
 * Quelqu'un s'est désabonné depuis un courriel : le CRM doit le savoir.
 *
 * Sans ceci, Mala verrait « abonnée » sur une fiche pendant que Mailchimp,
 * lui, ne lui écrit plus. Deux vérités pour une même personne, et c'est la
 * fiche qui aurait tort.
 */
function soha_crm_info_retour(WP_REST_Request $r) {
    $type = (string) $r->get_param('type');
    $data = (array) $r->get_param('data');
    $courriel = isset($data['email']) ? strtolower(trim((string) $data['email'])) : '';

    if ('unsubscribe' !== $type && 'cleaned' !== $type) {
        return new WP_REST_Response(array('ignore' => $type), 200);
    }
    if (!is_email($courriel)) {
        return new WP_REST_Response(array('ignore' => 'courriel'), 200);
    }

    $etat = soha_crm_registre_lire();
    $reg  = $etat['valeur'] ? json_decode($etat['valeur'], true) : null;
    if (!is_array($reg) || empty($reg['contacts'])) {
        return new WP_REST_Response(array('inconnu' => true), 200);
    }

    $touche = false;
    foreach ($reg['contacts'] as $i => $c) {
        if (empty($c['courriel']) || 0 !== strcasecmp(trim($c['courriel']), $courriel)) {
            continue;
        }
        $info = isset($c['infolettre']) && is_array($c['infolettre']) ? $c['infolettre'] : array();
        if (!empty($info['desabonne'])) {
            break;                       // déjà noté, rien à écrire
        }
        $info['desabonne'] = true;
        $info['abonne'] = false;
        $reg['contacts'][$i]['infolettre'] = $info;
        $touche = true;
        break;
    }

    if ($touche) {
        /* Sans re-synchroniser : l'information vient de Mailchimp, la lui
           renvoyer serait tourner en rond. */
        soha_crm_registre_ecrire(wp_json_encode($reg), 0, false);
    }

    return new WP_REST_Response(array('mis_a_jour' => $touche), 200);
}

/* -------------------------------------------------------------------------- */
/*  Le consentement donné sur un formulaire                                    */
/* -------------------------------------------------------------------------- */

/**
 * Une personne qui coche l'infolettre est inscrite tout de suite.
 *
 * Elle n'a pas à attendre que Mala verse sa demande au répertoire : elle a
 * coché, elle est inscrite. Faire dépendre son inscription d'un geste interne,
 * ce serait lui faire porter notre organisation.
 *
 * L'envoi est un `PUT` : quand la demande sera versée et que le contact naîtra
 * abonné, la deuxième mise en file écrasera celle-ci sans créer de doublon.
 */
add_action('soha_crm_demande_archivee', function ($id_demande, $champs) {
    if (!soha_crm_info_active()) {
        return;
    }
    if (!get_post_meta($id_demande, '_soha_consentement', true)) {
        return;
    }
    $courriel = (string) get_post_meta($id_demande, '_soha_courriel', true);
    $nom      = (string) get_post_meta($id_demande, '_soha_nom', true);
    if ('' === $courriel) {
        return;
    }
    soha_crm_info_enfiler($courriel, 'abonne', $nom, array('formulaire'));
}, 10, 2);
