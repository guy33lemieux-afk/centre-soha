<?php
/**
 * Centre Soha — CRM : qui entre.
 *
 * Le CRM tient des noms, des courriels et des téléphones de personnes réelles.
 * L'accès ne peut donc pas être un effet de bord d'autre chose : quelqu'un à qui
 * on donne le droit de corriger une page ne devrait pas hériter du répertoire.
 *
 * D'où une capacité à elle, `soha_acceder_crm`, qu'on donne à une personne
 * nommée — et un écran pour la donner et la retirer sans toucher au code.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * La capacité qui ouvre le CRM.
 *
 * Le filtre reste, pour qu'un thème puisse resserrer sans modifier l'extension.
 */
function soha_crm_capacite() {
    return apply_filters('soha_crm_capacite', 'soha_acceder_crm');
}

/** Les administratrices et administrateurs l'ont d'office. */
function soha_crm_poser_la_capacite() {
    $role = get_role('administrator');
    if ($role && !$role->has_cap('soha_acceder_crm')) {
        $role->add_cap('soha_acceder_crm');
    }
}

/**
 * Les personnes qui ont accès, aujourd'hui.
 *
 * On interroge les comptes un à un plutôt que de tenir une liste à part : la
 * liste finirait par mentir le jour où quelqu'un change de rôle ou s'en va.
 */
function soha_crm_qui_a_acces() {
    $gens = array();
    foreach (get_users(array('fields' => array('ID'))) as $u) {
        $user = get_userdata($u->ID);
        if ($user && $user->has_cap('soha_acceder_crm')) {
            $gens[] = $user;
        }
    }
    return $gens;
}

/** Par son rôle (administratrice), ou par une permission nominative ? */
function soha_crm_acces_par_le_role($user) {
    foreach ((array) $user->roles as $nom) {
        $role = get_role($nom);
        if ($role && $role->has_cap('soha_acceder_crm')) {
            return true;
        }
    }
    return false;
}

/* -------------------------------------------------------------------------- */
/*  L'écran                                                                    */
/* -------------------------------------------------------------------------- */

add_action('admin_menu', function () {
    add_submenu_page(
        'soha-crm',
        __('Accès au CRM', 'soha-crm'),
        __('Accès', 'soha-crm'),
        'promote_users',                 // donner un droit est un geste d'administration
        'soha-crm-acces',
        'soha_crm_ecran_acces'
    );
}, 20);

function soha_crm_ecran_acces() {
    if (!current_user_can('promote_users')) {
        wp_die(esc_html__("Seule une administratrice peut changer les accès.", 'soha-crm'));
    }

    $message = '';
    if (isset($_POST['soha_crm_acces_jeton'])) {
        check_admin_referer('soha_crm_acces', 'soha_crm_acces_jeton');
        $coches = isset($_POST['acces']) ? array_map('absint', (array) $_POST['acces']) : array();
        $change = 0;
        foreach (get_users(array('fields' => array('ID'))) as $u) {
            $user = get_userdata($u->ID);
            if (!$user || soha_crm_acces_par_le_role($user)) {
                continue;                // le rôle décide : on n'y touche pas ici
            }
            $veut = in_array((int) $u->ID, $coches, true);
            $a    = $user->has_cap('soha_acceder_crm');
            if ($veut && !$a) {
                $user->add_cap('soha_acceder_crm');
                $change++;
            } elseif (!$veut && $a) {
                $user->remove_cap('soha_acceder_crm');
                $change++;
            }
        }
        $message = 0 === $change
            ? __('Rien à changer.', 'soha-crm')
            : sprintf(
                /* translators: %d : nombre de comptes modifiés. */
                _n('%d accès modifié.', '%d accès modifiés.', $change, 'soha-crm'),
                $change
            );
    }

    $gens = get_users(array('orderby' => 'display_name'));
    ?>
    <div class="wrap">
        <h1><?php esc_html_e('Qui a accès au CRM', 'soha-crm'); ?></h1>

        <?php if ($message) : ?>
            <div class="notice notice-success"><p><?php echo esc_html($message); ?></p></div>
        <?php endif; ?>

        <p style="max-width:70ch">
            <?php esc_html_e(
                "Le CRM contient les coordonnées de personnes réelles. Coche seulement les comptes qui doivent les voir. Les administratrices y ont accès par leur rôle : leur ligne est grisée, il faut leur retirer le rôle pour leur retirer le CRM.",
                'soha-crm'
            ); ?>
        </p>

        <form method="post">
            <?php wp_nonce_field('soha_crm_acces', 'soha_crm_acces_jeton'); ?>
            <table class="widefat striped" style="max-width:760px">
                <thead>
                    <tr>
                        <th style="width:70px"><?php esc_html_e('Accès', 'soha-crm'); ?></th>
                        <th><?php esc_html_e('Personne', 'soha-crm'); ?></th>
                        <th><?php esc_html_e('Courriel', 'soha-crm'); ?></th>
                        <th><?php esc_html_e('Rôle', 'soha-crm'); ?></th>
                    </tr>
                </thead>
                <tbody>
                <?php foreach ($gens as $user) :
                    $par_role = soha_crm_acces_par_le_role($user);
                    $coche    = $par_role || $user->has_cap('soha_acceder_crm');
                    ?>
                    <tr>
                        <td>
                            <input type="checkbox" name="acces[]" value="<?php echo esc_attr($user->ID); ?>"
                                   <?php checked($coche); ?> <?php disabled($par_role); ?>
                                   aria-label="<?php echo esc_attr(sprintf(
                                       /* translators: %s : nom de la personne. */
                                       __('Donner accès au CRM à %s', 'soha-crm'),
                                       $user->display_name
                                   )); ?>">
                        </td>
                        <td><strong><?php echo esc_html($user->display_name); ?></strong></td>
                        <td><?php echo esc_html($user->user_email); ?></td>
                        <td>
                            <?php echo esc_html(implode(', ', (array) $user->roles)); ?>
                            <?php if ($par_role) : ?>
                                <em style="color:#646970">· <?php esc_html_e('par son rôle', 'soha-crm'); ?></em>
                            <?php endif; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
            <?php submit_button(__('Enregistrer les accès', 'soha-crm')); ?>
        </form>
    </div>
    <?php
}
