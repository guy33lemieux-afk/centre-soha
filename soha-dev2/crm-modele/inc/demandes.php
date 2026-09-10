<?php
/**
 * Centre Soha — CRM, phase 1 : ne plus rien perdre.
 *
 * Aujourd'hui, une demande de location arrive par courriel et n'existe nulle
 * part ailleurs. Si le courriel se perd, se classe mal, ou part dans une boîte
 * que personne ne regarde — ce qui est arrivé pendant des mois, faute de
 * destinataire défini — la demande n'a jamais eu lieu.
 *
 * Ici, chaque envoi de formulaire est écrit dans la base **avant** que le
 * courriel parte. Le courriel devient l'avis ; la base devient la mémoire.
 *
 * Ce qui n'est pas gardé, et volontairement : ni adresse IP, ni empreinte de
 * navigateur. On garde ce que la personne a écrit, rien de ce qu'elle n'a pas
 * choisi de dire.
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SOHA_CRM_DEMANDE', 'soha_demande');

/**
 * Le type de contenu qui porte les demandes.
 *
 * Ni public, ni interrogeable, ni dans les résultats de recherche : il n'existe
 * que pour l'écran du CRM. Le statut reste `publish` — un statut privé
 * imposerait des vérifications de droits en cascade alors que l'étanchéité est
 * déjà assurée par le fait que le type n'est exposé nulle part.
 */
add_action('init', function () {
    register_post_type(SOHA_CRM_DEMANDE, array(
        'labels'              => array(
            'name'          => __('Demandes', 'soha-crm'),
            'singular_name' => __('Demande', 'soha-crm'),
        ),
        'public'              => false,
        'publicly_queryable'  => false,
        'exclude_from_search' => true,
        'show_ui'             => false,
        'show_in_rest'        => false,
        'has_archive'         => false,
        'rewrite'             => false,
        'query_var'           => false,
        'supports'            => array('title'),
        'capability_type'     => 'soha_demande',
        'map_meta_cap'        => false,
        'capabilities'        => array(
            'edit_post'          => 'soha_acceder_crm',
            'read_post'          => 'soha_acceder_crm',
            'delete_post'        => 'soha_acceder_crm',
            'edit_posts'         => 'soha_acceder_crm',
            'edit_others_posts'  => 'soha_acceder_crm',
            'publish_posts'      => 'soha_acceder_crm',
            'read_private_posts' => 'soha_acceder_crm',
        ),
    ));
});

/* -------------------------------------------------------------------------- */
/*  La capture                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Elementor Pro, à chaque envoi de formulaire.
 *
 * Priorité 5 : avant les actions d'envoi de courriel, pour que la demande soit
 * en base même si le relais SMTP tombe. Si Elementor n'est pas là, rien ne se
 * produit — l'extension ne dépend pas de lui pour le reste.
 */
add_action('elementor_pro/forms/new_record', 'soha_crm_capter_la_demande', 5, 2);

function soha_crm_capter_la_demande($record, $handler) {
    if (!is_object($record) || !method_exists($record, 'get')) {
        return;
    }

    $reglages = $record->get('form_settings');
    $nom_form = is_array($reglages) && !empty($reglages['form_name'])
        ? $reglages['form_name']
        : __('Formulaire', 'soha-crm');

    $bruts  = (array) $record->get('fields');
    $champs = array();
    foreach ($bruts as $id => $champ) {
        $valeur = isset($champ['value']) ? $champ['value'] : '';
        if (is_array($valeur)) {
            $valeur = implode(', ', $valeur);
        }
        if ('' === trim((string) $valeur)) {
            continue;                     // un champ vide n'apprend rien
        }
        $champs[] = array(
            'id'        => (string) $id,
            'etiquette' => isset($champ['title']) && '' !== $champ['title']
                ? (string) $champ['title']
                : (string) $id,
            'type'      => isset($champ['type']) ? (string) $champ['type'] : 'text',
            'valeur'    => (string) $valeur,
        );
    }

    if (!$champs) {
        return;
    }

    $trouve    = soha_crm_reperer($champs);
    $titre     = $trouve['nom'] ? $trouve['nom'] : ($trouve['courriel'] ? $trouve['courriel'] : __('Sans nom', 'soha-crm'));
    $id_poste  = wp_insert_post(array(
        'post_type'   => SOHA_CRM_DEMANDE,
        'post_status' => 'publish',
        'post_title'  => sprintf('%s — %s', $nom_form, $titre),
        'post_author' => 0,
    ), true);

    if (is_wp_error($id_poste)) {
        return;
    }

    update_post_meta($id_poste, '_soha_formulaire', sanitize_text_field($nom_form));
    update_post_meta($id_poste, '_soha_champs', $champs);
    update_post_meta($id_poste, '_soha_nom', sanitize_text_field($trouve['nom']));
    update_post_meta($id_poste, '_soha_courriel', sanitize_email($trouve['courriel']));
    update_post_meta($id_poste, '_soha_telephone', sanitize_text_field($trouve['telephone']));
    update_post_meta($id_poste, '_soha_consentement', $trouve['consentement'] ? 1 : 0);
    update_post_meta($id_poste, '_soha_traitee', 0);

    /* À partir d'ici, le courriel d'avis part. S'il échoue, on saura à quelle
       demande l'attribuer. */
    $GLOBALS['soha_crm_demande_en_cours'] = $id_poste;

    /**
     * Après l'archivage d'une demande.
     *
     * @param int   $id_poste L'identifiant de la demande archivée.
     * @param array $champs   Les champs, tels qu'envoyés.
     */
    do_action('soha_crm_demande_archivee', $id_poste, $champs);
}

/**
 * Retrouve le nom, le courriel, le téléphone et le consentement dans les champs.
 *
 * Les formulaires du site ne nomment pas leurs champs de la même façon — d'un
 * côté `nom`, de l'autre `field_a1b2`. On regarde donc le type Elementor
 * d'abord, qui est fiable, et l'étiquette ensuite.
 */
function soha_crm_reperer($champs) {
    $trouve = array('nom' => '', 'courriel' => '', 'telephone' => '', 'consentement' => false);

    foreach ($champs as $c) {
        $etiquette = function_exists('mb_strtolower')
            ? mb_strtolower($c['etiquette'], 'UTF-8')
            : strtolower($c['etiquette']);
        $type = $c['type'];

        if (!$trouve['courriel'] && ('email' === $type || is_email($c['valeur']))) {
            $trouve['courriel'] = $c['valeur'];
            continue;
        }
        if (!$trouve['telephone'] && ('tel' === $type || false !== strpos($etiquette, 'téléphone') || false !== strpos($etiquette, 'telephone'))) {
            $trouve['telephone'] = $c['valeur'];
            continue;
        }
        if (!$trouve['nom'] && (false !== strpos($etiquette, 'nom') || false !== strpos($etiquette, 'prénom') || false !== strpos($etiquette, 'prenom'))) {
            $trouve['nom'] = $c['valeur'];
            continue;
        }
        if ('acceptance' === $type || 'checkbox' === $type) {
            if (false !== strpos($etiquette, 'infolettre') || false !== strpos($etiquette, 'consens')) {
                $trouve['consentement'] = true;
            }
        }
    }

    return $trouve;
}

/* -------------------------------------------------------------------------- */
/*  La purge des 24 mois                                                       */
/* -------------------------------------------------------------------------- */

/**
 * Celle-ci est légitime, contrairement à une purge du répertoire : la politique
 * de confidentialité annonce que les **demandes reçues par formulaire** sont
 * conservées 24 mois. Une demande versée au répertoire a laissé une fiche
 * contact ; c'est la fiche qui reste, pas la demande.
 */
add_action('soha_crm_purge', 'soha_crm_purger');

function soha_crm_purger() {
    $mois  = (int) apply_filters('soha_crm_conservation_mois', 24);
    $seuil = gmdate('Y-m-d H:i:s', strtotime('-' . $mois . ' months', current_time('timestamp', true)));

    $vieilles = get_posts(array(
        'post_type'      => SOHA_CRM_DEMANDE,
        'post_status'    => 'any',
        'posts_per_page' => 200,
        'fields'         => 'ids',
        'date_query'     => array(array('before' => $seuil, 'column' => 'post_date_gmt')),
        'no_found_rows'  => true,
    ));

    foreach ($vieilles as $id) {
        wp_delete_post($id, true);        // sans corbeille : effacer veut dire effacer
    }

    update_option('soha_crm_derniere_purge', array(
        'quand'    => time(),
        'effacees' => count($vieilles),
        'mois'     => $mois,
    ), false);

    return count($vieilles);
}

/* -------------------------------------------------------------------------- */
/*  Verser une demande au répertoire                                           */
/* -------------------------------------------------------------------------- */

/**
 * Transforme une demande en fiche contact — et, si c'est une location, en
 * réservation — dans le registre du CRM.
 *
 * Si le courriel est déjà connu, on n'ajoute pas une deuxième fiche : on inscrit
 * un échange dans celle qui existe. C'est exactement le doublon qui a coûté
 * cher ailleurs sur ce site ; on ne le refait pas ici.
 *
 * Le tout est écrit en une seule fois : contact et réservation partagent la même
 * écriture, donc soit les deux arrivent, soit ni l'un ni l'autre. Une fiche sans
 * sa réservation serait pire que rien — on la croirait traitée.
 *
 * @return array|WP_Error ('cree'|'fusionnee', nom du contact, résumé éventuel
 *                        de la réservation)
 */
function soha_crm_verser_au_repertoire($id_demande) {
    $demande = get_post($id_demande);
    if (!$demande || SOHA_CRM_DEMANDE !== $demande->post_type) {
        return new WP_Error('soha_crm_demande', __('Demande introuvable.', 'soha-crm'));
    }
    if (get_post_meta($id_demande, '_soha_versee', true)) {
        return new WP_Error('soha_crm_deja', __('Cette demande est déjà au répertoire.', 'soha-crm'));
    }

    $etat = soha_crm_registre_lire();
    $reg  = $etat['valeur'] ? json_decode($etat['valeur'], true) : null;
    if (!is_array($reg)) {
        $reg = array('contacts' => array(), 'reservations' => array(), 'ateliers' => array(), 'v' => 2);
    }
    foreach (array('contacts', 'reservations', 'ateliers') as $col) {
        if (!isset($reg[$col]) || !is_array($reg[$col])) {
            $reg[$col] = array();
        }
    }

    $nom      = (string) get_post_meta($id_demande, '_soha_nom', true);
    $courriel = (string) get_post_meta($id_demande, '_soha_courriel', true);
    $tel      = (string) get_post_meta($id_demande, '_soha_telephone', true);
    $form     = (string) get_post_meta($id_demande, '_soha_formulaire', true);
    $consent  = (bool) get_post_meta($id_demande, '_soha_consentement', true);
    $jour     = get_the_date('Y-m-d', $demande);

    $echange = array(
        'id'    => wp_generate_uuid4(),
        'date'  => $jour,
        'texte' => sprintf(
            /* translators: 1 : nom du formulaire, 2 : résumé des champs. */
            __('Demande par « %1$s » : %2$s', 'soha-crm'),
            $form,
            soha_crm_resumer($id_demande)
        ),
    );

    /* Le courriel fait foi ; sans courriel, le nom exact. */
    $indice = -1;
    foreach ($reg['contacts'] as $i => $c) {
        $meme_courriel = $courriel && !empty($c['courriel'])
            && 0 === strcasecmp(trim($c['courriel']), trim($courriel));
        $meme_nom = !$courriel && $nom && !empty($c['nom'])
            && 0 === strcasecmp(trim($c['nom']), trim($nom));
        if ($meme_courriel || $meme_nom) {
            $indice = $i;
            break;
        }
    }

    if ($indice >= 0) {
        $contact = $reg['contacts'][$indice];
        if (empty($contact['telephone']) && $tel) {
            $contact['telephone'] = $tel;
        }
        if (empty($contact['interactions']) || !is_array($contact['interactions'])) {
            $contact['interactions'] = array();
        }
        array_unshift($contact['interactions'], $echange);
        $reg['contacts'][$indice] = $contact;
        $geste = 'fusionnee';
        $qui   = isset($contact['nom']) ? $contact['nom'] : $nom;
    } else {
        $contact = array(
            'id'           => wp_generate_uuid4(),
            'nom'          => $nom ? $nom : ($courriel ? $courriel : __('Sans nom', 'soha-crm')),
            'type'         => 'prospect',
            'ecole'        => '',
            'courriel'     => $courriel,
            'telephone'    => $tel,
            'statut'       => 'Nouveau',
            'etiquettes'   => array(),
            'note'         => sprintf(
                /* translators: 1 : nom du formulaire, 2 : la date. */
                __('Arrivé·e par le formulaire « %1$s », le %2$s.', 'soha-crm'),
                $form,
                $jour
            ),
            'interactions' => array($echange),
            'ajoute'       => $jour,
            'infolettre'   => array(
                'abonne'       => $consent,
                'consentement' => $consent ? $jour : '',
                'source'       => $consent ? 'formulaire' : '',
                'desabonne'    => false,
            ),
        );
        array_unshift($reg['contacts'], $contact);
        $geste = 'cree';
        $qui   = $contact['nom'];
    }

    /* Phase 2 : si la demande parle d'un espace, elle porte aussi une
       réservation. On la crée en devis, rattachée à la fiche. */
    $champs = (array) get_post_meta($id_demande, '_soha_champs', true);
    $resume_resa = '';
    $reservation = soha_crm_reservation_depuis(
        $champs,
        $indice >= 0 ? $reg['contacts'][$indice]['id'] : $contact['id'],
        $jour
    );
    if ($reservation) {
        array_unshift($reg['reservations'], $reservation);
        $resume_resa = soha_crm_resumer_reservation($reservation);
    }

    $ecrit = soha_crm_registre_ecrire(wp_json_encode($reg));
    if (is_wp_error($ecrit)) {
        return $ecrit;
    }

    update_post_meta($id_demande, '_soha_versee', $jour);
    update_post_meta($id_demande, '_soha_traitee', 1);
    if ($resume_resa) {
        update_post_meta($id_demande, '_soha_reservation', $resume_resa);
    }

    return array('geste' => $geste, 'nom' => $qui, 'reservation' => $resume_resa);
}

/** Un résumé court d'une demande, pour l'inscrire dans l'historique du contact. */
function soha_crm_resumer($id_demande, $limite = 220) {
    $champs = (array) get_post_meta($id_demande, '_soha_champs', true);
    $bouts  = array();
    foreach ($champs as $c) {
        if (empty($c['etiquette']) || empty($c['valeur'])) {
            continue;
        }
        if (in_array($c['type'], array('acceptance', 'recaptcha', 'recaptcha_v3', 'honeypot'), true)) {
            continue;
        }
        $bouts[] = $c['etiquette'] . ' : ' . $c['valeur'];
    }
    $texte = implode(' · ', $bouts);
    if (function_exists('mb_strlen') && mb_strlen($texte, 'UTF-8') > $limite) {
        return mb_substr($texte, 0, $limite - 1, 'UTF-8') . '…';
    }
    return $texte;
}

/* -------------------------------------------------------------------------- */
/*  Quand le courriel d'avis ne part pas                                       */
/* -------------------------------------------------------------------------- */

/**
 * Archiver la demande était la moitié du travail.
 *
 * L'autre moitié : savoir que l'avis n'est pas arrivé. Un courriel qui échoue
 * ne laisse aucune trace visible — WordPress lève un signal, personne ne
 * l'écoute, et la demande dort dans la base pendant qu'on croit n'avoir rien
 * reçu. C'est exactement la panne d'origine, déplacée d'un cran.
 *
 * Vérifié le 10 septembre 2026 : aucun service d'envoi n'est configuré sur le
 * site, les courriels partent par la fonction d'envoi de PHP. C'est précisément
 * la situation où un échec silencieux est le plus probable.
 */
add_action('wp_mail_failed', 'soha_crm_courriel_rate');

function soha_crm_courriel_rate($erreur) {
    $message = is_wp_error($erreur) ? $erreur->get_error_message() : '';
    if ('' === $message) {
        $message = __('Cause inconnue.', 'soha-crm');
    }

    /* Si l'échec survient pendant qu'on traite une demande, on l'attribue à
       cette demande : c'est la ligne que Mala doit rappeler à la main. */
    $id = isset($GLOBALS['soha_crm_demande_en_cours'])
        ? (int) $GLOBALS['soha_crm_demande_en_cours'] : 0;
    if ($id && get_post($id)) {
        update_post_meta($id, '_soha_courriel_rate', sanitize_text_field($message));
    }

    $journal = (array) get_option(SOHA_CRM_COURRIELS, array());
    $journal['combien'] = (isset($journal['combien']) ? (int) $journal['combien'] : 0) + 1;
    $journal['quand']   = time();
    $journal['dernier'] = sanitize_text_field($message);
    update_option(SOHA_CRM_COURRIELS, $journal, false);
}

/** Combien d'avis ne sont pas partis depuis la dernière remise à zéro. */
function soha_crm_courriels_rates() {
    $j = (array) get_option(SOHA_CRM_COURRIELS, array());
    return array(
        'combien' => isset($j['combien']) ? (int) $j['combien'] : 0,
        'quand'   => isset($j['quand']) ? (int) $j['quand'] : 0,
        'dernier' => isset($j['dernier']) ? (string) $j['dernier'] : '',
    );
}
