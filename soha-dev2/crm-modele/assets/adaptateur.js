/* =============================================================================
 *  Centre Soha — l'adaptateur de stockage du CRM
 *
 *  Le CRM appelle `window.storage.get()` et `window.storage.set()`. Cet objet
 *  n'existe pas dans un navigateur : c'est pour ça que rien n'était conservé.
 *  Ce fichier le fournit, adossé à la base de données de WordPress.
 *
 *  Trois soins particuliers, tirés de la façon dont le CRM l'utilise :
 *
 *  1. `set()` n'est jamais attendu par le CRM (`persist()` l'appelle et passe
 *     à la suite). Un échec resterait donc invisible — exactement la panne
 *     qu'on vient de réparer. L'adaptateur affiche une bannière visible dès
 *     qu'une écriture échoue, et ne se tait jamais.
 *
 *  2. Le CRM enregistre à chaque frappe. On regroupe les écritures sur 800 ms
 *     pour ne pas marteler le serveur, et on vide la file avant la fermeture
 *     de l'onglet — sinon les dernières secondes de travail seraient perdues.
 *
 *  3. Deux personnes peuvent avoir le CRM ouvert. Le serveur refuse une
 *     écriture fondée sur une révision périmée ; on le dit clairement plutôt
 *     que d'écraser le travail de l'autre en silence.
 * ========================================================================== */
(function () {
  "use strict";

  if (typeof window.SOHA_CRM === "undefined") {
    return; // pas sur l'écran du CRM
  }

  var RACINE = window.SOHA_CRM.racine;
  var JETON = window.SOHA_CRM.jeton;
  var DELAI = 800;

  var revision = 0;
  var enAttente = null;
  var minuteur = null;
  var enVol = false;

  /* ---------------------------------------------------------------- bannière */

  var SOCLE =
    "position:fixed;left:50%;transform:translateX(-50%);top:44px;z-index:99999;" +
    "font-family:'Schibsted Grotesk',system-ui,sans-serif;font-size:14px;line-height:1.45;" +
    "padding:12px 18px;border-radius:2px;max-width:min(560px,92vw);" +
    "box-shadow:0 6px 24px rgba(14,26,21,.18);";
  var TEINTES = {
    erreur:  "background:#AE1E3B;color:#fff",
    conflit: "background:#D29A4E;color:#0E1A15"
  };

  /* On n'annonce QUE ce qui ne va pas. Le CRM a déjà son propre message quand
     une action réussit ; féliciter à chaque frappe serait du bruit, et le bruit
     finit par cacher le seul avis qui compte. */
  function banniere(texte, genre) {
    var el = document.getElementById("soha-crm-avis");
    if (!el) {
      el = document.createElement("div");
      el.id = "soha-crm-avis";
      el.setAttribute("role", "alert");
      el.setAttribute("aria-live", "assertive");
      document.body.appendChild(el);
    }
    el.setAttribute("style", SOCLE + (TEINTES[genre] || TEINTES.erreur));
    el.textContent = texte;
    el.hidden = false;
  }

  function silence() {
    var el = document.getElementById("soha-crm-avis");
    if (el) el.hidden = true;
  }

  /* ------------------------------------------------------------------ réseau */

  function lire() {
    return fetch(RACINE, {
      method: "GET",
      credentials: "same-origin",
      headers: { "X-WP-Nonce": JETON }
    }).then(function (r) {
      if (!r.ok) throw new Error("lecture " + r.status);
      return r.json();
    }).then(function (d) {
      revision = d.revision || 0;
      return d.valeur ? { value: d.valeur } : null;
    });
  }

  function ecrire(valeur) {
    enVol = true;
    return fetch(RACINE, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-WP-Nonce": JETON
      },
      body: JSON.stringify({ valeur: valeur, revision: revision })
    }).then(function (r) {
      return r.json().then(function (d) { return { statut: r.status, corps: d }; });
    }).then(function (rep) {
      enVol = false;

      if (rep.statut === 409) {
        banniere(
          "Quelqu'un d'autre a enregistré pendant que tu travaillais. " +
          "Recharge la page avant de continuer — sinon l'un des deux travaux sera perdu.",
          "conflit"
        );
        return;
      }
      if (rep.statut < 200 || rep.statut >= 300) {
        var m = (rep.corps && rep.corps.message) ? rep.corps.message : ("erreur " + rep.statut);
        banniere("Enregistrement refusé : " + m + " — ne ferme pas cet onglet.", "erreur");
        return;
      }
      revision = rep.corps.revision || revision + 1;
      silence();
    }).catch(function (e) {
      enVol = false;
      banniere(
        "Enregistrement impossible (" + (e && e.message ? e.message : "réseau") +
        "). Tes dernières modifications ne sont pas encore en sécurité — ne ferme pas cet onglet.",
        "erreur"
      );
    });
  }

  function vider() {
    clearTimeout(minuteur);
    minuteur = null;
    if (enAttente === null) return Promise.resolve();
    var v = enAttente;
    enAttente = null;
    return ecrire(v);
  }

  /* Dernier recours à la fermeture : sendBeacon part même si la page s'en va.
     Il ne porte pas d'en-tête personnalisé, donc le jeton voyage dans l'URL —
     WordPress l'accepte en paramètre `_wpnonce`. */
  function viderAvantFermeture() {
    if (enAttente === null) return;
    try {
      var url = RACINE + (RACINE.indexOf("?") === -1 ? "?" : "&") +
                "_wpnonce=" + encodeURIComponent(JETON);
      var charge = new Blob(
        [JSON.stringify({ valeur: enAttente, revision: revision })],
        { type: "application/json" }
      );
      navigator.sendBeacon(url, charge);
      enAttente = null;
    } catch (e) { /* on a fait ce qu'on a pu */ }
  }

  window.addEventListener("beforeunload", function (e) {
    if (enAttente !== null || enVol) {
      viderAvantFermeture();
      e.preventDefault();
      e.returnValue = "";
    }
  });

  /* Quand l'onglet passe en arrière-plan, on n'attend pas les 800 ms. */
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") vider();
  });

  /* ------------------------------------------------------------- l'interface */

  window.storage = {
    get: function () {
      return lire();
    },
    set: function (cle, valeur) {
      enAttente = valeur;
      clearTimeout(minuteur);
      minuteur = setTimeout(vider, DELAI);
      return Promise.resolve();
    }
  };
})();
