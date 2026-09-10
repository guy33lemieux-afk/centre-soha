<?php
/**
 * Centre Soha — CRM : la sauvegarde et la restauration du registre.
 *
 * Le registre entier tient dans une seule option. C'est ce qui le rend simple —
 * et c'est ce qui rend ce fichier nécessaire : une seule option, c'est aussi un
 * seul endroit où tout perdre. UpdraftPlus sauvegarde la base, mais restaurer
 * une base entière pour rattraper une fausse manœuvre dans le CRM, c'est un
 * marteau pour une punaise.
 *
 * Ici : un fichier qu'on télécharge quand on veut, qu'on remet quand il faut, et
 * un filet — l'état d'avant la restauration est conservé, pour qu'une
 * restauration ratée se défasse une fois.
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SOHA_CRM_AVANT', 'soha_crm_avant_restauration');

add_action('admin_menu', function () {
    add_submenu_page(
        'soha-crm',
        __('Sauvegarde du registre', 'soha-crm'),
        __('Sauvegarde', 'soha-crm'),
        soha_crm_capacite(),
        'soha-crm-sauvegarde',
        'soha_crm_ecran_sauvegarde'
    );
}, 15);

/** Ce que contient le registre, en clair, pour l'afficher sans le décoder deux fois. */
function soha_crm_compter() {
    $etat = soha_crm_registre_lire();
    $reg  = $etat['valeur'] ? json_decode($etat['valeur'], true) : null;
    if (!is_array($reg)) {
        return array('contacts' => 0, 'reservations' => 0, 'ateliers' => 0, 'octets' => 0);
    }
    return array(
        'contacts'     => isset($reg['contacts']) ? count((array) $reg['contacts']) : 0,
        'reservations' => isset($reg['reservations']) ? count((array) $reg['reservations']) : 0,
        'ateliers'     => isset($reg['ateliers']) ? count((array) $reg['ateliers']) : 0,
        'octets'       => strlen($etat['valeur']),
    );
}

function soha_crm_ecran_sauvegarde() {
    if (!current_user_can(soha_crm_capacite())) {
        wp_die(esc_html__("Tu n'as pas accès au CRM du Centre Soha.", 'soha-crm'));
    }

    $avis  = soha_crm_traiter_restauration();
    $c     = soha_crm_compter();
    $avant = get_option(SOHA_CRM_AVANT, array());
    ?>
    <div class="wrap">
        <h1><?php esc_html_e('Sauvegarde du registre', 'soha-crm'); ?></h1>

        <?php if ($avis) : ?>
            <div class="notice notice-<?php echo esc_attr($avis['genre']); ?>">
                <p><?php echo esc_html($avis['texte']); ?></p>
            </div>
        <?php endif; ?>

        <p style="max-width:72ch">
            <?php esc_html_e(
                "Le registre est sauvegardé avec la base du site par UpdraftPlus. Ce fichier-ci sert à autre chose : reprendre une fausse manœuvre dans le CRM sans restaurer tout le site, et emporter les données ailleurs si un jour il le faut.",
                'soha-crm'
            ); ?>
        </p>

        <h2><?php esc_html_e('Aujourd\'hui, le registre contient', 'soha-crm'); ?></h2>
        <table class="widefat striped" style="max-width:420px">
            <tbody>
                <tr><td><?php esc_html_e('Fiches contact', 'soha-crm'); ?></td>
                    <td><strong><?php echo (int) $c['contacts']; ?></strong></td></tr>
                <tr><td><?php esc_html_e('Réservations', 'soha-crm'); ?></td>
                    <td><strong><?php echo (int) $c['reservations']; ?></strong></td></tr>
                <tr><td><?php esc_html_e('Ateliers', 'soha-crm'); ?></td>
                    <td><strong><?php echo (int) $c['ateliers']; ?></strong></td></tr>
                <tr><td><?php esc_html_e('Taille', 'soha-crm'); ?></td>
                    <td><?php echo esc_html(size_format(max(1, $c['octets']))); ?></td></tr>
            </tbody>
        </table>

        <p>
            <a class="button button-primary" href="<?php echo esc_url(wp_nonce_url(
                add_query_arg(array('action' => 'soha_crm_sauvegarde'), admin_url('admin-post.php')),
                'soha_crm_sauvegarde'
            )); ?>"><?php esc_html_e('Télécharger la sauvegarde (JSON)', 'soha-crm'); ?></a>
        </p>

        <?php if (current_user_can('manage_options')) : ?>
            <hr style="margin:32px 0">
            <h2><?php esc_html_e('Remettre une sauvegarde', 'soha-crm'); ?></h2>
            <p style="max-width:72ch">
                <strong><?php esc_html_e('Ceci remplace tout le registre.', 'soha-crm'); ?></strong>
                <?php esc_html_e(
                    "L'état actuel est conservé de côté : si tu te trompes de fichier, tu peux revenir en arrière une fois, juste en dessous.",
                    'soha-crm'
                ); ?>
            </p>
            <form method="post" enctype="multipart/form-data">
                <?php wp_nonce_field('soha_crm_restaurer', 'soha_crm_restaurer_jeton'); ?>
                <p><input type="file" name="fichier" accept=".json,application/json" required></p>
                <p><label>
                    <input type="checkbox" name="compris" value="1" required>
                    <?php esc_html_e("Je comprends que le registre actuel sera remplacé.", 'soha-crm'); ?>
                </label></p>
                <?php submit_button(__('Remettre cette sauvegarde', 'soha-crm'), 'secondary'); ?>
            </form>

            <?php if (!empty($avant['valeur'])) :
                $c2 = json_decode($avant['valeur'], true); ?>
                <h3><?php esc_html_e('Revenir en arrière', 'soha-crm'); ?></h3>
                <p>
                    <?php printf(
                        /* translators: 1 : date, 2 : nombre de fiches. */
                        esc_html__('Un état est conservé depuis le %1$s (%2$d fiches). Il ne sera pas gardé indéfiniment : la prochaine restauration le remplacera.', 'soha-crm'),
                        esc_html(date_i18n(get_option('date_format') . ' à ' . get_option('time_format'), (int) $avant['quand'])),
                        (int) (is_array($c2) && isset($c2['contacts']) ? count($c2['contacts']) : 0)
                    ); ?>
                </p>
                <form method="post">
                    <?php wp_nonce_field('soha_crm_restaurer', 'soha_crm_restaurer_jeton'); ?>
                    <input type="hidden" name="revenir" value="1">
                    <?php submit_button(__('Revenir à cet état', 'soha-crm'), 'secondary', 'submit', false); ?>
                </form>
            <?php endif; ?>
        <?php endif; ?>
    </div>
    <?php
}

/**
 * Un registre est-il recevable ?
 *
 * On exige la forme, pas le contenu : trois listes et rien d'autre. Un fichier
 * qui n'a pas cette forme est refusé avant d'avoir touché quoi que ce soit —
 * remettre n'importe quel JSON à la place du registre, ce serait le perdre en
 * croyant le sauver.
 */
function soha_crm_registre_recevable($valeur) {
    if (!is_string($valeur) || strlen($valeur) > SOHA_CRM_TAILLE_MAX) {
        return false;
    }
    $reg = json_decode($valeur, true);
    if (!is_array($reg)) {
        return false;
    }
    foreach (array('contacts', 'reservations', 'ateliers') as $col) {
        if (!isset($reg[$col]) || !is_array($reg[$col])) {
            return false;
        }
    }
    foreach ((array) $reg['contacts'] as $c) {
        if (!is_array($c) || !isset($c['id'], $c['nom'])) {
            return false;
        }
    }
    return true;
}

function soha_crm_traiter_restauration() {
    if (empty($_POST['soha_crm_restaurer_jeton'])) {
        return null;
    }
    check_admin_referer('soha_crm_restaurer', 'soha_crm_restaurer_jeton');

    if (!current_user_can('manage_options')) {
        return array('genre' => 'error', 'texte' => __('Seule une administratrice peut remettre une sauvegarde.', 'soha-crm'));
    }

    /* --- revenir en arrière --- */
    if (!empty($_POST['revenir'])) {
        $avant = get_option(SOHA_CRM_AVANT, array());
        if (empty($avant['valeur'])) {
            return array('genre' => 'error', 'texte' => __("Il n'y a pas d'état conservé.", 'soha-crm'));
        }
        $courant = soha_crm_registre_lire();
        $r = soha_crm_registre_ecrire($avant['valeur'], 0, false);
        if (is_wp_error($r)) {
            return array('genre' => 'error', 'texte' => $r->get_error_message());
        }
        /* On échange : ce qu'on vient de quitter devient le retour possible. */
        update_option(SOHA_CRM_AVANT, array('valeur' => $courant['valeur'], 'quand' => time()), false);
        return array('genre' => 'success', 'texte' => __("Registre revenu à l'état conservé.", 'soha-crm'));
    }

    /* --- remettre un fichier --- */
    if (empty($_FILES['fichier']['tmp_name']) || !is_uploaded_file($_FILES['fichier']['tmp_name'])) {
        return array('genre' => 'error', 'texte' => __('Aucun fichier reçu.', 'soha-crm'));
    }
    if (empty($_POST['compris'])) {
        return array('genre' => 'error', 'texte' => __('La case de confirmation n\'était pas cochée ; rien n\'a été touché.', 'soha-crm'));
    }

    $brut = file_get_contents($_FILES['fichier']['tmp_name']);
    $lu   = json_decode((string) $brut, true);

    /* On accepte aussi bien le fichier de cette extension (avec son en-tête)
       que le JSON nu exporté par l'interface. */
    $valeur = null;
    if (is_array($lu) && isset($lu['registre']) && is_array($lu['registre'])) {
        $valeur = wp_json_encode($lu['registre']);
    } elseif (is_array($lu)) {
        $valeur = wp_json_encode($lu);
    }

    if (null === $valeur || !soha_crm_registre_recevable($valeur)) {
        return array('genre' => 'error', 'texte' => __(
            "Ce fichier n'a pas la forme d'un registre du CRM. Rien n'a été touché.",
            'soha-crm'
        ));
    }

    $courant = soha_crm_registre_lire();
    update_option(SOHA_CRM_AVANT, array('valeur' => $courant['valeur'], 'quand' => time()), false);

    /* Sans synchroniser : remettre une sauvegarde n'est pas un consentement
       nouveau, et cela réinscrirait tout un registre d'un coup chez Mailchimp. */
    $r = soha_crm_registre_ecrire($valeur, 0, false);
    if (is_wp_error($r)) {
        return array('genre' => 'error', 'texte' => $r->get_error_message());
    }

    $reg = json_decode($valeur, true);
    return array('genre' => 'success', 'texte' => sprintf(
        /* translators: 1 : fiches, 2 : réservations. */
        __('Registre remis : %1$d fiches et %2$d réservations. Recharge le CRM.', 'soha-crm'),
        count($reg['contacts']),
        count($reg['reservations'])
    ));
}

/* -------------------------------------------------------------------------- */
/*  Le téléchargement                                                          */
/* -------------------------------------------------------------------------- */

add_action('admin_post_soha_crm_sauvegarde', function () {
    if (!current_user_can(soha_crm_capacite())) {
        wp_die(esc_html__('Droits insuffisants.', 'soha-crm'));
    }
    check_admin_referer('soha_crm_sauvegarde');

    $etat = soha_crm_registre_lire();
    $reg  = $etat['valeur'] ? json_decode($etat['valeur'], true) : array();

    /* Un en-tête, pour qu'un fichier retrouvé dans deux ans se présente. */
    $paquet = array(
        'quoi'     => 'Centre Soha — registre du CRM',
        'site'     => home_url('/'),
        'version'  => SOHA_CRM_VERSION,
        'revision' => $etat['revision'],
        'faite_le' => current_time('c'),
        'registre' => is_array($reg) ? $reg : array(),
    );

    nocache_headers();
    header('Content-Type: application/json; charset=utf-8');
    header('Content-Disposition: attachment; filename=soha-registre-' . gmdate('Ymd-Hi') . '.json');
    echo wp_json_encode($paquet, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
});
