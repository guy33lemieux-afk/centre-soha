<?php
/**
 * Centre Soha — CRM : l'écran de l'infolettre.
 *
 * Brancher Mailchimp n'est pas qu'un réglage technique : c'est envoyer des
 * coordonnées de personnes du 961 chez un fournisseur américain. Cet écran le
 * dit avant de le faire, et donne le paragraphe exact à ajouter à la politique
 * de confidentialité — parce qu'une obligation qu'on rappelle sans fournir le
 * texte est une obligation qu'on ne remplit pas.
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('admin_menu', function () {
    add_submenu_page(
        'soha-crm',
        __('Infolettre', 'soha-crm'),
        __('Infolettre', 'soha-crm'),
        soha_crm_capacite(),
        'soha-crm-infolettre',
        'soha_crm_ecran_infolettre'
    );
}, 12);

/** Ce qu'on montre d'une clé : de quoi la reconnaître, pas de quoi s'en servir. */
function soha_crm_info_cle_masquee() {
    $cle = (string) get_option(SOHA_CRM_INFO_CLE, '');
    if ('' === $cle) {
        return '';
    }
    $dc = soha_crm_info_centre($cle);
    return str_repeat('•', 12) . substr($cle, -4) . ($dc ? ' · ' . $dc : '');
}

function soha_crm_ecran_infolettre() {
    if (!current_user_can(soha_crm_capacite())) {
        wp_die(esc_html__("Tu n'as pas accès au CRM du Centre Soha.", 'soha-crm'));
    }

    $avis = soha_crm_info_traiter_le_geste();

    $active    = soha_crm_info_active();
    $file      = (array) get_option(SOHA_CRM_INFO_FILE, array());
    $journal   = (array) get_option(SOHA_CRM_INFO_JJ, array());
    $bloquees  = array_filter($file, function ($x) { return (int) $x['essais'] >= SOHA_CRM_INFO_ESSAIS; });
    $audiences = $active ? soha_crm_info_audiences() : array();
    ?>
    <div class="wrap">
        <h1><?php esc_html_e('Infolettre', 'soha-crm'); ?></h1>

        <?php if ($avis) : ?>
            <div class="notice notice-<?php echo esc_attr($avis['genre']); ?>">
                <p><?php echo wp_kses_post($avis['texte']); ?></p>
            </div>
        <?php endif; ?>

        <p style="max-width:74ch">
            <?php esc_html_e(
                "Quand une personne coche l'infolettre — sur un formulaire du site, ou sur sa fiche dans le CRM — son adresse part chez Mailchimp toute seule. Quand elle se désabonne depuis un courriel, sa fiche le note. Plus personne ne recopie une adresse à la main, et les deux côtés disent la même chose.",
                'soha-crm'
            ); ?>
        </p>

        <div style="border-left:3px solid #d63638;background:#fff;padding:14px 18px;margin:22px 0;max-width:74ch">
            <p style="margin-top:0"><strong><?php esc_html_e(
                "Mailchimp est américain. Ça se dit dans la politique.",
                'soha-crm'
            ); ?></strong></p>
            <p><?php esc_html_e(
                "Mailchimp appartient à Intuit et ses serveurs sont aux États-Unis. Inscrire quelqu'un, c'est communiquer son adresse et son prénom hors du Québec — la Loi 25 demande que ce soit annoncé. Le paragraphe à ajouter à la section « Où vont tes renseignements » est prêt ci-dessous : copie-le tel quel.",
                'soha-crm'
            ); ?></p>
            <p style="margin-bottom:0"><?php esc_html_e(
                "Ce qui ne part pas : la date du consentement, le formulaire qui l'a recueilli, le téléphone, les notes. Mailchimp reçoit une adresse et un prénom. La preuve du consentement reste au 961 — c'est ici qu'il faudra la retrouver si on la demande, et un compte chez un tiers n'est pas un registre de preuve.",
                'soha-crm'
            ); ?></p>
            <p>
                <label for="soha-para" style="font-weight:600"><?php esc_html_e('À copier dans la politique de confidentialité :', 'soha-crm'); ?></label><br>
                <textarea id="soha-para" rows="5" readonly style="width:100%;max-width:70ch;font-family:inherit"
                ><?php echo esc_textarea(soha_crm_info_paragraphe()); ?></textarea>
            </p>
        </div>

        <h2><?php esc_html_e('La liaison', 'soha-crm'); ?></h2>
        <form method="post">
            <?php wp_nonce_field('soha_crm_info', 'soha_crm_info_jeton'); ?>
            <table class="form-table" role="presentation">
                <tr>
                    <th scope="row"><label for="cle"><?php esc_html_e("Clé d'API Mailchimp", 'soha-crm'); ?></label></th>
                    <td>
                        <input type="password" id="cle" name="cle" class="regular-text" autocomplete="off"
                               placeholder="<?php echo esc_attr($active ? soha_crm_info_cle_masquee() : 'xxxxxxxx…-us21'); ?>">
                        <p class="description"><?php esc_html_e(
                            "Dans Mailchimp : ton avatar → Account & billing → Extras → API keys → Create a key. Laisse vide pour garder celle qui est déjà enregistrée.",
                            'soha-crm'
                        ); ?></p>
                    </td>
                </tr>
                <?php if ($audiences && !is_wp_error($audiences)) : ?>
                <tr>
                    <th scope="row"><label for="liste"><?php esc_html_e('Audience', 'soha-crm'); ?></label></th>
                    <td>
                        <select id="liste" name="liste">
                            <?php foreach ($audiences as $a) : ?>
                                <option value="<?php echo esc_attr($a['id']); ?>"
                                    <?php selected(get_option(SOHA_CRM_INFO_LISTE, ''), $a['id']); ?>>
                                    <?php printf('%s (%d)', esc_html($a['nom']), (int) $a['membres']); ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </td>
                </tr>
                <?php endif; ?>
                <tr>
                    <th scope="row"><?php esc_html_e('Double confirmation', 'soha-crm'); ?></th>
                    <td>
                        <label>
                            <input type="checkbox" name="double" value="1" <?php checked(get_option(SOHA_CRM_INFO_DOUBLE, false)); ?>>
                            <?php esc_html_e("Demander une confirmation par courriel avant d'inscrire", 'soha-crm'); ?>
                        </label>
                        <p class="description"><?php esc_html_e(
                            "Décochée, la case du formulaire suffit : c'est un consentement daté et conservé, la Loi 25 s'en contente. Cochée, la personne doit encore cliquer dans un courriel — une preuve de plus, et environ une inscription sur quatre qui n'arrive jamais.",
                            'soha-crm'
                        ); ?></p>
                    </td>
                </tr>
            </table>
            <p>
                <button class="button button-primary" name="geste" value="enregistrer"><?php esc_html_e('Enregistrer', 'soha-crm'); ?></button>
                <button class="button" name="geste" value="tester"><?php esc_html_e('Tester la liaison', 'soha-crm'); ?></button>
                <?php if ($active) : ?>
                    <button class="button" name="geste" value="synchroniser"><?php esc_html_e('Envoyer la file maintenant', 'soha-crm'); ?></button>
                    <button class="button button-link-delete" name="geste" value="oublier"
                            onclick="return confirm('<?php echo esc_js(__('Oublier la clé ? Les inscriptions cesseront de partir.', 'soha-crm')); ?>')">
                        <?php esc_html_e('Oublier la clé', 'soha-crm'); ?></button>
                <?php endif; ?>
            </p>
        </form>

        <?php if ($active) : ?>
            <h2><?php esc_html_e('Ce qui attend de partir', 'soha-crm'); ?></h2>
            <?php if (!$file) : ?>
                <p><em><?php esc_html_e('Rien en attente. Tout est passé.', 'soha-crm'); ?></em></p>
            <?php else : ?>
                <table class="widefat striped" style="max-width:760px">
                    <thead><tr>
                        <th><?php esc_html_e('Adresse', 'soha-crm'); ?></th>
                        <th style="width:130px"><?php esc_html_e('Geste', 'soha-crm'); ?></th>
                        <th style="width:80px"><?php esc_html_e('Essais', 'soha-crm'); ?></th>
                        <th><?php esc_html_e('Dernier refus', 'soha-crm'); ?></th>
                    </tr></thead>
                    <tbody>
                    <?php foreach (array_slice($file, 0, 30) as $x) : ?>
                        <tr<?php echo (int) $x['essais'] >= SOHA_CRM_INFO_ESSAIS ? ' style="background:#fcf0f1"' : ''; ?>>
                            <td><?php echo esc_html($x['courriel']); ?></td>
                            <td><?php echo 'desabonne' === $x['statut']
                                ? esc_html__('désabonner', 'soha-crm')
                                : esc_html__('inscrire', 'soha-crm'); ?></td>
                            <td><?php echo (int) $x['essais']; ?></td>
                            <td><?php echo esc_html($x['erreur']); ?></td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>

            <?php if ($bloquees) : ?>
                <div class="notice notice-error inline"><p><?php
                    printf(
                        /* translators: %d : nombre d'adresses bloquées. */
                        esc_html__("%d adresse(s) ont échoué cinq fois et ne seront plus réessayées. Lis le refus de Mailchimp ci-dessus : c'est souvent une adresse invalide, ou quelqu'un qui s'était déjà désabonné et que Mailchimp refuse de réinscrire — ce qui est son droit.", 'soha-crm'),
                        count($bloquees)
                    );
                ?></p></div>
            <?php endif; ?>

            <?php if (!empty($journal['quand'])) : ?>
                <p style="color:#646970"><?php printf(
                    /* translators: 1 : date, 2 : envoyées, 3 : restantes. */
                    esc_html__('Dernier passage le %1$s : %2$d envoyée(s), %3$d en attente.', 'soha-crm'),
                    esc_html(date_i18n(get_option('date_format') . ' à ' . get_option('time_format'), (int) $journal['quand'])),
                    (int) $journal['faits'],
                    (int) $journal['reste']
                ); ?></p>
            <?php endif; ?>

            <h2><?php esc_html_e('Pour que les désabonnements reviennent', 'soha-crm'); ?></h2>
            <p style="max-width:74ch"><?php esc_html_e(
                "Sans ceci, une personne qui se désabonne depuis un courriel resterait « abonnée » sur sa fiche : deux vérités pour une même personne, et c'est la fiche qui aurait tort. Dans Mailchimp : Audience → Settings → Webhooks → Create New Webhook, colle cette adresse et coche « Unsubscribes ».",
                'soha-crm'
            ); ?></p>
            <p><input type="text" readonly class="large-text code" onclick="this.select()"
                      value="<?php echo esc_attr(soha_crm_info_adresse_retour()); ?>"></p>
            <p class="description" style="max-width:74ch"><?php esc_html_e(
                "Cette adresse contient un secret : ne la publie nulle part. Si elle traîne quelque part, oublie la clé et réenregistre-la — un nouveau secret sera créé.",
                'soha-crm'
            ); ?></p>
        <?php endif; ?>
    </div>
    <?php
}

/** Le paragraphe à coller dans la politique — écrit, pas résumé. */
function soha_crm_info_paragraphe() {
    return __(
        "Infolettre. Si tu t'inscris à notre infolettre, ton adresse courriel et ton prénom sont transmis à Mailchimp, un service d'envoi de courriels exploité par Intuit Inc., dont les serveurs sont situés aux États-Unis. Ces renseignements y sont conservés tant que tu restes inscrit·e, et servent uniquement à t'envoyer l'infolettre du Centre Soha. Chaque envoi contient un lien de désabonnement en un clic ; ton désabonnement est aussi noté dans nos dossiers. Le reste de tes renseignements — la date de ton consentement, ton téléphone, tes échanges avec le centre — demeure au Québec, sur l'hébergement de centresoha.com, et n'est pas communiqué à Mailchimp.",
        'soha-crm'
    );
}

/* -------------------------------------------------------------------------- */
/*  Les gestes de l'écran                                                      */
/* -------------------------------------------------------------------------- */

function soha_crm_info_traiter_le_geste() {
    if (empty($_POST['soha_crm_info_jeton'])) {
        return null;
    }
    check_admin_referer('soha_crm_info', 'soha_crm_info_jeton');

    if (!current_user_can(soha_crm_capacite())) {
        return array('genre' => 'error', 'texte' => __('Droits insuffisants.', 'soha-crm'));
    }

    $geste = isset($_POST['geste']) ? sanitize_key(wp_unslash($_POST['geste'])) : '';
    $cle_envoyee = isset($_POST['cle']) ? trim((string) wp_unslash($_POST['cle'])) : '';

    if ('oublier' === $geste) {
        delete_option(SOHA_CRM_INFO_CLE);
        delete_option(SOHA_CRM_INFO_LISTE);
        delete_option(SOHA_CRM_INFO_SECRET);
        return array('genre' => 'success', 'texte' => __(
            "Clé oubliée. Les inscriptions ne partent plus, et l'adresse de retour est caduque — pense à retirer le webhook dans Mailchimp.",
            'soha-crm'
        ));
    }

    if ('tester' === $geste) {
        $cle = '' !== $cle_envoyee ? $cle_envoyee : null;
        $compte = soha_crm_info_compte($cle);
        if (is_wp_error($compte)) {
            return array('genre' => 'error', 'texte' => sprintf(
                /* translators: %s : le message de Mailchimp. */
                __('Mailchimp refuse la liaison : %s', 'soha-crm'),
                $compte->get_error_message()
            ));
        }
        return array('genre' => 'success', 'texte' => sprintf(
            /* translators: 1 : nom du compte, 2 : courriel du compte. */
            __('Liaison établie avec le compte « %1$s » (%2$s).', 'soha-crm'),
            esc_html($compte['compte']),
            esc_html($compte['courriel'])
        ));
    }

    if ('synchroniser' === $geste) {
        $n = soha_crm_info_vider_la_file();
        return array('genre' => 'success', 'texte' => sprintf(
            /* translators: %d : nombre d'adresses envoyées. */
            _n('%d adresse envoyée.', '%d adresses envoyées.', $n, 'soha-crm'),
            $n
        ));
    }

    /* --- enregistrer --- */
    if ('' !== $cle_envoyee) {
        /* On refuse une clé qui ne mène nulle part : mieux vaut le dire ici que
           de laisser des inscriptions s'accumuler dans une file muette. */
        $compte = soha_crm_info_compte($cle_envoyee);
        if (is_wp_error($compte)) {
            return array('genre' => 'error', 'texte' => sprintf(
                /* translators: %s : le message de Mailchimp. */
                __("Clé refusée, rien n'a été enregistré : %s", 'soha-crm'),
                $compte->get_error_message()
            ));
        }
        update_option(SOHA_CRM_INFO_CLE, $cle_envoyee, false);
    }

    if (isset($_POST['liste'])) {
        update_option(SOHA_CRM_INFO_LISTE, sanitize_text_field(wp_unslash($_POST['liste'])), false);
    }
    update_option(SOHA_CRM_INFO_DOUBLE, !empty($_POST['double']), false);

    if ('' === (string) get_option(SOHA_CRM_INFO_LISTE, '')) {
        return array('genre' => 'warning', 'texte' => __(
            "Clé enregistrée. Choisis maintenant l'audience dans la liste qui vient d'apparaître, puis enregistre à nouveau.",
            'soha-crm'
        ));
    }
    return array('genre' => 'success', 'texte' => __('Réglages enregistrés.', 'soha-crm'));
}
