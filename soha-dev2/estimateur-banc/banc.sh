#!/bin/sh
# Le banc de l'estimateur. Base neuve, puis les deux suites.
set -e
ICI=$(cd "$(dirname "$0")" && pwd)
W="$ICI/wordpress"
rm -f "$W/wp-content/database/.ht.sqlite"
( cd "$W" && php -r '
  $_SERVER["HTTP_HOST"]="127.0.0.1:8899"; $_SERVER["REQUEST_URI"]="/"; $_SERVER["SERVER_NAME"]="127.0.0.1";
  define("WP_INSTALLING", true);
  require "wp-load.php"; require ABSPATH."wp-admin/includes/upgrade.php";
  wp_install("Centre Soha — banc", "mala", "mala@exemple.test", true, "", "motdepasse");
' ) > /dev/null 2>&1
php -r '
  $_SERVER["HTTP_HOST"]="127.0.0.1:8899"; $_SERVER["REQUEST_URI"]="/wp-admin/"; $_SERVER["SERVER_NAME"]="127.0.0.1";
  define("WP_ADMIN", true);
  require "'"$W"'/wp-load.php"; require_once ABSPATH."wp-admin/includes/plugin.php";
  $r = activate_plugin("soha-estimateur/soha-estimateur.php");
  if (is_wp_error($r)) { echo "ACTIVATION REFUSÉE\n"; exit(1); }
' > /dev/null 2>&1

echo "── Rendu ───────────────────────────────────────────────────────────────"
php "$ICI/essai.php"
echo
echo "── Navigateur, avec et sans JavaScript ─────────────────────────────────"
python3 "$ICI/navigateur.py"
