<?php
/**
 * Centre Soha — CRM : l'écran des demandes.
 *
 * Volontairement sans React et sans style de marque : c'est un écran de travail
 * dans l'administration de WordPress, et il vaut mieux qu'il ressemble au reste
 * de l'administration qu'à une deuxième application. Le CRM, lui, a sa peau.
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('admin_menu', function () {
    add_submenu_page(
        'soha-crm',
        __('Demandes reçues', 'soha-crm'),
        __('Demandes', 'soha-crm'),
        soha_crm_capacite(),
        'soha-crm-demandes',
        'soha_crm_ecran_demandes'
    );
}, 10);

/** Combien de demandes attendent — le pastille rouge du menu. */
function soha_crm_compter_non_traitees() {
    $q = new WP_Query(array(
        'post_type'      => SOHA_CRM_DEMANDE,
        'post_status'    => 'publish',
        'posts_per_page' => 1,
        'fields'         => 'ids',
        'meta_query'     => array(array('key' => '_soha_traitee', 'value' => '0')),
    ));
    return (int) $q->found_posts;
}

function soha_crm_ecran_demandes() {
    if (!current_user_can(soha_crm_capacite())) {
        wp_die(esc_html__("Tu n'as pas accès aux demandes du Centre Soha.", 'soha-crm'));
    }

    $avis = soha_crm_traiter_le_geste();

    $filtre = isset($_GET['etat']) && 'toutes' === $_GET['etat'] ? 'toutes' : 'attente';
    $page   = max(1, isset($_GET['paged']) ? absint($_GET['paged']) : 1);

    $args = array(
        'post_type'      => SOHA_CRM_DEMANDE,
        'post_status'    => 'publish',
        'posts_per_page' => 25,
        'paged'          => $page,
        'orderby'        => 'date',
        'order'          => 'DESC',
    );
    if ('attente' === $filtre) {
        $args['meta_query'] = array(array('key' => '_soha_traitee', 'value' => '0'));
    }
    $q = new WP_Query($args);

    $purge = get_option('soha_crm_derniere_purge', array());
    ?>
    <div class="wrap">
        <h1><?php esc_html_e('Demandes reçues', 'soha-crm'); ?></h1>

        <?php if ($avis) : ?>
            <div class="notice notice-<?php echo esc_attr($avis['genre']); ?> is-dismissible">
                <p><?php echo esc_html($avis['texte']); ?></p>
            </div>
        <?php endif; ?>

        <?php $rates = soha_crm_courriels_rates();
        if ($rates['combien']) : ?>
            <div class="notice notice-warning">
                <p><strong><?php printf(
                    /* translators: %d : nombre d'avis non partis. */
                    esc_html(_n('%d avis par courriel n\'a pas pu partir.',
                                '%d avis par courriel ne sont pas partis.',
                                $rates['combien'], 'soha-crm')),
                    (int) $rates['combien']
                ); ?></strong>
                <?php esc_html_e(
                    "Les demandes sont ici quand même — c'est précisément à ça que sert cet écran. Mais personne n'a été prévenu : relis la liste ci-dessous, les lignes marquées d'un point rouge sont celles-là.",
                    'soha-crm'
                ); ?></p>
                <p><em><?php printf(
                    /* translators: 1 : date, 2 : message d'erreur. */
                    esc_html__('Dernier échec le %1$s : %2$s', 'soha-crm'),
                    esc_html(date_i18n(get_option('date_format') . ' à ' . get_option('time_format'), $rates['quand'])),
                    esc_html($rates['dernier'])
                ); ?></em></p>
                <form method="post" style="margin-bottom:10px">
                    <?php wp_nonce_field('soha_crm_courriels', 'soha_crm_courriels_jeton'); ?>
                    <button class="button button-small" name="geste_courriels" value="oublier">
                        <?php esc_html_e("C'est réglé, remets le compteur à zéro", 'soha-crm'); ?></button>
                </form>
            </div>
        <?php endif; ?>

        <?php $retenues = isset($purge['retenues']) ? (array) $purge['retenues'] : array();
        if ($retenues) : ?>
            <div class="notice notice-info">
                <p><strong><?php printf(
                    /* translators: %d : nombre de demandes retenues par la purge. */
                    esc_html(_n('%d demande de plus de 24 mois n\'a pas été effacée.',
                                '%d demandes de plus de 24 mois n\'ont pas été effacées.',
                                count($retenues), 'soha-crm')),
                    count($retenues)
                ); ?></strong>
                <?php esc_html_e(
                    "Chacune porte un consentement à l'infolettre dont le répertoire ne garde aucune trace : c'est donc la seule preuve qu'on ait du droit de continuer à écrire à cette personne. L'effacer serait envoyer des courriels sans pouvoir dire pourquoi.",
                    'soha-crm'
                ); ?></p>
                <p><?php esc_html_e(
                    "Pour la libérer, un des deux gestes : la verser au répertoire — la fiche gardera la date du consentement — ou désabonner la personne. Au passage suivant, la demande s'effacera d'elle-même.",
                    'soha-crm'
                ); ?></p>
                <p><?php foreach ($retenues as $id_r) :
                    $t = get_the_title($id_r);
                    if ('' === $t) { continue; } ?>
                    <span class="dashicons dashicons-email-alt" style="color:#19A7DB"></span>
                    <?php echo esc_html($t); ?>
                    <em style="opacity:.7"><?php echo esc_html(get_the_date(get_option('date_format'), $id_r)); ?></em><br>
                <?php endforeach; ?></p>
                <p><a href="<?php echo esc_url(add_query_arg(
                    array('page' => 'soha-crm-demandes', 'etat' => 'toutes'),
                    admin_url('admin.php')
                )); ?>"><?php esc_html_e('Voir toutes les demandes, les plus anciennes comprises', 'soha-crm'); ?></a></p>
            </div>
        <?php endif; ?>

        <p style="max-width:74ch">
            <?php esc_html_e(
                "Chaque envoi de formulaire du site est écrit ici avant que le courriel ne parte. Si un courriel se perd, la demande, elle, est restée.",
                'soha-crm'
            ); ?>
            <?php
            $mois = (int) apply_filters('soha_crm_conservation_mois', 24);
            printf(
                /* translators: %d : nombre de mois de conservation. */
                esc_html__('Conservation : %d mois, puis effacement automatique.', 'soha-crm'),
                (int) $mois
            );
            if (!empty($purge['quand'])) {
                echo ' <em style="color:#646970">';
                printf(
                    /* translators: 1 : date, 2 : nombre de demandes effacées. */
                    esc_html__('Dernier passage le %1$s : %2$d effacée(s).', 'soha-crm'),
                    esc_html(date_i18n(get_option('date_format'), (int) $purge['quand'])),
                    (int) (isset($purge['effacees']) ? $purge['effacees'] : 0)
                );
                echo '</em>';
            }
            ?>
        </p>

        <ul class="subsubsub">
            <li><a href="<?php echo esc_url(add_query_arg(array('page' => 'soha-crm-demandes', 'etat' => 'attente'), admin_url('admin.php'))); ?>"
                   class="<?php echo 'attente' === $filtre ? 'current' : ''; ?>">
                <?php esc_html_e('En attente', 'soha-crm'); ?>
                <span class="count">(<?php echo (int) soha_crm_compter_non_traitees(); ?>)</span></a> |</li>
            <li><a href="<?php echo esc_url(add_query_arg(array('page' => 'soha-crm-demandes', 'etat' => 'toutes'), admin_url('admin.php'))); ?>"
                   class="<?php echo 'toutes' === $filtre ? 'current' : ''; ?>">
                <?php esc_html_e('Toutes', 'soha-crm'); ?></a></li>
        </ul>

        <p style="clear:both;padding-top:8px">
            <a class="button" href="<?php echo esc_url(wp_nonce_url(
                add_query_arg(array('action' => 'soha_crm_export'), admin_url('admin-post.php')),
                'soha_crm_export'
            )); ?>"><?php esc_html_e('Exporter tout en CSV', 'soha-crm'); ?></a>
        </p>

        <?php if (!$q->have_posts()) : ?>
            <p><em><?php echo 'attente' === $filtre
                ? esc_html__('Rien en attente. Tout a été traité.', 'soha-crm')
                : esc_html__("Aucune demande pour l'instant. Les prochains envois de formulaire apparaîtront ici.", 'soha-crm'); ?></em></p>
        <?php else : ?>
            <table class="widefat striped">
                <thead>
                    <tr>
                        <th style="width:130px"><?php esc_html_e('Reçue', 'soha-crm'); ?></th>
                        <th style="width:180px"><?php esc_html_e('Formulaire', 'soha-crm'); ?></th>
                        <th><?php esc_html_e('Personne', 'soha-crm'); ?></th>
                        <th style="width:300px"><?php esc_html_e('Ce qui a été demandé', 'soha-crm'); ?></th>
                        <th style="width:260px"><?php esc_html_e('Suite', 'soha-crm'); ?></th>
                    </tr>
                </thead>
                <tbody>
                <?php while ($q->have_posts()) : $q->the_post();
                    $id       = get_the_ID();
                    $traitee  = (int) get_post_meta($id, '_soha_traitee', true);
                    $versee   = (string) get_post_meta($id, '_soha_versee', true);
                    $courriel = (string) get_post_meta($id, '_soha_courriel', true);
                    $tel      = (string) get_post_meta($id, '_soha_telephone', true);
                    $nom      = (string) get_post_meta($id, '_soha_nom', true);
                    ?>
                    <tr>
                        <td><?php echo esc_html(get_the_date('j M Y')); ?><br>
                            <span style="color:#646970"><?php echo esc_html(get_the_date('H:i')); ?></span>
                            <?php $rate = (string) get_post_meta($id, '_soha_courriel_rate', true);
                            if ($rate) : ?>
                                <br><span style="color:#d63638" title="<?php echo esc_attr($rate); ?>">
                                    ● <?php esc_html_e('avis non parti', 'soha-crm'); ?></span>
                            <?php endif; ?></td>
                        <td><?php echo esc_html(get_post_meta($id, '_soha_formulaire', true)); ?></td>
                        <td>
                            <strong><?php echo esc_html($nom ? $nom : '—'); ?></strong><br>
                            <?php if ($courriel) : ?>
                                <a href="mailto:<?php echo esc_attr($courriel); ?>"><?php echo esc_html($courriel); ?></a><br>
                            <?php endif; ?>
                            <?php if ($tel) : ?><span style="color:#646970"><?php echo esc_html($tel); ?></span><?php endif; ?>
                        </td>
                        <td>
                            <details>
                                <summary style="cursor:pointer"><?php echo esc_html(soha_crm_resumer($id, 90)); ?></summary>
                                <table style="margin-top:8px">
                                    <?php foreach (soha_crm_champs_de($id) as $c) : ?>
                                        <tr>
                                            <th style="text-align:left;padding:2px 12px 2px 0;vertical-align:top;font-weight:600">
                                                <?php echo esc_html($c['etiquette']); ?></th>
                                            <td style="padding:2px 0"><?php echo nl2br(esc_html($c['valeur'])); ?></td>
                                        </tr>
                                    <?php endforeach; ?>
                                </table>
                            </details>
                        </td>
                        <td>
                            <?php if ($versee) :
                                $resa = (string) get_post_meta($id, '_soha_reservation', true); ?>
                                <span style="color:#2c7a3f">✓ <?php esc_html_e('au répertoire', 'soha-crm'); ?></span><br>
                                <?php if ($resa) : ?>
                                    <span style="color:#2c7a3f">✓ <?php
                                        printf(
                                            /* translators: %s : espace, date et prix. */
                                            esc_html__('réservation en devis · %s', 'soha-crm'),
                                            esc_html($resa)
                                        ); ?></span><br>
                                <?php endif; ?>
                            <?php endif; ?>
                            <form method="post" style="display:inline">
                                <?php wp_nonce_field('soha_crm_demande_' . $id, 'soha_crm_jeton'); ?>
                                <input type="hidden" name="demande" value="<?php echo esc_attr($id); ?>">
                                <?php if (!$versee) : ?>
                                    <button class="button button-primary button-small" name="geste" value="verser">
                                        <?php esc_html_e('Verser au répertoire', 'soha-crm'); ?></button>
                                <?php endif; ?>
                                <?php if (!$traitee) : ?>
                                    <button class="button button-small" name="geste" value="traiter">
                                        <?php esc_html_e('Marquer traitée', 'soha-crm'); ?></button>
                                <?php else : ?>
                                    <button class="button button-small" name="geste" value="rouvrir">
                                        <?php esc_html_e('Rouvrir', 'soha-crm'); ?></button>
                                <?php endif; ?>
                                <button class="button button-small button-link-delete" name="geste" value="supprimer"
                                        onclick="return confirm('<?php echo esc_js(__('Supprimer cette demande ? Elle ne sera pas récupérable.', 'soha-crm')); ?>')">
                                    <?php esc_html_e('Supprimer', 'soha-crm'); ?></button>
                            </form>
                        </td>
                    </tr>
                <?php endwhile; wp_reset_postdata(); ?>
                </tbody>
            </table>

            <?php if ($q->max_num_pages > 1) : ?>
                <div class="tablenav"><div class="tablenav-pages"><?php
                    echo wp_kses_post(paginate_links(array(
                        'base'    => add_query_arg('paged', '%#%'),
                        'format'  => '',
                        'current' => $page,
                        'total'   => $q->max_num_pages,
                    )));
                ?></div></div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
    <?php
}

/** Le geste demandé par le formulaire de la ligne, s'il y en a un. */
function soha_crm_traiter_le_geste() {
    if (!empty($_POST['geste_courriels'])) {
        check_admin_referer('soha_crm_courriels', 'soha_crm_courriels_jeton');
        if (!current_user_can(soha_crm_capacite())) {
            return array('genre' => 'error', 'texte' => __('Droits insuffisants.', 'soha-crm'));
        }
        delete_option(SOHA_CRM_COURRIELS);
        return array('genre' => 'success', 'texte' => __(
            "Compteur remis à zéro. Il remontera au prochain courriel qui n'arrive pas à partir.",
            'soha-crm'
        ));
    }

    if (empty($_POST['geste']) || empty($_POST['demande'])) {
        return null;
    }
    $id = absint($_POST['demande']);
    check_admin_referer('soha_crm_demande_' . $id, 'soha_crm_jeton');

    if (!current_user_can(soha_crm_capacite())) {
        return array('genre' => 'error', 'texte' => __('Droits insuffisants.', 'soha-crm'));
    }

    $demande = get_post($id);
    if (!$demande || SOHA_CRM_DEMANDE !== $demande->post_type) {
        return array('genre' => 'error', 'texte' => __('Demande introuvable.', 'soha-crm'));
    }

    switch (sanitize_key(wp_unslash($_POST['geste']))) {
        case 'verser':
            $r = soha_crm_verser_au_repertoire($id);
            if (is_wp_error($r)) {
                return array('genre' => 'error', 'texte' => $r->get_error_message());
            }
            $texte = 'cree' === $r['geste']
                ? sprintf(
                    /* translators: %s : le nom du contact. */
                    __('Fiche créée pour %s.', 'soha-crm'),
                    $r['nom']
                )
                : sprintf(
                    /* translators: %s : le nom du contact. */
                    __('%s existait déjà : la demande a été ajoutée à son historique, sans doublon.', 'soha-crm'),
                    $r['nom']
                );
            if (!empty($r['reservation'])) {
                $texte .= ' ' . sprintf(
                    /* translators: %s : espace, date et prix de la réservation. */
                    __('Réservation créée en devis : %s.', 'soha-crm'),
                    $r['reservation']
                );
            }
            $texte .= ' ' . __("Recharge le CRM si tu l'as ouvert ailleurs.", 'soha-crm');
            return array('genre' => 'success', 'texte' => $texte);

        case 'traiter':
            update_post_meta($id, '_soha_traitee', 1);
            return array('genre' => 'success', 'texte' => __('Marquée traitée.', 'soha-crm'));

        case 'rouvrir':
            update_post_meta($id, '_soha_traitee', 0);
            return array('genre' => 'success', 'texte' => __('Remise en attente.', 'soha-crm'));

        case 'supprimer':
            wp_delete_post($id, true);
            return array('genre' => 'success', 'texte' => __('Demande supprimée.', 'soha-crm'));
    }

    return null;
}

/* -------------------------------------------------------------------------- */
/*  L'export                                                                   */
/* -------------------------------------------------------------------------- */

add_action('admin_post_soha_crm_export', function () {
    if (!current_user_can(soha_crm_capacite())) {
        wp_die(esc_html__('Droits insuffisants.', 'soha-crm'));
    }
    check_admin_referer('soha_crm_export');

    $demandes = get_posts(array(
        'post_type'      => SOHA_CRM_DEMANDE,
        'post_status'    => 'publish',
        'posts_per_page' => -1,
        'orderby'        => 'date',
        'order'          => 'DESC',
    ));

    nocache_headers();
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename=soha-demandes-' . gmdate('Ymd') . '.csv');

    $sortie = fopen('php://output', 'w');
    fwrite($sortie, "\xEF\xBB\xBF");      // pour qu'Excel lise les accents
    fputcsv($sortie, array('Reçue le', 'Formulaire', 'Nom', 'Courriel', 'Téléphone',
                           'Infolettre', 'Traitée', 'Au répertoire', 'Réservation', 'Contenu'));

    foreach ($demandes as $d) {
        fputcsv($sortie, array(
            get_the_date('Y-m-d H:i', $d),
            (string) get_post_meta($d->ID, '_soha_formulaire', true),
            (string) get_post_meta($d->ID, '_soha_nom', true),
            (string) get_post_meta($d->ID, '_soha_courriel', true),
            (string) get_post_meta($d->ID, '_soha_telephone', true),
            get_post_meta($d->ID, '_soha_consentement', true) ? 'oui' : 'non',
            get_post_meta($d->ID, '_soha_traitee', true) ? 'oui' : 'non',
            (string) get_post_meta($d->ID, '_soha_versee', true),
            (string) get_post_meta($d->ID, '_soha_reservation', true),
            soha_crm_resumer($d->ID, 2000),
        ));
    }
    fclose($sortie);
    exit;
});

/* La pastille du menu : le nombre de demandes qui attendent. */
add_action('admin_menu', function () {
    global $menu, $submenu;
    $n = soha_crm_compter_non_traitees();
    if (!$n || empty($submenu['soha-crm'])) {
        return;
    }
    $pastille = ' <span class="update-plugins count-' . (int) $n . '"><span class="plugin-count">'
              . (int) $n . '</span></span>';
    foreach ($submenu['soha-crm'] as $i => $entree) {
        if ('soha-crm-demandes' === $entree[2]) {
            $submenu['soha-crm'][$i][0] .= $pastille;
        }
    }
    foreach ((array) $menu as $i => $entree) {
        if (isset($entree[2]) && 'soha-crm' === $entree[2]) {
            $menu[$i][0] .= $pastille;
        }
    }
}, 99);
