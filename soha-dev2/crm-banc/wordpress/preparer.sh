#!/bin/sh
# Monte un WordPress jetable pour le banc : WordPress 6.8.3 sur SQLite, aucune
# base de données à installer, aucun serveur à configurer. Rien de tout ceci ne
# ressemble à l'hébergement du Centre Soha — c'est voulu : si l'extension passe
# ici ET là, elle ne dépend d'aucune particularité de l'un ou de l'autre.
set -e
ICI=$(cd "$(dirname "$0")" && pwd)

git clone --depth 1 -q https://github.com/WordPress/WordPress.git "$ICI/wordpress"
( cd "$ICI/wordpress" && git fetch --depth 1 -q origin tag 6.8.3 && git checkout -q 6.8.3 )

git clone --depth 1 -q https://github.com/WordPress/sqlite-database-integration.git "$ICI/sqlite-tmp"
( cd "$ICI/sqlite-tmp" && git fetch --depth 1 -q origin tag v2.1.13 && git checkout -q v2.1.13 )
rm -rf "$ICI/sqlite-tmp/.git"
mv "$ICI/sqlite-tmp" "$ICI/wordpress/wp-content/plugins/sqlite-database-integration"

P="$ICI/wordpress/wp-content/plugins/sqlite-database-integration"
cp "$P/db.copy" "$ICI/wordpress/wp-content/db.php"
sed -i "s|{SQLITE_IMPLEMENTATION_FOLDER_PATH}|$P|g;s|{SQLITE_PLUGIN}|sqlite-database-integration/load.php|g" \
    "$ICI/wordpress/wp-content/db.php"
mkdir -p "$ICI/wordpress/wp-content/database"

cat > "$ICI/wordpress/wp-config.php" <<'PHP'
<?php
define('DB_NAME','soha'); define('DB_USER',''); define('DB_PASSWORD',''); define('DB_HOST','localhost');
define('DB_CHARSET','utf8mb4'); define('DB_COLLATE','');
define('AUTH_KEY','a'); define('SECURE_AUTH_KEY','b'); define('LOGGED_IN_KEY','c'); define('NONCE_KEY','d');
define('AUTH_SALT','e'); define('SECURE_AUTH_SALT','f'); define('LOGGED_IN_SALT','g'); define('NONCE_SALT','h');
$table_prefix = 'wp_';
/* Le mode bavard, et sans le filet qui masque les erreurs : au banc, on veut
   voir tomber ce qui tombe. */
define('WP_DEBUG', true); define('WP_DEBUG_DISPLAY', true);
define('WP_DISABLE_FATAL_ERROR_HANDLER', true);
define('WP_HOME','http://127.0.0.1:8899'); define('WP_SITEURL','http://127.0.0.1:8899');
define('FS_METHOD','direct');
if (!defined('ABSPATH')) define('ABSPATH', __DIR__ . '/');
require_once ABSPATH . 'wp-settings.php';
PHP

echo "WordPress prêt. Poser l'extension puis lancer le banc :"
echo "  cp -r <sortie de build_crm.py>/soha-crm $ICI/wordpress/wp-content/plugins/"
echo "  sh $ICI/banc.sh"
