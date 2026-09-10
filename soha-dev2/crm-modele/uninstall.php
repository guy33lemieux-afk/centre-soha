<?php
/**
 * Centre Soha — CRM : la désinstallation.
 *
 * WordPress n'exécute ce fichier que si l'on supprime l'extension depuis
 * l'écran des extensions — pas à la désactivation. C'est le seul endroit où le
 * registre et les demandes sont effacés, et il faut l'avoir voulu.
 */

if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

delete_option('soha_crm_etat');
delete_option('soha_crm_revision');
delete_option('soha_crm_dernier');
delete_option('soha_crm_derniere_purge');
delete_option('soha_crm_avant_restauration');
delete_option('soha_crm_infolettre_cle');
delete_option('soha_crm_infolettre_liste');
delete_option('soha_crm_infolettre_double');
delete_option('soha_crm_infolettre_file');
delete_option('soha_crm_infolettre_journal');
delete_option('soha_crm_infolettre_secret');

/* Les demandes archivées. */
$demandes = get_posts(array(
    'post_type'      => 'soha_demande',
    'post_status'    => 'any',
    'posts_per_page' => -1,
    'fields'         => 'ids',
));
foreach ($demandes as $id) {
    wp_delete_post($id, true);
}

/* La capacité, partout où elle a été posée. */
$role = get_role('administrator');
if ($role) {
    $role->remove_cap('soha_acceder_crm');
}
foreach (get_users(array('fields' => array('ID'))) as $u) {
    $user = get_userdata($u->ID);
    if ($user && isset($user->caps['soha_acceder_crm'])) {
        $user->remove_cap('soha_acceder_crm');
    }
}

foreach (array('soha_crm_purge', 'soha_crm_infolettre_reprise', 'soha_crm_infolettre_traiter') as $tache) {
    $prochaine = wp_next_scheduled($tache);
    if ($prochaine) {
        wp_unschedule_event($prochaine, $tache);
    }
}
