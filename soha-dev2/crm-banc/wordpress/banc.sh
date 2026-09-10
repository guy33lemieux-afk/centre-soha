#!/bin/sh
# Le banc WordPress du CRM.
#
# Chaque suite repart d'un WordPress neuf : un essai qui hérite de la veille ne
# prouve rien. La base SQLite est jetée, WordPress réinstallé, l'extension
# activée dans son propre processus — comme le fait WordPress — puis la suite.
set -e
ICI=$(cd "$(dirname "$0")" && pwd)
W="$ICI/wordpress"

neuf() {
  rm -f "$W/wp-content/database/.ht.sqlite"
  ( cd "$W" && php -r '
    $_SERVER["HTTP_HOST"]="127.0.0.1:8899"; $_SERVER["REQUEST_URI"]="/"; $_SERVER["SERVER_NAME"]="127.0.0.1";
    define("WP_INSTALLING", true);
    require "wp-load.php"; require ABSPATH."wp-admin/includes/upgrade.php";
    wp_install("Centre Soha — banc", "mala", "mala@exemple.test", true, "", "motdepasse");
  ' ) > /dev/null 2>&1
  php "$ICI/activer.php" > /dev/null
}

echo "── Comportement ────────────────────────────────────────────────────────"
neuf; php "$ICI/essai.php"
echo
echo "── Écrans ──────────────────────────────────────────────────────────────"
neuf; php "$ICI/ecrans.php"
echo
echo "── Navigateur, dans WordPress ──────────────────────────────────────────"
neuf; python3 "$ICI/navigateur.py"
