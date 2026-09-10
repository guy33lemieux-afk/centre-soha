<?php
/**
 * L'activation, dans son propre processus.
 *
 * C'est ce que fait WordPress : on active une fois, puis on sert des requêtes.
 * Activer et vérifier dans la même exécution donnerait un faux résultat — les
 * crochets `init` sont déjà passés, donc le type de contenu ne serait jamais
 * enregistré, et on croirait à tort qu'il manque.
 */
$_SERVER['HTTP_HOST'] = '127.0.0.1:8899';
$_SERVER['REQUEST_URI'] = '/wp-admin/';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_METHOD'] = 'GET';
define('WP_ADMIN', true);
require __DIR__ . '/wordpress/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';

$r = activate_plugin('soha-crm/soha-crm.php');
if (is_wp_error($r)) {
    echo "ACTIVATION REFUSÉE : ", $r->get_error_message(), "\n";
    exit(1);
}
echo "extension activée\n";
