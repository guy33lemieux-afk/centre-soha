<?php
/**
 * Le banc du contrôle après import.
 *
 * On fabrique les quatre défauts pour de vrai — de vraies pièces jointes, de
 * vraies données Elementor — puis on demande à l'écran ce qu'il voit. Un
 * contrôle qu'on n'a jamais vu trouver quelque chose ne protège de rien.
 */
$_SERVER['HTTP_HOST'] = '127.0.0.1:8899';
$_SERVER['REQUEST_URI'] = '/wp-admin/';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_METHOD'] = 'GET';
define('WP_ADMIN', true);
require __DIR__ . '/wordpress/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/admin.php';
set_current_screen('tools_page_soha-controle');

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

/* Le site de Mala est installé dans un sous-dossier, `/dev`. Le banc, lui, est
   à la racine. On lui fait donc croire qu'il est dans `/dev` — sinon on
   éprouverait le seul cas où le contrôle des liens ne s'applique pas.

   On filtre l'option, pas `home_url` : ce filtre-là reçoit l'adresse complète,
   chemin compris, et y ajouter « /dev » donnerait
   « …/wp-content/uploads/x.webp/dev/ ». C'est la première version de ce banc,
   et elle rendait le contrôle des images aveugle pour de mauvaises raisons. */
add_filter('option_home', function ($url) { return rtrim($url, '/') . '/dev'; });
add_filter('option_siteurl', function ($url) { return rtrim($url, '/') . '/dev'; });
dit("le banc simule bien une installation dans un sous-dossier",
    '/dev' === soha_controle_prefixe(), soha_controle_prefixe());

/* --- au départ, un site sain --------------------------------------------- */
dit("sur un site vide, aucun doublon", array() === soha_controle_doublons());
dit("aucune image absente", array() === soha_controle_images_absentes());
dit("aucun formulaire muet", array() === soha_controle_formulaires());
dit("aucun lien hors du site", array() === soha_controle_liens());

ob_start(); soha_controle_ecran(); $html = ob_get_clean();
dit("l'écran se rend et le dit", propre($html) && false !== strpos($html, 'Rien à signaler'));

/* --- 1 · on fabrique le doublon exact que le site a subi ------------------ */
function piece_jointe($chemin) {
    $id = wp_insert_post(array('post_type' => 'attachment', 'post_status' => 'inherit',
                               'post_title' => basename($chemin), 'post_mime_type' => 'image/webp'));
    update_post_meta($id, '_wp_attached_file', $chemin);
    return $id;
}
piece_jointe('2026/09/soha-accueil-001.webp');
$copie = piece_jointe('2026/09/soha-accueil-001-1.webp');
piece_jointe('2026/09/soha-studio-podcast-056.webp');   // un nom qui finit par un chiffre
piece_jointe('2026/09/soha-serie-2.webp');              // seul : PAS un doublon

$d = soha_controle_doublons();
dit("le doublon est vu", 1 === count($d), count($d) . ' trouvé(s)');
dit("c'est la copie qui est nommée, pas l'originale",
    $d && '2026/09/soha-accueil-001-1.webp' === $d[0]['copie']);
dit("un nom qui finit par un chiffre n'est pas un doublon",
    !in_array('2026/09/soha-studio-podcast-056.webp', array_column($d, 'copie'), true));
dit("un « -2 » sans jumeau n'est pas un doublon",
    !in_array('2026/09/soha-serie-2.webp', array_column($d, 'copie'), true));

/* --- 2 · une page qui demande une image qui n'existe pas ------------------ */
$page = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
                             'post_title' => 'Accueil'));
$arbre = array(array(
    'id' => 'a1', 'elType' => 'container', 'elements' => array(
        array('id' => 'b1', 'elType' => 'widget', 'widgetType' => 'image',
              'settings' => array('image' => array(
                  'url' => home_url('/wp-content/uploads/2026/09/soha-accueil-001.webp')))),
        array('id' => 'b2', 'elType' => 'widget', 'widgetType' => 'image',
              'settings' => array('image' => array(
                  'url' => home_url('/wp-content/uploads/2026/09/soha-fantome.webp')))),
    ),
));
update_post_meta($page, '_elementor_data', wp_slash(wp_json_encode($arbre)));

$refs = soha_controle_images_referencees();
dit("les images de la page sont retrouvées", 2 === count($refs), count($refs) . ' référencée(s)');
$abs = soha_controle_images_absentes();
dit("seule l'absente est signalée",
    array('2026/09/soha-fantome.webp') === $abs, implode(', ', $abs));

/* --- 3 · un formulaire sans destinataire, et un avec -------------------- */
$contact = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
                                'post_title' => 'Contact'));
$arbre = array(array(
    'id' => 'c1', 'elType' => 'container', 'elements' => array(
        array('id' => 'f1', 'elType' => 'widget', 'widgetType' => 'form',
              'settings' => array('form_name' => 'Demande de location',
                                  'submit_actions' => array('email'), 'email_to' => '')),
        array('id' => 'f2', 'elType' => 'widget', 'widgetType' => 'form',
              'settings' => array('form_name' => 'Contact',
                                  'submit_actions' => array('email'),
                                  'email_to' => 'info@centresoha.com')),
        array('id' => 'f3', 'elType' => 'widget', 'widgetType' => 'form',
              'settings' => array('form_name' => 'Infolettre seule',
                                  'submit_actions' => array('mailchimp'))),
    ),
));
update_post_meta($contact, '_elementor_data', wp_slash(wp_json_encode($arbre)));

$m = soha_controle_formulaires();
dit("le formulaire sans destinataire est vu", 1 === count($m), count($m) . ' trouvé(s)');
dit("c'est le bon qui est nommé", $m && 'Demande de location' === $m[0]['nom'],
    $m ? $m[0]['nom'] : '');
dit("un formulaire qui n'envoie pas de courriel est laissé tranquille",
    !in_array('Infolettre seule', array_column($m, 'nom'), true));

/* --- 4 · les liens vers le mauvais préfixe ------------------------------- */
dit("le préfixe du site est lu", '/dev' === soha_controle_prefixe(), soha_controle_prefixe());

$menu = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
                             'post_title' => 'Menu'));
$arbre = array(array(
    'id' => 'm1', 'elType' => 'container',
    'settings' => array('link' => array('url' => '/dev2/contact/')),
    'elements' => array(
        array('id' => 'n1', 'elType' => 'widget', 'widgetType' => 'button',
              'settings' => array('link' => array('url' => '/dev2/se-ressourcer/'))),
        array('id' => 'n2', 'elType' => 'widget', 'widgetType' => 'button',
              'settings' => array('link' => array('url' => '/dev/contact/'))),
        array('id' => 'n3', 'elType' => 'widget', 'widgetType' => 'image',
              'settings' => array('image' => array('url' => '/wp-content/uploads/x.webp'))),
        /* Un lien hors du site, mais qui ressemble : il doit être vu. */
        array('id' => 'n4', 'elType' => 'widget', 'widgetType' => 'button',
              'settings' => array('link' => array('url' => 'https://exemple.test/'))),
    ),
));
update_post_meta($menu, '_elementor_data', wp_slash(wp_json_encode($arbre)));

$l = soha_controle_liens();
$adresses = array_column($l, 'lien');
sort($adresses);
dit("les liens vers /dev2/ sont vus",
    array('/dev2/contact/', '/dev2/se-ressourcer/') === $adresses, implode(' · ', $adresses));
dit("un lien correct est laissé tranquille", !in_array('/dev/contact/', $adresses, true));
dit("wp-content n'est pas un lien de page", !in_array('/wp-content/uploads/x.webp', $adresses, true));
dit("une adresse complète vers ailleurs n'est pas concernée",
    !in_array('https://exemple.test/', $adresses, true));

/* --- l'écran, avec les quatre défauts ------------------------------------ */
ob_start(); soha_controle_ecran(); $html = ob_get_clean();
dit("l'écran se rend avec les quatre défauts", propre($html));
dit("il annonce qu'il y a des points à regarder",
    false !== strpos($html, 'points à regarder'));
dit("il montre le doublon", false !== strpos($html, 'soha-accueil-001-1.webp'));
dit("il montre l'image absente", false !== strpos($html, 'soha-fantome.webp'));
dit("il nomme le formulaire muet", false !== strpos($html, 'Demande de location'));
dit("il montre le lien fautif", false !== strpos($html, '/dev2/contact/'));
dit("il rappelle le chemin du site", false !== strpos($html, 'Ce site est installé dans'));

/* --- les scripts sont à l'abri de Rocket Loader --------------------------- */
/*
 * Le site est servi derrière Cloudflare, Rocket Loader actif : il diffère et
 * réordonne les scripts de la page. Nos quatre scripts touchent au DOM tout de
 * suite. `data-cfasync="false"` est la façon documentée de lui dire de ne pas y
 * toucher — encore faut-il qu'il soit vraiment sur chacun.
 */
wp_set_current_user(0);
wp_set_current_user(get_user_by('login', 'mala')->ID);

/* Déclencher `wp_footer` hors d'un vrai rendu de page fait râler WordPress
   lui-même (`the_block_template_skip_link`, obsolète depuis 6.4). C'est son
   avertissement, pas le nôtre : on ne le confond pas avec un défaut de
   l'extension. */
ob_start(); do_action('wp_footer'); $pied = ob_get_clean();
ob_start(); do_action('wp_head'); $tete = ob_get_clean();
$sortie = $tete . $pied;

$scripts = preg_match_all('/<script\b([^>]*)>/i', $sortie, $m) ? $m[1] : array();
$nos = array();
foreach ($scripts as $attributs) {
    if (false !== strpos($attributs, 'soha-')) {
        $nos[] = $attributs;
    }
}
dit("nos scripts sont bien posés dans la page", count($nos) >= 3, count($nos) . ' script(s)');
$sans = array_filter($nos, function ($a) { return false === strpos($a, 'data-cfasync="false"'); });
dit("chacun porte data-cfasync=\"false\"", 0 === count($sans),
    $sans ? implode(' | ', $sans) : 'tous protégés');

/* --- l'écran est au menu, et réservé ------------------------------------- */
$GLOBALS['menu'] = array(); $GLOBALS['submenu'] = array();
do_action('admin_menu');
$sous = array();
foreach ((array) ($GLOBALS['submenu']['tools.php'] ?? array()) as $e) { $sous[] = $e[2]; }
dit("l'écran est dans Outils", in_array('soha-controle', $sous, true), implode(' · ', $sous));

$abonne = wp_insert_user(array('user_login' => 'passante', 'user_pass' => wp_generate_password(),
                               'user_email' => 'p@exemple.test', 'role' => 'subscriber'));
wp_set_current_user(0); wp_set_current_user($abonne);
dit("un abonné n'y a pas accès", !current_user_can('manage_options'));

echo "\n", str_repeat('─', 72), "\n";
printf("%d réussites, %d échecs\n", $ok, $ko);
exit($ko > 0 ? 1 : 0);
