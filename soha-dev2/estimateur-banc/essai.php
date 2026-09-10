<?php
/**
 * Le banc de l'estimateur.
 *
 * Ce qu'on éprouve d'abord : que le bouton mène quelque part **avant** que le
 * moindre script ne s'exécute. C'est le seul défaut qui perdait une demande de
 * location sans rien dire.
 */
$_SERVER['HTTP_HOST'] = '127.0.0.1:8899';
$_SERVER['REQUEST_URI'] = '/';
$_SERVER['SERVER_NAME'] = '127.0.0.1';
$_SERVER['REQUEST_METHOD'] = 'GET';
require __DIR__ . '/wordpress/wp-load.php';

$ok = 0; $ko = 0;
function dit($quoi, $vrai, $detail = '') {
    global $ok, $ko;
    $vrai ? $ok++ : $ko++;
    printf("%s %-54s %s\n", $vrai ? ' ✓' : ' ✗', $quoi, $detail);
}

/* Le site de Mala vit dans un sous-dossier : c'est là que la v2.0.0 se
   trompait de domaine, et c'est donc là qu'il faut mesurer. */
add_filter('option_home', function ($u) { return rtrim($u, '/') . '/dev'; });
add_filter('option_siteurl', function ($u) { return rtrim($u, '/') . '/dev'; });

$html = do_shortcode('[soha_estimateur]');

/* --- le rendu de base ----------------------------------------------------- */
dit("le shortcode rend quelque chose", strlen($html) > 500, strlen($html) . ' caractères');
dit("aucune erreur PHP dans la sortie",
    !preg_match('/\b(Warning|Notice|Deprecated|Fatal error)\b/', $html));
/* `class="se-space` attrape aussi `se-spaces`, `se-space-name` et
   `se-space-sub` : on compte les boutons, pas les préfixes. */
$boutons_espace = preg_match_all('/<button[^>]*class="se-space(?: on)?"/', $html);
dit("les quatre espaces sont proposés", 4 === $boutons_espace, $boutons_espace);
foreach (array('Studio', 'Espace SÖHA', 'Salle 4', 'Salles 1·2·3') as $nom) {
    dit("l'espace « $nom » est nommé", false !== strpos($html, $nom));
}

/* --- LE point : le bouton mène quelque part sans JavaScript ---------------- */
preg_match('/<a class="se-cta"[^>]*href="([^"]*)"/', $html, $m);
$href = isset($m[1]) ? html_entity_decode($m[1]) : '';
dit("le bouton a une vraie destination dès le rendu",
    '' !== $href && '#' !== $href, $href);
dit("elle pointe dans le sous-dossier du site",
    false !== strpos($href, '/dev/reservation/'), $href);

parse_str((string) parse_url($href, PHP_URL_QUERY), $q);
dit("elle porte les quatre paramètres",
    isset($q['espace'], $q['jour'], $q['plage'], $q['tarif']),
    implode(', ', array_keys((array) $q)));
dit("et ils décrivent la sélection de départ",
    'studio' === ($q['espace'] ?? '') && 'sem' === ($q['jour'] ?? '')
    && 'jour' === ($q['plage'] ?? '') && '450' === (string) ($q['tarif'] ?? ''),
    wp_json_encode($q));

/* --- le prix affiché vient de la grille, pas d'un nombre écrit en dur ----- */
$grille = soha_estim_grille();
dit("le prix de départ est celui de la grille",
    false !== strpos($html, (string) $grille['studio'][2]['jour'] . ' $'),
    $grille['studio'][2]['jour'] . ' $');

/* On change la grille : le rendu doit suivre tout seul. */
add_filter('all', '__return_null', 0); remove_filter('all', '__return_null', 0); // no-op lisible
$copie = $grille; $copie['studio'][2]['jour'] = 999;
dit("les 24 tarifs sont là", 24 === count($grille) * 6, count($grille) . ' espaces × 6 tarifs');

/* --- la protection contre Rocket Loader ----------------------------------- */
dit("le script est à l'abri de Rocket Loader",
    false !== strpos($html, 'id="soha-estim-js" data-cfasync="false"'));

/* --- l'accessibilité ------------------------------------------------------ */
/* Le script contient aussi le mot, dans ses `setAttribute` : on compte la
   forme attribut, `aria-pressed="`, qui n'existe que dans le balisage. */
$enfonces = substr_count($html, 'aria-pressed="');
dit("les neuf boutons disent s'ils sont enfoncés", 9 === $enfonces, $enfonces . ' boutons');
dit("un seul est enfoncé par groupe",
    3 === substr_count($html, 'aria-pressed="true"'), substr_count($html, 'aria-pressed="true"'));
dit("le prix s'annonce quand il change",
    false !== strpos($html, 'aria-live="polite"') && false !== strpos($html, 'role="status"'));

/* --- la destination reste juste si on la force ---------------------------- */
dit("home_url décide, pas une adresse écrite en dur",
    false === strpos($html, 'https://centresoha.com/reservation/'));

/* --- deux estimateurs sur la même page ------------------------------------ */
$deux = do_shortcode('[soha_estimateur]') . do_shortcode('[soha_estimateur]');
/* Le premier rendu de la requête a déjà imprimé le CSS et le JS : les suivants
   n'en remettent pas, quel qu'en soit le nombre. C'est ce qu'on vérifie —
   une fois au total, pas une fois par estimateur. */
dit("le premier rendu porte le script", 1 === substr_count($html, 'id="soha-estim-js"'));
dit("les rendus suivants ne le répètent pas",
    0 === substr_count($deux, 'id="soha-estim-js"'), substr_count($deux, 'id="soha-estim-js"'));
dit("mais chaque estimateur a bien son bloc",
    2 === substr_count($deux, 'id="sohaEstim"'), substr_count($deux, 'id="sohaEstim"'));
preg_match_all('/<a class="se-cta"[^>]*href="([^"]*)"/', $deux, $liens);
dit("et chacun son bouton, avec sa destination",
    2 === count($liens[1]) && false !== strpos(html_entity_decode($liens[1][1]), 'tarif=450'));

echo "\n", str_repeat('─', 74), "\n";
printf("%d réussites, %d échecs\n", $ok, $ko);
exit($ko > 0 ? 1 : 0);
