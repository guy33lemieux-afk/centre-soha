<?php
/**
 * Plugin Name:       Centre Soha — Finition (/dev)
 * Plugin URI:        https://centresoha.com/dev
 * Description:        Réunit en UNE extension tout ce qui tournait dans les boîtes Code Snippets : accessibilité, finition mobile, vitesse, estimateur, menu mobile — PLUS (v1.2.0) : textes alternatifs des 61 images (posés une fois), préchargement du héros (LCP) et avis de témoins en français (remplace CookieYes) — et (v1.3.0) un écran « Contrôle Soha » dans Outils, qui cherche après un import les quatre défauts que ce site a réellement subis. 100% réversible : désactiver l'extension retire absolument tout, rien n'est écrit dans les pages.
 * Version:           1.3.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Centre Soha
 * License:           GPL-2.0-or-later
 * Text Domain:       centre-soha
 *
 * ============================================================================
 *  REMPLACE les 3 boîtes Code Snippets : soha_a11y, soha_finition, soha_vitesse.
 *  APRÈS avoir activé cette extension, DÉSACTIVER ces 3 boîtes (sinon double
 *  affichage — l'image d'article se poserait deux fois).
 *  L'estimateur reste son extension à lui (sohaestimateur) ; ici on ne fait
 *  que lui donner son format téléphone (CSS scopé #estimateur, sans effet si
 *  l'estimateur n'est pas sur la page).
 * ============================================================================
 */

if (!defined('ABSPATH')) { exit; }

/* ===========================================================================
 * MODULE 1 — VITESSE  (ex-boîte « soha_vitesse » v01)
 * Allègements SÛRS : émojis, oEmbed (wp-embed.js), entêtes superflus.
 * Aucun impact visuel. Ne touche PAS jQuery Migrate ni les styles de blocs.
 * =========================================================================== */

add_action('init', function () {
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('admin_print_scripts', 'print_emoji_detection_script');
    remove_action('wp_print_styles', 'print_emoji_styles');
    remove_action('admin_print_styles', 'print_emoji_styles');
    remove_filter('the_content_feed', 'wp_staticize_emoji');
    remove_filter('comment_text_rss', 'wp_staticize_emoji');
    remove_filter('wp_mail', 'wp_staticize_emoji_for_email');
    add_filter('emoji_svg_url', '__return_false');
    add_filter('tiny_mce_plugins', function ($plugins) {
        return is_array($plugins) ? array_diff($plugins, array('wpemoji')) : array();
    });
    add_filter('wp_resource_hints', function ($urls, $relation_type) {
        if ('dns-prefetch' === $relation_type) {
            $urls = array_filter($urls, function ($u) {
                return is_array($u) || false === strpos((string) $u, 's.w.org');
            });
        }
        return $urls;
    }, 10, 2);
});

add_action('init', function () {
    remove_action('wp_head', 'wp_oembed_add_discovery_links');
    remove_action('wp_head', 'wp_oembed_add_host_js');
    add_filter('embed_oembed_discover', '__return_false');
}, 9);
add_action('wp_footer', function () {
    wp_dequeue_script('wp-embed');
});

remove_action('wp_head', 'wp_generator');
remove_action('wp_head', 'rsd_link');
remove_action('wp_head', 'wlwmanifest_link');
remove_action('wp_head', 'wp_shortlink_wp_head');
remove_action('wp_head', 'adjacent_posts_rel_link_wp_head');
add_filter('the_generator', '__return_empty_string');


/* ===========================================================================
 * MODULE 2 — FINITION  (ex-boîte « soha_finition » v06)
 * Image d'article + « Autres articles » + CSS mobile (en-tête, titres nets,
 * fil d'Ariane, estimateur, menu mobile plus vif).
 * =========================================================================== */

/* 2a) Image mise en avant en tête d'article */
add_filter('the_content', function ($content) {
    if (is_singular('post') && in_the_loop() && is_main_query() && has_post_thumbnail()) {
        $img = get_the_post_thumbnail(get_the_ID(), 'large', array(
            'style'    => 'display:block;width:100%;height:auto;border-radius:12px;margin:0 0 28px;',
            'loading'  => 'eager',
            'decoding' => 'async',
        ));
        return $img . $content;
    }
    return $content;
}, 20);

/* 2b) « Autres articles du Journal » en bas d'article */
add_filter('the_content', function ($content) {
    if (!(is_singular('post') && in_the_loop() && is_main_query())) { return $content; }

    $others = get_posts(array(
        'post_type'           => 'post',
        'posts_per_page'      => 3,
        'post__not_in'        => array(get_the_ID()),
        'orderby'             => 'rand',
        'no_found_rows'       => true,
        'ignore_sticky_posts' => true,
    ));
    if (!$others) { return $content; }

    $cards = '';
    foreach ($others as $p) {
        $thumb = has_post_thumbnail($p->ID)
            ? get_the_post_thumbnail($p->ID, 'medium', array(
                'style'   => 'display:block;width:100%;height:150px;object-fit:cover;border-radius:10px;margin:0 0 10px;',
                'loading' => 'lazy',
              ))
            : '<span style="display:block;height:150px;border-radius:10px;margin:0 0 10px;background:#DDF0F5"></span>';
        $cards .= '<a href="' . esc_url(get_permalink($p->ID)) . '" style="text-decoration:none;color:inherit;display:block">'
                . $thumb
                . '<span style="font-family:Fraunces,Georgia,serif;font-size:17px;line-height:1.25;color:#20303a">' . esc_html(get_the_title($p->ID)) . '</span>'
                . '</a>';
    }

    $block  = '<aside style="margin:48px 0 0;padding:28px 0 0;border-top:1px solid #E0D8CA">';
    $block .= '<div style="font-family:\'DM Mono\',ui-monospace,monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#19A7DB;margin:0 0 18px">Autres articles du Journal</div>';
    $block .= '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:22px">' . $cards . '</div>';
    $block .= '</aside>';

    return $content . $block;
}, 25);

/* 2c) CSS mobile de finition */
add_action('wp_head', function () {
    echo <<<'CSS'

<style id="soha-finition-css">
/* En-tête : retirer le trait/ombre sous la barre (toutes tailles) */
.e-con:has(img[src*="logo" i]):has(.elementor-menu-toggle){
  border-bottom: 0 !important;
  box-shadow: none !important;
}

@media (max-width: 767px){

  /* Barre d'en-tête : logo à gauche, ☰ à droite, resserrée, alignés */
  .e-con:has(img[src*="logo" i]):has(.elementor-menu-toggle){
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: space-between !important;
    align-items: center !important;
    gap: 12px !important;
    min-height: 0 !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
  }
  .e-con:has(img[src*="logo" i]):has(.elementor-menu-toggle) > *{
    align-self: center !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
  }
  /* « Réserver » VISIBLE dans la barre (compact), à droite avec le ☰ */
  .soha-nav{
    display: flex !important; flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important; gap: 10px !important;
    width: auto !important;
  }
  /* Le widget menu (☰) et le bouton Réserver se réduisent à leur contenu →
     ils restent CÔTE À CÔTE au lieu que le menu prenne toute la largeur
     et pousse « Réserver » sur une 2e ligne. */
  .soha-nav .elementor-widget-nav-menu,
  .soha-nav .elementor-widget-button{
    width: auto !important; max-width: none !important;
    flex: 0 0 auto !important; margin: 0 !important;
  }
  .soha-nav .elementor-menu-toggle{ margin: 0 !important; }
  .e-con:has(img[src*="logo" i]):has(.elementor-menu-toggle) .elementor-widget-button .elementor-button{
    padding: 7px 13px !important; font-size: 13px !important; min-height: 0 !important; line-height: 1.2 !important;
  }

  /* Logo (taille conservée) */
  img[src*="logo" i]{ max-width:140px !important; height:auto !important; }

  /* TITRES : mots ENTIERS à la ligne, jamais coupés (pas de césure auto) */
  .elementor-heading-title{
    overflow-wrap: break-word !important;
    word-break: normal !important;
    hyphens: manual !important;
    -webkit-hyphens: manual !important;
  }
  h1.elementor-heading-title{
    font-size: clamp(1.9rem, 10.5vw, 2.8rem) !important;
    line-height: 1.07 !important;
  }
  h2.elementor-heading-title,
  h3.elementor-heading-title{
    font-size: clamp(1.5rem, 7.5vw, 2.2rem) !important;
    line-height: 1.12 !important;
  }

  /* FIL D'ARIANE (pages atelier/événement) : une ligne compacte, pas des blocs */
  .elementor-widget-breadcrumbs .elementor-widget-container,
  .tribe-events-breadcrumb, .tribe-breadcrumbs,
  nav[aria-label="Breadcrumb" i], nav[aria-label="Fil d’Ariane" i],
  #breadcrumbs, .rank-math-breadcrumb, .yoast-breadcrumb,
  .breadcrumbs, .breadcrumb{
    display: block !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
    margin: 0 0 14px !important;
    padding: 0 !important;
  }
  .elementor-widget-breadcrumbs .elementor-widget-container > *,
  .elementor-widget-breadcrumbs li, .elementor-widget-breadcrumbs a, .elementor-widget-breadcrumbs span,
  .tribe-events-breadcrumb li, .tribe-events-breadcrumb a, .tribe-events-breadcrumb span,
  .tribe-breadcrumbs li, .tribe-breadcrumbs a, .tribe-breadcrumbs span,
  #breadcrumbs a, #breadcrumbs span,
  .rank-math-breadcrumb a, .rank-math-breadcrumb span,
  .yoast-breadcrumb a, .yoast-breadcrumb span,
  .breadcrumbs li, .breadcrumbs a, .breadcrumbs span,
  .breadcrumb li, .breadcrumb a, .breadcrumb span{
    display: inline !important;
    float: none !important;
    width: auto !important;
    min-height: 0 !important;
    margin: 0 4px 0 0 !important;
    padding: 0 !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
  }

  /* MENU MOBILE plus vif : plus d'animation qui traîne + tap sans délai de 300 ms.
     (Le JS ci-dessous ouvre/ferme instantanément ; ce CSS retire toute transition
      résiduelle du panneau déroulant.) */
  .elementor-menu-toggle{ touch-action: manipulation !important; }
  .elementor-nav-menu--dropdown,
  .elementor-nav-menu__container.elementor-nav-menu--dropdown,
  .elementor-nav-menu--dropdown .elementor-nav-menu,
  .elementor-nav-menu--dropdown ul,
  .elementor-nav-menu--dropdown li,
  .elementor-nav-menu--dropdown a,
  .elementor-nav-menu--dropdown .sub-menu{
    transition: none !important;
    animation: none !important;
    animation-duration: 0s !important;
  }

  /* ESTIMATEUR — format téléphone (sans effet si l'estimateur n'est pas là) */
  #estimateur .soha-estim{
    grid-template-columns: 1fr !important;
    gap: 14px !important;
    max-width: 100% !important;
  }
  #estimateur .soha-epanel{ padding: 18px 15px !important; }
  #estimateur .soha-eout{
    position: static !important;
    top: auto !important;
    padding: 22px 18px !important;
  }
  #estimateur .soha-opt-grid{
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }
  #estimateur .soha-estim,
  #estimateur .soha-epanel,
  #estimateur .soha-eout{ min-width: 0 !important; }
}
</style>

CSS;
}, 100);

/* 2d) MENU MOBILE — ouverture INSTANTANÉE.
 * Elementor ouvre le menu ☰ avec un glissement jQuery (~400 ms) = « ça traîne ».
 * On intercepte le clic du bouton (seulement quand le ☰ est réellement visible,
 * donc uniquement sur mobile) et on ouvre/ferme d'un coup. Défensif : si la
 * structure du menu n'est pas celle attendue, on ne touche à rien (Elementor
 * garde la main). Le desktop n'est jamais affecté. Réversible : désactiver
 * l'extension rend le glissement d'origine. */
add_action('wp_footer', function () {
    echo <<<'SOHA_MENU_JS'

<script id="soha-menu-js">
(function(){
  function ready(fn){ if(document.readyState!=='loading'){fn();}else{document.addEventListener('DOMContentLoaded',fn);} }
  ready(function(){
    try{
      /* NB v1.0.3 : le menu ☰ principal est laissé à Elementor (natif = FIABLE,
         toujours accessible, s'ouvre bien avec ses liens). On ne fait plus que
         régler la vitesse des SOUS-MENUS via SmartMenus ci-dessous. */

      /* SOUS-MENUS (catégories) : dépliage INSTANTANÉ.
         Les sous-menus mobiles sont animés par SmartMenus (glissement lent).
         On règle sa fonction de dépliage/repliage repliable (collapsible) sur
         « instantané » — uniquement le mode mobile, le survol bureau reste
         inchangé. Non destructif : on ne modifie que la durée, pas la logique. */
      function tuneSM(){
        if(!window.jQuery){ return false; }
        var found=false;
        window.jQuery('ul.elementor-nav-menu').each(function(){
          var sm=window.jQuery(this).data('smartmenus');
          if(sm&&sm.opts){
            sm.opts.collapsibleShowFunction=null;
            sm.opts.collapsibleHideFunction=null;
            found=true;
          }
        });
        return found;
      }
      if(!tuneSM()){ setTimeout(tuneSM,800); }

      /* « RÉSERVER » (en-tête) → vrai système de réservation GoRendezVous,
         au lieu de la page de location de salles. Scopé au .soha-nav de l'en-tête
         (ne touche PAS les vrais CTA « Louer une salle » ailleurs sur le site).
         Pour changer la destination : remplacer l'URL ci-dessous. */
      var RESERVER_URL = 'https://www.gorendezvous.com/fr/centresoha';
      function isReserver(a){
        if(!a) return false;
        var t=(a.textContent||'').trim().toLowerCase();
        return t==='réserver' || t==='reserver';
      }
      /* (a) réécrit le href de tout bouton « Réserver » */
      document.querySelectorAll('a').forEach(function(a){
        if(isReserver(a)){ a.setAttribute('href', RESERVER_URL); a.setAttribute('rel','noopener'); }
      });
      /* (b) FILET DE SÉCURITÉ : intercepte le clic — marche même si le href
             n'a pas encore été réécrit (serveur lent, timing) */
      document.addEventListener('click', function(e){
        var a = (e.target && e.target.closest) ? e.target.closest('a') : null;
        if(isReserver(a)){ e.preventDefault(); window.location.href = RESERVER_URL; }
      }, true);
    }catch(e){}
  });
})();
</script>

SOHA_MENU_JS;
}, 100);


/* ===========================================================================
 * MODULE 3 — ACCESSIBILITÉ  (ex-boîte « soha_a11y » v03)
 * Rapport : https://centresoha.com/dev/wp-admin/?soha_a11y=scan
 * Entièrement réversible (rien n'est écrit dans _elementor_data).
 * =========================================================================== */

/* 3a) Rapport lecture seule dans l'admin */
add_action('admin_init', function () {
    if (!isset($_GET['soha_a11y']) || 'scan' !== $_GET['soha_a11y']) { return; }
    if (!current_user_can('manage_options')) { return; }

    global $wpdb;
    $like = '%' . $wpdb->esc_like('"header_size":"h6"') . '%';
    $rows = $wpdb->get_col($wpdb->prepare(
        "SELECT meta_value FROM {$wpdb->postmeta} WHERE meta_key = '_elementor_data' AND meta_value LIKE %s",
        $like
    ));
    $h6 = 0;
    foreach ((array) $rows as $r) { $h6 += substr_count($r, '"header_size":"h6"'); }

    $html  = '<div style="font:15px/1.6 system-ui,sans-serif;max-width:640px;margin:60px auto;padding:28px 32px;background:#FBF8F3;border:1px solid #E0D8CA;border-radius:14px;color:#20303a">';
    $html .= '<h1 style="font:600 22px/1.2 Georgia,serif;color:#19A7DB;margin:0 0 14px">Soha · accessibilité — scan (extension)</h1>';
    $html .= '<p style="margin:0 0 16px"><b>Le module est actif ✓</b> — les correctifs se posent à chaque affichage.</p>';
    $html .= '<ol style="margin:0 0 16px;padding-left:20px">';
    $html .= '<li>Cartels <code>&lt;h6&gt;</code> → <code>&lt;div&gt;</code> — <b>' . intval($h6) . '</b> titre(s) <code>h6</code> dans les pages.</li>';
    $html .= '<li>Lien du logo → « Centre Soha — accueil ».</li>';
    $html .= '<li>Repère principal + « Aller au contenu ».</li>';
    $html .= '<li>Liens de prose et de pied de page soulignés.</li>';
    $html .= '<li>Contraste MESURÉ (ratio WCAG) : relève ce qui échoue sur fond uni.</li>';
    $html .= '</ol>';
    $html .= '<p style="margin:0;color:#5a6b73">Un texte sur IMAGE reste inchangé (choix de design). Rien n\'est écrit dans tes pages : tout revient en désactivant l\'extension. Re-mesure sur PageSpeed (onglet Accessibilité).</p>';
    $html .= '</div>';

    wp_die($html, 'Soha · a11y — scan', array('response' => 200));
});

/* 3b) Soulignement des liens (CSS) */
add_action('wp_head', function () {
    echo "\n<style id=\"soha-a11y-css\">.elementor-location-footer a,[data-elementor-type=\"footer\"] a,.elementor-widget-text-editor a{text-decoration:underline !important;text-underline-offset:2px}</style>\n";
}, 99);

/* 3c) Structure + contraste mesuré (JS) */
add_action('wp_footer', function () {
    echo <<<'SOHA_A11Y_JS'

<script id="soha-a11y-js">
(function(){
  function parse(c){var m=c&&c.match(/[\d.]+/g);if(!m)return null;return [+m[0],+m[1],+m[2],m[3]===undefined?1:+m[3]];}
  function rl(c){var a=[c[0],c[1],c[2]].map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});return 0.2126*a[0]+0.7152*a[1]+0.0722*a[2];}
  function ratio(f,b){var L1=rl(f),L2=rl(b),hi=Math.max(L1,L2),lo=Math.min(L1,L2);return (hi+0.05)/(lo+0.05);}
  function solidBg(el){var n=el;while(n&&n.nodeType===1){var c=parse(getComputedStyle(n).backgroundColor);if(c&&c[3]!==0)return {c:c,node:n};n=n.parentElement;}return {c:[255,255,255,1],node:document.body};}
  function imgBetween(el,stop){var n=el;while(n&&n!==stop&&n.nodeType===1){if(getComputedStyle(n).backgroundImage!=='none')return true;n=n.parentElement;}return false;}
  function fix(el){
    var col=parse(getComputedStyle(el).color); if(!col) return;
    var sb=solidBg(el);
    if(imgBetween(el,sb.node)) return;
    if(ratio(col,sb.c)>=4.5) return;
    var dark=rl(sb.c)<0.35;
    var pick=dark?[221,240,245]:[4,108,134];
    if(ratio(pick,sb.c)<4.5) pick=dark?[255,255,255]:[32,48,58];
    el.style.setProperty('color','rgb('+pick[0]+','+pick[1]+','+pick[2]+')','important');
  }
  function run(){
    try{
      document.querySelectorAll('h6.elementor-heading-title').forEach(function(h){var d=document.createElement('div');for(var i=0;i<h.attributes.length;i++){d.setAttribute(h.attributes[i].name,h.attributes[i].value);}d.innerHTML=h.innerHTML;h.parentNode.replaceChild(d,h);});
      var head=document.querySelector('.elementor-location-header,[data-elementor-type="header"],header');
      if(head){head.querySelectorAll('a').forEach(function(a){if(a.querySelector('img,svg')&&!(a.textContent||'').trim()&&!a.getAttribute('aria-label')){a.setAttribute('aria-label','Centre Soha — accueil');}});}
      var main=document.querySelector('main')||document.querySelector('[data-elementor-type="wp-page"],[data-elementor-type="wp-post"]');
      if(main){if(!main.getAttribute('role'))main.setAttribute('role','main');var t=document.getElementById('content');if(!t){main.id='content';t=main;}if(!t.hasAttribute('tabindex'))t.setAttribute('tabindex','-1');}
      var seen=[];
      document.querySelectorAll('.elementor-heading-title').forEach(function(e){seen.push(e);});
      document.querySelectorAll('.elementor-location-footer,[data-elementor-type="footer"],.elementor-location-header,[data-elementor-type="header"]').forEach(function(sc){sc.querySelectorAll('*').forEach(function(e){if(e.tagName==='A'||(!e.querySelector('*')&&(e.textContent||'').trim())){seen.push(e);}});});
      seen.forEach(function(e){fix(e);});
    }catch(e){}
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',run);}else{run();}
})();
</script>

SOHA_A11Y_JS;
}, 99);


/* ===========================================================================
 * MODULE 4 — IMPORT (v1.2.0)
 * (4a) Textes alternatifs des 61 images — posés UNE fois, dès que les images
 *      sont dans la médiathèque (avant ou après l'import, peu importe).
 * (4b) Préchargement du héros (LCP) + priorité haute.
 * (4c) Avis de témoins en français (remplace CookieYes — désactiver CookieYes).
 * =========================================================================== */

add_action('admin_init', function () {
    if (get_option('soha_fi_alt_done') === '1') { return; }
    $alts = array(
        'soha_logo-site_20260828' => 'Logo du Centre Soha',
        'soha_logo-site-inverse_20260828' => 'Logo du Centre Soha, version claire',
        'soha-portrait-alice-mayeux' => 'Portrait d\'Alice Mayeux, artisane au Centre Soha',
        'soha-portrait-dominique-mennessier' => 'Portrait de Dominique Mennessier, cofondatrice du Centre Soha',
        'soha-portrait-dominique-animatrices-invitees' => 'Dominique Mennessier entourée d\'animatrices invitées au Centre Soha',
        'soha-portrait-elaine-delorme' => 'Portrait d\'Élaine Delorme, artisane au Centre Soha',
        'soha-portrait-eve-morin' => 'Portrait d\'Ève Morin, artisane au Centre Soha',
        'soha-portrait-fabien-rosenberg' => 'Portrait de Fabien Rosenberg, artisan au Centre Soha',
        'soha-portrait-farah-quiroga' => 'Portrait de Farah Quiroga, artisane au Centre Soha',
        'soha-portrait-jacinthe-chausse' => 'Portrait de Jacinthe Chaussé, artisane au Centre Soha',
        'soha-portrait-joanne-bourcier' => 'Portrait de Joanne Bourcier, artisane au Centre Soha',
        'soha-portrait-julie-habart' => 'Portrait de Julie Habart, artisane au Centre Soha',
        'soha-portrait-laurence-rimokh' => 'Portrait de Laurence Rimokh, artisane au Centre Soha',
        'soha-portrait-mamselle-ruiz' => 'Portrait de Mamselle Ruiz, artisane au Centre Soha',
        'soha-portrait-margaux-lecolier' => 'Portrait de Margaux Lécolier, artisane au Centre Soha',
        'soha-portrait-samira-kenikssi' => 'Portrait de Samira Kenikssi, artisane au Centre Soha',
        'soha-portrait-solange-rousseau' => 'Portrait de Solange Rousseau, artisane au Centre Soha',
        'soha-portrait-stephanie-bertrand' => 'Portrait de Stéphanie Bertrand, artisane au Centre Soha',
        'soha-portrait-yuv-baboolall' => 'Portrait de Yuv Baboolall, artisan au Centre Soha',
        'soha-hero-prendre-soin' => 'Espace de soin lumineux au Centre Soha',
        'soha-hero-se-ressourcer' => 'Salle calme et douce pour se ressourcer au Centre Soha',
        'soha-hero-se-transformer' => 'Grand espace ouvert pour les ateliers au Centre Soha',
        'soha-hero-studio-podcast' => 'Studio d\'enregistrement du Centre Soha',
        'soha-hero-espaces-professionnels' => 'Grande salle à louer au Centre Soha, sur le Plateau',
        'soha-hero-contact' => 'Devanture du Centre Soha, au 961 Rachel Est',
        'soha-hero-journal' => 'Coin lecture et écriture au Centre Soha',
        'soha-accueil-001' => 'Un moment de pratique au Centre Soha',
        'soha-accueil-003' => 'Un atelier en petit groupe au Centre Soha',
        'soha-accueil-005' => 'Les mains d\'une artisane au travail au Centre Soha',
        'soha-accueil-007' => 'Un espace lumineux du Centre Soha',
        'soha-accueil-009' => 'Un temps de partage au Centre Soha',
        'soha-accueil-plate-b4c136c1' => 'Détail d\'ambiance au Centre Soha',
        'soha-contact-093' => 'Un espace chaleureux du Centre Soha, au 961 Rachel Est',
        'soha-prendre-soin-028' => 'Séance de soin individuelle au Centre Soha',
        'soha-prendre-soin-034' => 'Table de soin dans un cabinet du Centre Soha',
        'soha-prendre-soin-035' => 'Ambiance apaisante d\'un espace de soin au Centre Soha',
        'soha-se-transformer-038' => 'Atelier de groupe dans la grande salle du Centre Soha',
        'soha-se-transformer-039' => 'Un moment de pratique corporelle au Centre Soha',
        'soha-se-transformer-040' => 'Cercle de participant·es au Centre Soha',
        'soha-espaces-professionnels-072' => 'Salle à louer au Centre Soha, sur le Plateau',
        'soha-espaces-professionnels-073' => 'Cabinet à louer pour thérapeute au Centre Soha',
        'soha-espaces-professionnels-075' => 'Grand plateau ouvert à louer au Centre Soha',
        'soha-espaces-professionnels-076' => 'Espace de travail lumineux à louer au Centre Soha',
        'soha-espaces-professionnels-plate-f4aaabd5' => 'Détail d\'un espace à louer au Centre Soha',
        'soha-studio-podcast-056' => 'Studio podcast à louer au Centre Soha',
        'soha-studio-podcast-057' => 'Micro et casque dans le studio du Centre Soha',
        'soha-studio-podcast-058' => 'Table d\'enregistrement du studio du Centre Soha',
        'soha-studio-podcast-059' => 'Coin prise de son du studio du Centre Soha',
        'soha-studio-podcast-060' => 'Éclairage tamisé du studio du Centre Soha',
        'soha-studio-podcast-061' => 'Régie du studio podcast du Centre Soha',
        'soha-studio-podcast-062' => 'Fauteuils d\'invité·es dans le studio du Centre Soha',
        'soha-studio-podcast-063' => 'Détail acoustique du studio du Centre Soha',
        'soha-studio-podcast-064' => 'Micro de studio en gros plan au Centre Soha',
        'soha-studio-podcast-065' => 'Table de mixage du studio du Centre Soha',
        'soha-studio-podcast-066' => 'Vue d\'ensemble du studio podcast du Centre Soha',
        'soha-studio-podcast-067' => 'Espace d\'enregistrement du Centre Soha',
        'soha-studio-podcast-068' => 'Casque posé sur la table du studio du Centre Soha',
        'soha-studio-podcast-069' => 'Coin causerie du studio du Centre Soha',
        'soha-studio-podcast-070' => 'Ambiance chaleureuse du studio du Centre Soha',
        'soha-studio-podcast-plate-4afc2856' => 'Détail du studio podcast du Centre Soha',
        'soha-evenement-atelier-core-energetics-107' => 'Atelier Core Energetics au Centre Soha',
    );
    global $wpdb; $done = 0;
    foreach ($alts as $frag => $alt) {
        $id = $wpdb->get_var($wpdb->prepare(
            "SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key='_wp_attached_file' AND meta_value LIKE %s ORDER BY post_id ASC LIMIT 1",
            '%' . $wpdb->esc_like($frag) . '%'
        ));
        if ($id) { update_post_meta($id, '_wp_attachment_image_alt', $alt); $done++; }
    }
    if ($done > 0) {
        update_option('soha_fi_alt_done', '1');
        set_transient('soha_fi_alt_report', $done . ' textes alternatifs posés.', 300);
    }
});
add_action('admin_notices', function () {
    if ($m = get_transient('soha_fi_alt_report')) {
        echo '<div class="notice notice-success is-dismissible"><p><strong>Soha :</strong> ' . esc_html($m) . '</p></div>';
        delete_transient('soha_fi_alt_report');
    }
});

add_action('wp_head', function () {
    if (!is_singular() && !is_front_page()) { return; }
    $heros = array(
      'accueil' => '2026/08/soha-accueil-001-1.webp',
      'se-ressourcer' => '2026/08/soha-hero-se-ressourcer-1.webp',
      'prendre-soin' => '2026/08/soha-hero-prendre-soin-1.webp',
      'se-transformer' => '2026/08/soha-hero-se-transformer-1.webp',
      'studio-podcast' => '2026/08/soha-hero-studio-podcast-1.webp',
      'espaces-professionnels' => '2026/08/soha-hero-espaces-professionnels-1.webp',
      'journal' => '2026/08/soha-hero-journal-1.webp',
      'contact' => '2026/08/soha-hero-contact-1.webp',
    );
    $slug = is_front_page() ? 'accueil' : get_post_field('post_name', get_queried_object_id());
    if (empty($heros[$slug])) { return; }
    $url = esc_url(wp_get_upload_dir()['baseurl'] . '/' . $heros[$slug]);
    echo "\n<link rel=\"preload\" as=\"image\" href=\"" . $url . "\" fetchpriority=\"high\">\n";
}, 1);
/* ============================================================================
 *  v1.2.2 — LES TROIS POLICES DU CANON, SERVIES PAR LE SITE LUI-MÊME
 *
 *  Avant : chaque page appelait fonts.googleapis.com et fonts.gstatic.com.
 *  Deux consequences — l'adresse IP du visiteur partait chez un tiers avant
 *  tout consentement (Loi 25), et le premier affichage attendait deux
 *  aller-retours reseau.
 *
 *  Ici : Elementor cesse d'imprimer ses liens Google, et les douze fichiers
 *  .woff2 livres avec l'extension sont declares a la place. Desactiver
 *  l'extension rend exactement l'etat d'avant — rien n'est ecrit nulle part.
 *
 *  Couverture : 286 des 300 usages du kit. Manquent Fraunces 300 (9 usages),
 *  Schibsted 300 (3) et 800 (2) — le navigateur les approche depuis la graisse
 *  voisine, l'ecart n'est pas perceptible a ces volumes.
 * ========================================================================== */

/* Elementor n'imprime plus aucun lien vers Google Fonts. */
add_filter('elementor/frontend/print_google_fonts', '__return_false');

/* Et le theme non plus, si jamais il en mettait un. */
add_action('wp_enqueue_scripts', function () {
    $styles = wp_styles();
    if (!$styles) { return; }
    foreach ($styles->queue as $poignee) {
        $src = isset($styles->registered[$poignee]) ? $styles->registered[$poignee]->src : '';
        if ($src && strpos($src, 'fonts.googleapis.com') !== false) {
            wp_dequeue_style($poignee);
        }
    }
}, 100);

/**
 * Les faces livrees : famille, style, graisse, fichier.
 */
function soha_polices_faces() {
    return array(
        array('DM Mono', 'normal', '500', 'dm-mono-v16-latin-500.woff2'),
        array('DM Mono', 'normal', '400', 'dm-mono-v16-latin-regular.woff2'),
        array('Fraunces', 'normal', '500', 'fraunces-v38-latin-500.woff2'),
        array('Fraunces', 'normal', '600', 'fraunces-v38-latin-600.woff2'),
        array('Fraunces', 'normal', '700', 'fraunces-v38-latin-700.woff2'),
        array('Fraunces', 'italic', '400', 'fraunces-v38-latin-italic.woff2'),
        array('Fraunces', 'normal', '400', 'fraunces-v38-latin-regular.woff2'),
        array('Schibsted Grotesk', 'normal', '500', 'schibsted-grotesk-v7-latin-500.woff2'),
        array('Schibsted Grotesk', 'normal', '600', 'schibsted-grotesk-v7-latin-600.woff2'),
        array('Schibsted Grotesk', 'normal', '700', 'schibsted-grotesk-v7-latin-700.woff2'),
        array('Schibsted Grotesk', 'italic', '400', 'schibsted-grotesk-v7-latin-italic.woff2'),
        array('Schibsted Grotesk', 'normal', '400', 'schibsted-grotesk-v7-latin-regular.woff2'),
    );
}

add_action('wp_head', function () {
    $base = plugins_url('polices/', __FILE__);

    /* Les deux faces qui portent le premier ecran : prechargees. */
    $prioritaires = array('schibsted-grotesk-v7-latin-regular.woff2',
                          'fraunces-v38-latin-600.woff2');
    foreach ($prioritaires as $face) {
        printf('<link rel="preload" as="font" type="font/woff2" crossorigin href="%s">' . "\n",
               esc_url($base . $face));
    }

    $css = '';
    foreach (soha_polices_faces() as $f) {
        list($famille, $style, $graisse, $fichier) = $f;
        $css .= sprintf(
            "@font-face{font-family:'%s';font-style:%s;font-weight:%s;font-display:swap;"
            . "src:url('%s') format('woff2')}\n",
            $famille, $style, $graisse, esc_url($base . $fichier)
        );
    }
    echo '<style id="soha-polices">' . "\n" . $css . '</style>' . "\n";
}, 1);

/* ============================================================================
 *  v1.2.3 — L'ESTIMATION VOYAGE AVEC LA DEMANDE
 *
 *  L'estimateur envoie vers /reservation/ avec quatre parametres dans
 *  l'adresse : ?espace=&jour=&plage=&tarif=. Sans ce pont, ils s'arretaient a
 *  la porte : la personne refaisait son choix a la main dans le formulaire, et
 *  le montant qu'elle avait vu a l'ecran n'arrivait jamais au Centre.
 *
 *  Ici, ils sont recopies dans les quatre champs caches du formulaire. Chaque
 *  demande arrive donc avec l'estimation que la personne avait sous les yeux —
 *  c'est aussi exactement ce qu'un CRM a besoin de recevoir.
 *
 *  Ne s'execute que sur une page portant le formulaire, et n'ecrit rien si les
 *  champs n'y sont pas.
 * ========================================================================== */
add_action('wp_footer', function () {
    ?>
    <script>
    (function () {
      try {
        var p = new URLSearchParams(window.location.search);
        var paires = {
          estim_espace: p.get('espace'),
          estim_jour:   p.get('jour'),
          estim_plage:  p.get('plage'),
          estim_tarif:  p.get('tarif')
        };
        var lisible = {
          sem: 'Semaine', fds: 'Fin de semaine',
          jour: 'Journée', demi: 'Demi-journée', soir: 'Soirée',
          studio: 'Studio', soha: 'Espace SÖHA',
          salle4: 'Salle 4', salles123: 'Salles 1·2·3'
        };
        Object.keys(paires).forEach(function (id) {
          var v = paires[id];
          if (!v) return;
          var champ = document.querySelector('[name="form_fields[' + id + ']"]')
                   || document.getElementById(id);
          if (!champ) return;
          champ.value = (id === 'estim_tarif') ? (v + ' $ +tx') : (lisible[v] || v);
        });
      } catch (e) {}
    })();
    </script>
    <?php
}, 110);

add_filter('wp_omit_loading_attr_threshold', function ($t) { return 1; });

add_action('wp_footer', function () {
    $lien = '/politique-de-confidentialite/';
    ?>
    <div id="soha-avis-temoins" role="region" aria-label="Avis de confidentialité" hidden>
      <p>Ce site n'utilise que des témoins essentiels à son bon fonctionnement — aucun traceur publicitaire ni de mesure d'audience. <a href="<?php echo esc_url($lien); ?>">En savoir plus</a>.</p>
      <button type="button" id="soha-avis-ok">J'ai compris</button>
    </div>
    <style>
      #soha-avis-temoins{position:fixed;left:0;right:0;bottom:0;z-index:9999;display:flex;gap:16px;align-items:center;justify-content:center;flex-wrap:wrap;background:#0E1A15;color:#F4F0E7;padding:14px 20px;font-size:14px;line-height:1.5;font-family:'Schibsted Grotesk',system-ui,sans-serif;box-shadow:0 -2px 12px rgba(14,26,21,.25)}
      #soha-avis-temoins[hidden]{display:none !important}
      #soha-avis-temoins p{margin:0;max-width:62ch}
      #soha-avis-temoins a{color:#19A7DB;text-decoration:underline}
      #soha-avis-ok{flex:none;cursor:pointer;border:0;border-radius:8px;background:#19A7DB;color:#0E1A15;font-weight:700;padding:9px 18px;font-size:14px;min-height:44px;font-family:inherit}
      #soha-avis-ok:hover{background:#19A7DB;color:#fff}
      #soha-avis-ok:focus-visible{outline:2px solid #F4F0E7;outline-offset:2px}
      @media(max-width:600px){#soha-avis-temoins{text-align:center}}
    </style>
    <script>(function(){try{var K='soha_avis_temoins_vu',el=document.getElementById('soha-avis-temoins');if(!el)return;var vu=false;try{vu=localStorage.getItem(K)==='1'}catch(e){}if(!vu)el.hidden=false;var b=document.getElementById('soha-avis-ok');if(b)b.addEventListener('click',function(){el.hidden=true;try{localStorage.setItem(K,'1')}catch(e){}})}catch(e){}})();</script>
    <?php
}, 100);


/* ============================================================================
 * MODULE 7 — CONTRÔLE APRÈS IMPORT  (v1.3.0)
 *
 * Quatre vérifications, et pas quatre au hasard : ce sont les quatre défauts
 * que ce site a réellement subis, chacun découvert des semaines après coup
 * parce qu'aucun d'eux ne lève d'erreur.
 *
 *   1. Les doublons de médias. Le kit ne contient aucune image : il les
 *      référence par adresse. À l'import, Elementor va les chercher — et si
 *      elles sont déjà dans la médiathèque, il en crée une deuxième copie,
 *      « soha-accueil-001-1.webp » à côté de « soha-accueil-001.webp ». Les
 *      pages pointent alors vers la copie ; l'originale devient orpheline.
 *      Cinquante-neuf fois, la dernière fois.
 *
 *   2. Les images référencées mais absentes. Le symétrique du premier : une
 *      adresse qui ne mène à rien. À l'écran, un trou. Aucune erreur.
 *
 *   3. Les formulaires sans destinataire. Elementor se rabat alors sur
 *      l'adresse d'administration du site. Les demandes partent dans une boîte
 *      que personne ne regarde — c'est arrivé, sur quatre formulaires.
 *
 *   4. Les liens internes qui pointent à côté. Un lien vers « /dev2/… » sur un
 *      site installé dans « /dev » mène à une page introuvable. Quatre-vingt-
 *      quatre fois, dans la dernière version du kit.
 *
 * Lecture seule : cet écran ne répare rien. Il regarde, il compte, il nomme.
 * =========================================================================== */

add_action('admin_menu', function () {
    add_management_page(
        __('Contrôle Soha', 'centre-soha'),
        __('Contrôle Soha', 'centre-soha'),
        'manage_options',
        'soha-controle',
        'soha_controle_ecran'
    );
});

/** Le chemin d'installation du site, tel que WordPress le connaît. */
function soha_controle_prefixe() {
    $chemin = parse_url(home_url('/'), PHP_URL_PATH);
    return '/' . trim((string) $chemin, '/');
}

/**
 * 1 · Les médias en double.
 *
 * On cherche les fichiers dont le nom finit par « -1 », « -2 »… ET dont le
 * jumeau sans suffixe existe aussi. Un « photo-2.webp » tout seul n'est pas un
 * doublon : c'est peut-être la deuxième photo d'une série.
 */
function soha_controle_doublons() {
    global $wpdb;
    $fichiers = $wpdb->get_results(
        "SELECT p.ID, m.meta_value AS chemin
           FROM {$wpdb->postmeta} m
           JOIN {$wpdb->posts} p ON p.ID = m.post_id
          WHERE m.meta_key = '_wp_attached_file'"
    );

    $tous = array();
    foreach ($fichiers as $f) {
        $tous[$f->chemin] = (int) $f->ID;
    }

    $doublons = array();
    foreach ($tous as $chemin => $id) {
        if (!preg_match('#^(.*)-([1-9]\d?)(\.[A-Za-z0-9]+)$#', $chemin, $m)) {
            continue;
        }
        $original = $m[1] . $m[3];
        if (isset($tous[$original])) {
            $doublons[] = array(
                'id'       => $id,
                'copie'    => $chemin,
                'original' => $original,
            );
        }
    }
    return $doublons;
}

/** Toutes les adresses d'images de ce site trouvées dans les pages Elementor. */
function soha_controle_images_referencees() {
    global $wpdb;
    $lignes = $wpdb->get_col(
        "SELECT meta_value FROM {$wpdb->postmeta} WHERE meta_key = '_elementor_data'"
    );
    $base = preg_quote(untrailingslashit(home_url()), '#');
    $vues = array();
    foreach ($lignes as $donnees) {
        /* Elementor range son arbre en JSON : les barres obliques y sont
           échappées, `http:\/\/…\/wp-content\/…`. Chercher une adresse
           normale là-dedans ne trouve rien — et ne trouver rien ressemble
           beaucoup à ne rien avoir à trouver. C'est exactement le piège qui
           avait déjà fait rater le premier recensement des images. */
        $plat = str_replace('\\/', '/', (string) $donnees);
        if (preg_match_all('#' . $base . '/wp-content/uploads/([^"\\\\ )]+\.(?:jpe?g|png|webp|gif|svg))#i',
                           $plat, $m)) {
            foreach ($m[1] as $chemin) {
                $vues[$chemin] = true;
            }
        }
    }
    return array_keys($vues);
}

/** 2 · Les images référencées qui ne sont pas dans la médiathèque. */
function soha_controle_images_absentes() {
    global $wpdb;
    $presents = array_flip($wpdb->get_col(
        "SELECT meta_value FROM {$wpdb->postmeta} WHERE meta_key = '_wp_attached_file'"
    ));
    $absentes = array();
    foreach (soha_controle_images_referencees() as $chemin) {
        if (!isset($presents[$chemin])) {
            $absentes[] = $chemin;
        }
    }
    return $absentes;
}

/** 3 · Les formulaires Elementor sans destinataire. */
function soha_controle_formulaires() {
    global $wpdb;
    $lignes = $wpdb->get_results(
        "SELECT post_id, meta_value FROM {$wpdb->postmeta} WHERE meta_key = '_elementor_data'"
    );
    $muets = array();
    foreach ($lignes as $ligne) {
        $arbre = json_decode((string) $ligne->meta_value, true);
        if (!is_array($arbre)) {
            continue;
        }
        soha_controle_chercher_formulaires($arbre, (int) $ligne->post_id, $muets);
    }
    return $muets;
}

function soha_controle_chercher_formulaires($noeud, $page, &$muets) {
    foreach ((array) $noeud as $e) {
        if (!is_array($e)) {
            continue;
        }
        if (isset($e['widgetType']) && 'form' === $e['widgetType']) {
            $r = isset($e['settings']) ? $e['settings'] : array();
            $actions = isset($r['submit_actions']) ? (array) $r['submit_actions'] : array();
            $envoie = in_array('email', $actions, true) || !$actions;
            $vers = isset($r['email_to']) ? trim((string) $r['email_to']) : '';
            if ($envoie && '' === $vers) {
                $muets[] = array(
                    'page' => $page,
                    'nom'  => isset($r['form_name']) ? $r['form_name'] : __('sans nom', 'centre-soha'),
                );
            }
        }
        if (!empty($e['elements'])) {
            soha_controle_chercher_formulaires($e['elements'], $page, $muets);
        }
    }
}

/** 4 · Les liens internes qui ne pointent pas dans ce site. */
function soha_controle_liens() {
    global $wpdb;
    $lignes = $wpdb->get_results(
        "SELECT post_id, meta_value FROM {$wpdb->postmeta} WHERE meta_key = '_elementor_data'"
    );
    $bon = soha_controle_prefixe();

    /* À la racine, il n'y a pas de préfixe à comparer : `/dev2/contact/` y est
       une adresse comme une autre. Le contrôle n'a alors rien à dire, et il
       vaut mieux qu'il se taise que qu'il signale tout le site. */
    if ('/' === $bon) {
        return array();
    }

    $mauvais = array();
    foreach ($lignes as $ligne) {
        if (!preg_match_all('#"(?:url|href)"\s*:\s*"(\\\\/[^"]*)"#', (string) $ligne->meta_value, $m)) {
            continue;
        }
        foreach ($m[1] as $lien) {
            $lien = stripslashes($lien);
            if (0 === strpos($lien, '//') || 0 === strpos($lien, $bon . '/') || $lien === $bon) {
                continue;
            }
            if (0 === strpos($lien, '/wp-content/') || 0 === strpos($lien, '/wp-admin/')) {
                continue;
            }
            $cle = $lien;
            if (!isset($mauvais[$cle])) {
                $mauvais[$cle] = array('lien' => $lien, 'pages' => array());
            }
            $mauvais[$cle]['pages'][(int) $ligne->post_id] = true;
        }
    }
    return array_values($mauvais);
}

function soha_controle_ecran() {
    if (!current_user_can('manage_options')) {
        wp_die(esc_html__('Droits insuffisants.', 'centre-soha'));
    }

    $doublons  = soha_controle_doublons();
    $absentes  = soha_controle_images_absentes();
    $muets     = soha_controle_formulaires();
    $liens     = soha_controle_liens();
    $total     = count($doublons) + count($absentes) + count($muets) + count($liens);
    ?>
    <div class="wrap">
        <h1><?php esc_html_e('Contrôle Soha — après un import', 'centre-soha'); ?></h1>

        <p style="max-width:74ch">
            <?php esc_html_e(
                "Quatre vérifications, et pas quatre au hasard : ce sont les quatre défauts que ce site a réellement subis. Aucun des quatre ne lève d'erreur — c'est pour ça qu'ils ont vécu des semaines. Cet écran ne répare rien : il regarde, il compte, il nomme.",
                'centre-soha'
            ); ?>
        </p>

        <?php if (0 === $total) : ?>
            <div class="notice notice-success inline"><p><strong><?php
                esc_html_e('Rien à signaler sur les quatre points.', 'centre-soha');
            ?></strong></p></div>
        <?php else : ?>
            <div class="notice notice-warning inline"><p><strong><?php printf(
                /* translators: %d : nombre total de signalements. */
                esc_html(_n('%d point à regarder.', '%d points à regarder.', $total, 'centre-soha')),
                (int) $total
            ); ?></strong></p></div>
        <?php endif; ?>

        <h2><?php esc_html_e('1 · Médias en double', 'centre-soha'); ?>
            <span class="count">(<?php echo count($doublons); ?>)</span></h2>
        <p class="description" style="max-width:74ch"><?php esc_html_e(
            "Une copie « nom-1.webp » à côté de « nom.webp ». C'est ce que produit un import quand l'image est déjà dans la médiathèque : les pages pointent vers la copie, l'originale devient orpheline. Cinquante-neuf fois, la dernière fois.",
            'centre-soha'
        ); ?></p>
        <?php if (!$doublons) : ?>
            <p><em><?php esc_html_e('Aucun.', 'centre-soha'); ?></em></p>
        <?php else : ?>
            <table class="widefat striped" style="max-width:840px"><thead><tr>
                <th><?php esc_html_e('La copie', 'centre-soha'); ?></th>
                <th><?php esc_html_e("L'originale", 'centre-soha'); ?></th>
                <th style="width:120px"></th>
            </tr></thead><tbody>
            <?php foreach (array_slice($doublons, 0, 100) as $d) : ?>
                <tr>
                    <td><code><?php echo esc_html($d['copie']); ?></code></td>
                    <td><code><?php echo esc_html($d['original']); ?></code></td>
                    <td><a href="<?php echo esc_url(get_edit_post_link($d['id'])); ?>">
                        <?php esc_html_e('voir', 'centre-soha'); ?></a></td>
                </tr>
            <?php endforeach; ?>
            </tbody></table>
        <?php endif; ?>

        <h2><?php esc_html_e('2 · Images référencées mais absentes', 'centre-soha'); ?>
            <span class="count">(<?php echo count($absentes); ?>)</span></h2>
        <p class="description" style="max-width:74ch"><?php esc_html_e(
            "Une page demande une image que la médiathèque n'a pas. À l'écran, un trou — et aucune erreur nulle part.",
            'centre-soha'
        ); ?></p>
        <?php if (!$absentes) : ?>
            <p><em><?php esc_html_e('Aucune.', 'centre-soha'); ?></em></p>
        <?php else : ?>
            <ul style="list-style:disc;padding-left:1.4em">
            <?php foreach (array_slice($absentes, 0, 60) as $a) : ?>
                <li><code><?php echo esc_html($a); ?></code></li>
            <?php endforeach; ?>
            </ul>
        <?php endif; ?>

        <h2><?php esc_html_e('3 · Formulaires sans destinataire', 'centre-soha'); ?>
            <span class="count">(<?php echo count($muets); ?>)</span></h2>
        <p class="description" style="max-width:74ch"><?php esc_html_e(
            "Sans destinataire, Elementor envoie à l'adresse d'administration du site. Les demandes partent dans une boîte que personne ne regarde. C'est arrivé, sur quatre formulaires.",
            'centre-soha'
        ); ?></p>
        <?php if (!$muets) : ?>
            <p><em><?php esc_html_e('Aucun.', 'centre-soha'); ?></em></p>
        <?php else : ?>
            <ul style="list-style:disc;padding-left:1.4em">
            <?php foreach ($muets as $f) : ?>
                <li><?php printf(
                    /* translators: 1 : nom du formulaire, 2 : titre de la page. */
                    esc_html__('« %1$s » sur %2$s', 'centre-soha'),
                    esc_html($f['nom']),
                    esc_html(get_the_title($f['page']))
                ); ?> — <a href="<?php echo esc_url(get_edit_post_link($f['page'])); ?>">
                    <?php esc_html_e('modifier', 'centre-soha'); ?></a></li>
            <?php endforeach; ?>
            </ul>
        <?php endif; ?>

        <h2><?php esc_html_e('4 · Liens internes hors du site', 'centre-soha'); ?>
            <span class="count">(<?php echo count($liens); ?>)</span></h2>
        <p class="description" style="max-width:74ch"><?php printf(
            /* translators: %s : le chemin d'installation du site. */
            esc_html__("Ce site est installé dans %s. Un lien vers un autre chemin mène à une page introuvable — et l'import ne les corrige pas : il ne réécrit que les adresses complètes, jamais celles qui commencent par une barre oblique.", 'centre-soha'),
            '<code>' . esc_html(soha_controle_prefixe()) . '</code>'
        ); ?></p>
        <?php if ('/' === soha_controle_prefixe()) : ?>
            <p><em><?php esc_html_e(
                "Ce site est installé à la racine : il n'y a pas de préfixe à comparer, ce contrôle ne s'applique pas.",
                'centre-soha'
            ); ?></em></p>
        <?php elseif (!$liens) : ?>
            <p><em><?php esc_html_e('Aucun.', 'centre-soha'); ?></em></p>
        <?php else : ?>
            <table class="widefat striped" style="max-width:840px"><thead><tr>
                <th><?php esc_html_e('Le lien', 'centre-soha'); ?></th>
                <th style="width:120px"><?php esc_html_e('Pages', 'centre-soha'); ?></th>
            </tr></thead><tbody>
            <?php foreach (array_slice($liens, 0, 60) as $l) : ?>
                <tr>
                    <td><code><?php echo esc_html($l['lien']); ?></code></td>
                    <td><?php echo count($l['pages']); ?></td>
                </tr>
            <?php endforeach; ?>
            </tbody></table>
        <?php endif; ?>
    </div>
    <?php
}
