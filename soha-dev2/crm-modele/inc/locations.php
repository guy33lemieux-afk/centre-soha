<?php
/**
 * Centre Soha — CRM, phase 2 : la demande devient une réservation.
 *
 * L'estimateur affiche un prix, le formulaire le transporte, la demande le
 * garde — et jusqu'ici tout ça s'arrêtait là : Mala relisait le courriel et
 * ressaisissait à la main l'espace, la date et le montant. Trois occasions de
 * se tromper, pour une information qui était déjà juste.
 *
 * Ici, verser une demande de location crée la réservation avec ce que la
 * personne a réellement choisi. Aucune valeur n'est inventée : ce qui n'a pas
 * été demandé reste vide, et ce qui ne se traduit pas proprement va dans la
 * note plutôt que dans un champ où il mentirait.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Les quatre espaces du 961, tels que le site les nomme.
 *
 * Le formulaire les écrit avec leur superficie entre parenthèses ; le CRM les
 * veut nus. C'est la seule traduction, et elle est explicite pour qu'un
 * cinquième espace un jour se déclare ici plutôt que se devine.
 */
function soha_crm_espaces() {
    return apply_filters('soha_crm_espaces', array(
        'Studio (900 pi²)'              => 'Studio',
        'Espace SÖHA (2200 pi²)'        => 'Espace SÖHA',
        'Salle 4 (bureau double)'       => 'Salle 4',
        'Salles 1·2·3 (cabinet de soin)' => 'Salles 1·2·3',
    ));
}

/** La valeur d'un champ, par son identifiant puis par son étiquette. */
function soha_crm_champ($champs, $cle) {
    foreach ((array) $champs as $c) {
        if (isset($c['id']) && $c['id'] === $cle) {
            return trim((string) $c['valeur']);
        }
    }
    $cle_min = function_exists('mb_strtolower') ? mb_strtolower($cle, 'UTF-8') : strtolower($cle);
    foreach ((array) $champs as $c) {
        $et = function_exists('mb_strtolower')
            ? mb_strtolower($c['etiquette'], 'UTF-8')
            : strtolower($c['etiquette']);
        if ($et === $cle_min) {
            return trim((string) $c['valeur']);
        }
    }
    return '';
}

/** Cette demande parle-t-elle d'un espace ? Sinon, ce n'est pas une location. */
function soha_crm_est_une_location($champs) {
    return '' !== soha_crm_champ($champs, 'espace')
        || '' !== soha_crm_champ($champs, 'estim_espace');
}

/**
 * Construit la réservation à partir des champs d'une demande.
 *
 * @return array|null La réservation au format du CRM, ou null si la demande
 *                    ne concerne pas une location.
 */
function soha_crm_reservation_depuis($champs, $contact_id, $jour_recu) {
    if (!soha_crm_est_une_location($champs)) {
        return null;
    }

    /* L'espace : celui du formulaire d'abord, celui de l'estimateur ensuite —
       le premier est ce que la personne a choisi en dernier. */
    $brut = soha_crm_champ($champs, 'espace');
    if ('' === $brut) {
        $brut = soha_crm_champ($champs, 'estim_espace');
    }
    $table  = soha_crm_espaces();
    $espace = isset($table[$brut]) ? $table[$brut] : $brut;

    /* La date souhaitée. Un champ « date » d'Elementor arrive en AAAA-MM-JJ ;
       s'il arrive autrement, on ne devine pas — on le dit dans la note. */
    $date_brute = soha_crm_champ($champs, 'date');
    $date = '';
    $date_douteuse = '';
    if ('' !== $date_brute) {
        if (preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $date_brute, $m)
            && checkdate((int) $m[2], (int) $m[3], (int) $m[1])) {
            $date = $date_brute;
        } else {
            $date_douteuse = $date_brute;
        }
    }

    /* Le tarif affiché arrive en clair : « 400 $ +tx ». On en extrait le
       nombre, et rien d'autre — c'est une estimation, pas une facture. */
    $prix   = '';
    $tarif  = soha_crm_champ($champs, 'estim_tarif');
    if ('' !== $tarif && preg_match('/(\d[\d\s\x{00A0}]*)/u', $tarif, $m)) {
        $prix = (string) (int) preg_replace('/[^\d]/', '', $m[1]);
    }

    /* « Ponctuel » passe tel quel ; « Récurrent (résident·e) » devient
       « Récurrent » — la liste du CRM le prévoit. On ne choisit pas à sa place
       entre hebdomadaire et mensuel : elle seule le sait. */
    $freq = soha_crm_champ($champs, 'frequence');
    if ('' !== $freq && 'Ponctuel' !== $freq) {
        $freq = 'Récurrent';
    }
    if ('' === $freq) {
        $freq = 'Ponctuel';
    }

    /* Tout ce qui n'a pas de case à lui va dans la note, en clair. */
    $bouts = array();
    foreach (array(
        'journee' => 'Type de journée',
        'plage'   => 'Plage',
        'usage'   => 'Pour',
        'vousetes'=> 'Profil',
        'details' => 'Détails',
    ) as $id => $mot) {
        $v = soha_crm_champ($champs, $id);
        if ('' !== $v) {
            $bouts[] = $mot . ' : ' . $v;
        }
    }
    if ('' !== $date_douteuse) {
        $bouts[] = 'Date demandée (non reconnue) : ' . $date_douteuse;
    }
    if ('' !== $tarif) {
        $bouts[] = 'Estimation affichée : ' . $tarif;
    }
    $bouts[] = 'Demande reçue le ' . $jour_recu;

    return array(
        'id'         => wp_generate_uuid4(),
        'contactId'  => (string) $contact_id,
        'espace'     => $espace,
        'date'       => $date,
        'debut'      => '',      // l'heure exacte se convient au téléphone
        'fin'        => '',
        'prix'       => $prix,
        'recurrence' => $freq,
        'paiement'   => 'devis', // rien n'est confirmé tant que Mala ne l'a pas dit
        'note'       => implode(' · ', $bouts),
    );
}

/** Une phrase pour l'écran : ce que la réservation créée contient. */
function soha_crm_resumer_reservation($r) {
    $bouts = array($r['espace']);
    if ('' !== $r['date']) {
        $bouts[] = 'le ' . date_i18n('j F Y', strtotime($r['date']));
    }
    if ('' !== $r['prix']) {
        $bouts[] = $r['prix'] . ' $';
    }
    return implode(', ', $bouts);
}
