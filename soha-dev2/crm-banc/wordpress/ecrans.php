<?php
/**
 * Les écrans, rendus pour de vrai.
 *
 * Du PHP qui compile peut très bien mourir à l'affichage. On rend donc les
 * trois écrans, on vérifie ce qu'ils contiennent, et surtout qu'ils ne
 * contiennent AUCUN avertissement de PHP — `WP_DEBUG` est allumé, donc toute
 * notice sortirait dans la page.
 */
$_SERVER['HTTP_HOST'] = '127.0.0.1:8899';
$_SERVER['REQUEST_URI'] = '/wp-admin/admin.php?page=soha-crm';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_METHOD'] = 'GET';
define('WP_ADMIN', true);
require __DIR__ . '/wordpress/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/admin.php';
/* Un écran courant, comme dans une vraie requête d'administration : sans lui,
   des crochets de WordPress lui-même tombent. */
set_current_screen('toplevel_page_soha-crm');

$ok = 0; $ko = 0;
function dit($quoi, $vrai, $detail = '') {
    global $ok, $ko;
    $vrai ? $ok++ : $ko++;
    printf("%s %-52s %s\n", $vrai ? ' ✓' : ' ✗', $quoi, $detail);
}
function propre($html) {
    return !preg_match('/\b(Warning|Notice|Deprecated|Fatal error)\b/', $html);
}

wp_set_current_user(get_user_by('login', 'mala')->ID);

/* --- une demande à afficher ------------------------------------------------ */
class Faux_Record {
    private $c; private $r;
    public function __construct($c, $n) { $this->c = $c; $this->r = array('form_name' => $n); }
    public function get($q) { return 'fields' === $q ? $this->c : ('form_settings' === $q ? $this->r : null); }
}
do_action('elementor_pro/forms/new_record', new Faux_Record(array(
    'n' => array('title' => 'Nom',      'type' => 'text',  'value' => 'Rosalie <b>Gagné</b>'),
    'c' => array('title' => 'Courriel', 'type' => 'email', 'value' => 'rosalie@exemple.test'),
    'm' => array('title' => 'Message',  'type' => 'textarea', 'value' => "Deux lignes\net des « guillemets »."),
), 'Demande de location'), null);

/* --- le répertoire --------------------------------------------------------- */
ob_start(); soha_crm_ecran(); $html = ob_get_clean();
dit("l'écran du répertoire se rend", propre($html) && false !== strpos($html, 'id="soha-crm-racine"'));

/* les fichiers chargés sur cet écran */
do_action('admin_enqueue_scripts', 'toplevel_page_soha-crm');
dit("crm.js est mis en file", wp_script_is('soha-crm', 'enqueued'));
dit("l'adaptateur passe AVANT crm.js",
    in_array('soha-crm-adaptateur', wp_scripts()->registered['soha-crm']->deps, true));
dit("React vient de wp-element",
    in_array('wp-element', wp_scripts()->registered['soha-crm']->deps, true));
dit("les polices sont mises en file", wp_style_is('soha-crm-polices', 'enqueued'));
$donnees = (string) wp_scripts()->get_data('soha-crm-adaptateur', 'data');
/* `wp_json_encode` échappe les barres obliques : on cherche donc la forme
   telle qu'elle arrive dans la page, pas telle qu'on l'a écrite. */
preg_match('/=\s*(\{.*\})\s*;/s', $donnees, $m);
$decode = isset($m[1]) ? (array) json_decode($m[1], true) : array();
dit("l'adresse REST et le jeton sont passés",
    !empty($decode['racine']) && false !== strpos($decode['racine'], 'soha-crm/v1/etat')
    && !empty($decode['jeton']),
    isset($decode['racine']) ? $decode['racine'] : '');
dit("l'adaptateur sait ajouter son jeton à cette adresse",
    !empty($decode['racine']) && false !== strpos($decode['racine'], '?'),
    'permaliens simples : ?rest_route=… — l\'adaptateur ajoute &_wpnonce');

/* rien ne doit se charger ailleurs dans l'administration */
wp_dequeue_script('soha-crm'); wp_deregister_script('soha-crm');
wp_dequeue_style('soha-crm-polices'); wp_deregister_style('soha-crm-polices');
do_action('admin_enqueue_scripts', 'index.php');
dit("rien ne se charge sur les autres écrans", !wp_script_is('soha-crm', 'enqueued'));

/* --- les demandes ---------------------------------------------------------- */
ob_start(); soha_crm_ecran_demandes(); $html = ob_get_clean();
dit("l'écran des demandes se rend", propre($html));
dit("la demande y apparaît", false !== strpos($html, 'rosalie@exemple.test'));
dit("le nom est échappé (pas de HTML injecté)",
    false === strpos($html, 'Rosalie <b>Gagné</b>')
    && false !== strpos($html, 'Rosalie &lt;b&gt;Gagn'));
dit("les trois gestes sont offerts",
    false !== strpos($html, 'value="verser"') && false !== strpos($html, 'value="traiter"')
    && false !== strpos($html, 'value="supprimer"'));
dit("la conservation est annoncée", false !== strpos($html, '24 mois'));
dit("l'export CSV est offert", false !== strpos($html, 'soha_crm_export'));

/* --- les accès ------------------------------------------------------------- */
ob_start(); soha_crm_ecran_acces(); $html = ob_get_clean();
dit("l'écran des accès se rend", propre($html));
dit("il liste les comptes", false !== strpos($html, 'name="acces[]"'));
dit("la ligne d'une administratrice est verrouillée", false !== strpos($html, 'disabled'));
dit("il porte un jeton de sécurité", false !== strpos($html, 'soha_crm_acces_jeton'));

/* --- le menu --------------------------------------------------------------- */
$GLOBALS['menu'] = array(); $GLOBALS['submenu'] = array();
do_action('admin_menu');
$pages = array();
foreach ((array) $GLOBALS['submenu']['soha-crm'] as $e) { $pages[] = $e[2]; }
dit("les trois écrans sont au menu",
    in_array('soha-crm', $pages, true) && in_array('soha-crm-demandes', $pages, true)
    && in_array('soha-crm-acces', $pages, true), implode(' · ', $pages));
$avec_pastille = implode('', array_map(function ($e) { return $e[0]; }, $GLOBALS['submenu']['soha-crm']));
dit("la demande en attente porte une pastille", false !== strpos($avec_pastille, 'plugin-count'));

echo "\n", str_repeat('─', 72), "\n";
printf("%d réussites, %d échecs\n", $ok, $ko);
exit($ko > 0 ? 1 : 0);
