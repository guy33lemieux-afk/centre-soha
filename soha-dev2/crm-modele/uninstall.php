<?php
/**
 * Centre Soha — CRM : la désinstallation.
 *
 * WordPress n'exécute ce fichier que si l'on supprime l'extension depuis
 * l'écran des extensions — pas à la désactivation. C'est le seul endroit où le
 * registre est effacé, et il faut l'avoir voulu.
 */

if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

delete_option('soha_crm_etat');
delete_option('soha_crm_revision');
