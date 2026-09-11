<?php
/**
 * Plugin Name: Soha — Estimateur de location
 * Description: Shortcode [soha_estimateur] — estimateur de location des espaces du Centre Soha. Grille réelle (24 tarifs), autonome, sans dépendance ACF. Le bouton pointe vers la page de réservation, et fonctionne AVANT que le JavaScript ne tourne.
 * Version:     2.2.0
 * Author:      Centre Soha
 */

if (!defined('ABSPATH')) { exit; }

/**
 * URL de la page (ou du formulaire) de réservation.
 *
 * v2.0.2 — destination : la page « /reservation/ », conformément à la décision
 * déjà retenue au dossier (index du 7 septembre : « Destination du bouton
 * estimateur — /reservation/ (formulaire) est retenu »). La v2.0.1 l'avait
 * détournée vers #demande parce que la page n'existait pas encore ; c'est la
 * page qu'il faut monter, pas la destination qu'il faut changer.
 *
 * Le seul vrai défaut de la v2.0.0 est corrigé : « /reservation/ » écrit en dur
 * pointait la RACINE du domaine, donc le site de production, depuis une
 * installation en sous-dossier. home_url() le résout d'après l'adresse réelle
 * du site — /dev, /dev2 ou la racine, la destination reste juste.
 *
 * Pour la forcer ailleurs, la définir dans wp-config.php :
 *   define('SOHA_ESTIM_RESERVATION_URL', 'https://centresoha.com/reservation/');
 */
function soha_estim_reservation_url() {
    if (defined('SOHA_ESTIM_RESERVATION_URL')) {
        return SOHA_ESTIM_RESERVATION_URL;
    }
    return home_url('/reservation/');
}

/**
 * Grille tarifaire réelle (source : estimateur centresoha.com). Tous les prix + tx.
 * Structure : clé => [ libellé, superficie, semaine[jour,demi,soir], fin-de-semaine[jour,demi,soir] ].
 */
function soha_estim_grille() {
    return array(
        'studio'    => array('Studio',        '900 pi² · insonorisé',   array('jour'=>450,'demi'=>250,'soir'=>200), array('jour'=>550,'demi'=>300,'soir'=>250)),
        'soha'      => array('Espace SÖHA',    '2200 pi² · grand plateau',array('jour'=>600,'demi'=>350,'soir'=>250), array('jour'=>700,'demi'=>400,'soir'=>300)),
        'salle4'    => array('Salle 4',        'bureau double · fenestré',array('jour'=>160,'demi'=>100,'soir'=>80),  array('jour'=>240,'demi'=>140,'soir'=>120)),
        'salles123' => array('Salles 1·2·3',   'cabinet de soin',        array('jour'=>120,'demi'=>60, 'soir'=>30),  array('jour'=>160,'demi'=>90, 'soir'=>60)),
    );
}

/**
 * L'adresse de réservation pour une sélection donnée.
 *
 * v2.1.0 — elle est calculée ici, en PHP, et posée dans le `href` dès le
 * rendu. Avant, le bouton partait avec `href="#"` et n'obtenait sa vraie
 * destination qu'une fois le JavaScript exécuté. Sur un site servi derrière
 * Rocket Loader — qui diffère et réordonne les scripts — la personne pouvait
 * cliquer « Demander cette réservation » et rester exactement où elle était.
 * Un bouton qui ne mène nulle part ne lève aucune erreur ; il perd juste une
 * demande de location, en silence.
 */
function soha_estim_lien($espace, $jour, $plage, $tarif) {
    return add_query_arg(
        array('espace' => $espace, 'jour' => $jour, 'plage' => $plage, 'tarif' => $tarif),
        soha_estim_reservation_url()
    );
}

function soha_estim_shortcode($atts = array()) {
    $grille = soha_estim_grille();

    // Données pour le JS (échappées via wp_json_encode).
    $data = wp_json_encode($grille);
    $resa = wp_json_encode(esc_url(soha_estim_reservation_url()));

    // Clé du premier espace (sélection par défaut).
    $first = key($grille);

    /* La sélection de départ, en clair : ce que la page affiche avant même
       qu'un script ne s'exécute. Le prix vient de la grille, il n'est plus
       écrit en dur — sinon il resterait à 450 $ le jour où la grille change. */
    $depart       = $grille[$first];
    $tarif_depart = $depart[2]['jour'];
    $lien_depart  = soha_estim_lien($first, 'sem', 'jour', $tarif_depart);

    ob_start();
    ?>
    <div id="sohaEstim" data-first="<?php echo esc_attr($first); ?>">
      <div class="se-grid">

        <div class="se-panel">
          <h3 class="se-step">1 · Choisissez votre espace</h3>
          <div class="se-spaces" id="seSpaces">
            <?php $i = 0; foreach ($grille as $k => $e): ?>
              <button type="button" class="se-space<?php echo $i === 0 ? ' on' : ''; ?>"
                      aria-pressed="<?php echo $i === 0 ? 'true' : 'false'; ?>"
                      data-k="<?php echo esc_attr($k); ?>">
                <span class="se-space-name"><?php echo esc_html($e[0]); ?></span>
                <span class="se-space-sub"><?php echo esc_html($e[1]); ?></span>
              </button>
            <?php $i++; endforeach; ?>
          </div>

          <h3 class="se-step">2 · Type de journée</h3>
          <div class="se-seg" id="seDay">
            <button type="button" data-k="sem" class="on" aria-pressed="true">Semaine</button>
            <button type="button" data-k="fds" aria-pressed="false">Fin de semaine</button>
          </div>

          <h3 class="se-step">3 · Plage horaire</h3>
          <div class="se-seg" id="seSlot">
            <button type="button" data-k="jour" class="on" aria-pressed="true">Journée</button>
            <button type="button" data-k="demi" aria-pressed="false">Demi-journée</button>
            <button type="button" data-k="soir" aria-pressed="false">Soirée</button>
          </div>
        </div>

        <div class="se-out">
          <div class="se-lab" id="seLab">Estimation</div>
          <div class="se-price" id="sePrice" aria-live="polite" aria-atomic="true"
               role="status"><?php echo esc_html(number_format_i18n($tarif_depart)); ?> $ <small>+tx</small></div>
          <div class="se-sel" id="seSel"><?php
              echo esc_html($depart[0] . ' · Semaine · Journée'); ?></div>
          <p class="se-note">* Tarif indicatif. Prix, conditions et disponibilités sujets à changement.
             Minimum 2 jours les fins de semaine. Aucune réservation par téléphone.</p>
          <a class="se-cta" id="seCta" href="<?php echo esc_url($lien_depart); ?>">Demander cette réservation</a>
        </div>

      </div>
    </div>
    <?php

    // CSS + JS imprimés une seule fois même si le shortcode est présent plusieurs fois.
    static $assets = false;
    if (!$assets):
        $assets = true;
    ?>
    <style id="soha-estim-css">
      #sohaEstim{
        --se-accent:#19A7DB; --se-ink:#0E1A15; --se-paper:#F4F1E9;
        --se-card:#14100C; --se-card-ink:#F4F1E9; --se-line:rgba(14,26,21,.16);
        font-family:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
        color:var(--se-ink); max-width:960px; margin:0 auto;
      }
      #sohaEstim *{box-sizing:border-box}
      #sohaEstim .se-grid{display:grid; grid-template-columns:1.15fr .85fr; gap:22px}
      @media (max-width:720px){#sohaEstim .se-grid{grid-template-columns:1fr}}
      #sohaEstim .se-panel{background:var(--se-paper); border:1px solid var(--se-line); border-radius:14px; padding:22px 24px}
      #sohaEstim .se-step{font-size:.72rem; letter-spacing:.14em; text-transform:uppercase;
        color:rgba(14,26,21,.55); font-weight:600; margin:18px 0 10px}
      #sohaEstim .se-step:first-child{margin-top:0}
      #sohaEstim .se-spaces{display:grid; grid-template-columns:1fr 1fr; gap:10px}
      @media (max-width:480px){#sohaEstim .se-spaces{grid-template-columns:1fr}}
      #sohaEstim .se-space{display:flex; flex-direction:column; gap:2px; text-align:left; cursor:pointer;
        background:#fff; border:1px solid var(--se-line); border-radius:0; padding:13px 15px; min-height:60px; font:inherit; color:inherit}
      #sohaEstim .se-space .se-space-name{font-family:"Fraunces",Georgia,serif; font-size:1.05rem}
      #sohaEstim .se-space .se-space-sub{font-size:.78rem; color:rgba(14,26,21,.55)}
      #sohaEstim .se-space.on{border-color:var(--se-accent); box-shadow:inset 0 0 0 1px var(--se-accent)}
      #sohaEstim .se-seg{display:flex; flex-wrap:wrap; gap:8px}
      #sohaEstim .se-seg button{cursor:pointer; font:inherit; background:#fff; color:inherit;
        border:1px solid var(--se-line); border-radius:999px; padding:9px 16px; min-height:44px}
      #sohaEstim .se-seg button.on{background:var(--se-ink); color:#fff; border-color:var(--se-ink)}
      #sohaEstim .se-seg button.off{opacity:.35; pointer-events:none}
      #sohaEstim :focus-visible{outline:2px solid var(--se-accent); outline-offset:2px}
      #sohaEstim .se-out{background:var(--se-card); color:var(--se-card-ink); border-radius:14px;
        padding:28px 26px; display:flex; flex-direction:column; justify-content:center}
      #sohaEstim .se-lab{font-size:.72rem; letter-spacing:.18em; text-transform:uppercase; color:var(--se-accent); font-weight:600}
      #sohaEstim .se-price{font-family:"Fraunces",Georgia,serif; font-size:3rem; line-height:1.05; margin:8px 0 6px}
      #sohaEstim .se-price small{font-size:1rem; color:var(--se-accent)}
      #sohaEstim .se-sel{font-size:.95rem; color:rgba(244,241,231,.7)}
      #sohaEstim .se-note{font-size:.74rem; color:rgba(244,241,231,.5); margin:16px 0 18px; line-height:1.5}
      #sohaEstim .se-cta{display:inline-flex; align-items:center; justify-content:center;
        text-align:center; text-decoration:none; font-weight:600;
        background:var(--se-accent); color:#fff; border:1px solid var(--se-accent);
        border-radius:0; padding:14px 27px; min-height:48px;
        transition:background-color 140ms cubic-bezier(.22,.61,.36,1),
                   border-color 140ms cubic-bezier(.22,.61,.36,1)}
      #sohaEstim .se-cta:hover,
      #sohaEstim .se-cta:focus-visible{background:var(--se-ink); border-color:var(--se-ink); color:#fff}
      #sohaEstim .se-cta:focus-visible{outline:2px solid var(--se-accent); outline-offset:2px}
      @media (prefers-reduced-motion:reduce){#sohaEstim .se-cta{transition:none}}
    </style>

    <?php /* `data-cfasync="false"` : le site est servi derrière Cloudflare avec
             Rocket Loader, qui diffère et réordonne les scripts. Celui-ci
             touche au DOM tout de suite. Sans cet attribut, l'estimateur peut
             rester figé sur sa sélection de départ. */ ?>
    <script id="soha-estim-js" data-cfasync="false">
    (function(){
      var GRILLE = <?php echo $data; ?>;
      var RESA   = <?php echo $resa; ?>;
      var DAYLBL = {sem:'Semaine', fds:'Fin de semaine'};
      var SLOTLBL= {jour:'Journée', demi:'Demi-journée', soir:'Soirée'};

      document.querySelectorAll('#sohaEstim').forEach(function(root){
        var space = root.getAttribute('data-first');
        var day = 'sem', slot = 'jour';
        var priceEl = root.querySelector('#sePrice');
        var selEl   = root.querySelector('#seSel');
        var ctaEl   = root.querySelector('#seCta');

        function fmt(n){ return n.toLocaleString('fr-CA'); }

        function sync(){
          var e = GRILLE[space];
          var table = (day === 'fds') ? e[3] : e[2];
          var val = table[slot];
          priceEl.innerHTML = fmt(val) + ' $ <small>+tx</small>';
          selEl.textContent = e[0] + ' · ' + DAYLBL[day] + ' · ' + SLOTLBL[slot];
          var q = '?espace=' + encodeURIComponent(space)
                + '&jour='   + encodeURIComponent(day)
                + '&plage='  + encodeURIComponent(slot)
                + '&tarif='  + encodeURIComponent(val);
          ctaEl.setAttribute('href', RESA + q);
        }

        root.querySelectorAll('#seSpaces .se-space').forEach(function(b){
          b.addEventListener('click', function(){
            space = b.getAttribute('data-k');
            root.querySelectorAll('#seSpaces .se-space').forEach(function(x){
              x.classList.remove('on'); x.setAttribute('aria-pressed', 'false');
            });
            b.classList.add('on'); b.setAttribute('aria-pressed', 'true');
            sync();
          });
        });
        root.querySelectorAll('#seDay button').forEach(function(b){
          b.addEventListener('click', function(){
            day = b.getAttribute('data-k');
            root.querySelectorAll('#seDay button').forEach(function(x){
              x.classList.remove('on'); x.setAttribute('aria-pressed', 'false');
            });
            b.classList.add('on'); b.setAttribute('aria-pressed', 'true');
            sync();
          });
        });
        root.querySelectorAll('#seSlot button').forEach(function(b){
          b.addEventListener('click', function(){
            slot = b.getAttribute('data-k');
            root.querySelectorAll('#seSlot button').forEach(function(x){
              x.classList.remove('on'); x.setAttribute('aria-pressed', 'false');
            });
            b.classList.add('on'); b.setAttribute('aria-pressed', 'true');
            sync();
          });
        });

        sync();
      });
    })();
    </script>
    <?php
    endif;

    return ob_get_clean();
}
add_shortcode('soha_estimateur', 'soha_estim_shortcode');
