<?php
/**
 * Un faux Mailchimp, pour le banc.
 *
 * Je n'ai pas de compte Mailchimp, et je n'en veux pas dans un essai : un banc
 * qui dépend d'un service payant à l'autre bout du continent n'est plus un banc.
 * Ce fichier intercepte les appels sortants de WordPress et répond comme le fait
 * l'API v3 — mêmes chemins, même authentification, mêmes formes d'erreur.
 *
 * Ce qu'il prouve : que l'extension frappe la bonne adresse, avec la bonne
 * authentification, le bon corps, et qu'elle comprend les réponses documentées.
 * Ce qu'il ne prouve pas : que Mailchimp accepte. Ça, seule la vraie clé de Mala
 * le dira, et c'est à ça que sert le bouton « Tester la liaison ».
 */

if (!defined('ABSPATH')) {
    exit;
}

class Faux_Mailchimp {

    public static $appels = array();
    public static $membres = array();
    public static $panne = false;      // simule un service qui ne répond pas
    public static $refus = null;       // force un refus : array(statut, detail)

    /**
     * Comment répondre à un PUT sur une adresse déjà désabonnée.
     *
     * Les deux formes existent dans la nature et je ne sais pas laquelle Mala
     * rencontrera : Mailchimp peut refuser avec un 400 « Member In Compliance
     * State », ou accepter par un 200 en renvoyant simplement
     * « status: unsubscribed » — puisque notre corps n'envoie jamais `status`,
     * il n'y a rien à refuser. Le banc essaie donc les deux, et l'extension doit
     * faire la même chose dans les deux cas : redresser la fiche.
     */
    public static $desabonnee = 'conformite';   // 'conformite' | 'silencieux'

    public static function brancher() {
        add_filter('pre_http_request', array(__CLASS__, 'repondre'), 10, 3);
    }

    public static function oublier() {
        self::$appels = array();
        self::$membres = array();
        self::$panne = false;
        self::$refus = null;
        self::$desabonnee = 'conformite';
    }

    private static function json($statut, $corps) {
        return array(
            'headers'  => array(),
            'body'     => wp_json_encode($corps),
            'response' => array('code' => $statut, 'message' => ''),
            'cookies'  => array(),
            'filename' => null,
        );
    }

    public static function repondre($faux, $args, $url) {
        if (false === strpos($url, 'api.mailchimp.com')) {
            return $faux;                // pas pour nous
        }

        $methode = isset($args['method']) ? $args['method'] : 'GET';
        $corps   = isset($args['body']) ? json_decode((string) $args['body'], true) : null;
        $chemin  = preg_replace('#^https://[^/]+/3\.0/#', '', $url);

        self::$appels[] = array('methode' => $methode, 'chemin' => $chemin, 'corps' => $corps,
                                'entetes' => isset($args['headers']) ? $args['headers'] : array());

        if (self::$panne) {
            return new WP_Error('http_request_failed', 'cURL error 28: Operation timed out');
        }

        /* L'authentification, comme chez eux : Basic, n'importe quel nom, la clé
           comme mot de passe. */
        $auth = isset($args['headers']['Authorization']) ? $args['headers']['Authorization'] : '';
        $cle  = '';
        if (0 === strpos($auth, 'Basic ')) {
            $paire = base64_decode(substr($auth, 6));
            $bouts = explode(':', $paire, 2);
            $cle = isset($bouts[1]) ? $bouts[1] : '';
        }
        if ('bonne-cle-us21' !== $cle) {
            return self::json(401, array(
                'type' => 'https://mailchimp.com/developer/marketing/docs/errors/',
                'title' => 'API Key Invalid', 'status' => 401,
                'detail' => "Your API key may be invalid, or you've attempted to access the wrong datacenter.",
            ));
        }

        if (self::$refus) {
            return self::json(self::$refus[0], array(
                'title' => 'Forbidden', 'status' => self::$refus[0], 'detail' => self::$refus[1],
            ));
        }

        /* GET /3.0/ — le compte */
        if ('' === $chemin || '/' === $chemin) {
            return self::json(200, array('account_name' => 'Centre Soha', 'email' => 'info@centresoha.com'));
        }

        /* GET /3.0/lists — les audiences */
        if (0 === strpos($chemin, 'lists?')) {
            return self::json(200, array('lists' => array(
                array('id' => 'aud961', 'name' => 'Infolettre du Centre Soha', 'stats' => array('member_count' => 214)),
                array('id' => 'autre',  'name' => 'Vieille liste',            'stats' => array('member_count' => 3)),
            )));
        }

        /* .../members/{hash}/tags */
        if (preg_match('#^lists/([^/]+)/members/([0-9a-f]{32})/tags$#', $chemin, $m)) {
            if (!isset(self::$membres[$m[2]])) {
                return self::json(404, array('title' => 'Resource Not Found', 'status' => 404,
                                             'detail' => 'The requested resource could not be found.'));
            }
            self::$membres[$m[2]]['tags'] = $corps['tags'];
            return self::json(204, array());
        }

        /* PUT / PATCH .../members/{hash} */
        if (preg_match('#^lists/([^/]+)/members/([0-9a-f]{32})$#', $chemin, $m)) {
            $hash = $m[2];
            if ('PUT' === $methode) {
                $existe = isset(self::$membres[$hash]);
                /* Le vrai Mailchimp refuse de réinscrire quelqu'un qui s'est
                   désabonné : c'est le cas d'erreur qui compte le plus ici. */
                if ($existe && 'unsubscribed' === self::$membres[$hash]['status']) {
                    if ('silencieux' === self::$desabonnee) {
                        /* 200, et c'est tout : l'adresse reste désabonnée et
                           rien dans le code de réponse ne le dit. C'est le cas
                           traître — celui où un client naïf croit avoir réussi. */
                        return self::json(200, self::$membres[$hash]);
                    }
                    return self::json(400, array(
                        'title' => 'Member In Compliance State', 'status' => 400,
                        'detail' => 'This contact was permanently deleted or unsubscribed and cannot be re-imported.',
                    ));
                }
                if (!$existe) {
                    self::$membres[$hash] = array(
                        'email_address' => $corps['email_address'],
                        'status' => $corps['status_if_new'],
                        'merge_fields' => isset($corps['merge_fields']) ? $corps['merge_fields'] : array(),
                        'tags' => array(),
                    );
                } else {
                    self::$membres[$hash]['merge_fields'] = isset($corps['merge_fields'])
                        ? $corps['merge_fields'] : self::$membres[$hash]['merge_fields'];
                }
                return self::json(200, self::$membres[$hash]);
            }
            if ('PATCH' === $methode) {
                if (!isset(self::$membres[$hash])) {
                    return self::json(404, array('title' => 'Resource Not Found', 'status' => 404,
                                                 'detail' => 'The requested resource could not be found.'));
                }
                self::$membres[$hash]['status'] = $corps['status'];
                return self::json(200, self::$membres[$hash]);
            }
        }

        return self::json(404, array('title' => 'Resource Not Found', 'status' => 404,
                                     'detail' => 'Chemin non prévu par le faux Mailchimp : ' . $chemin));
    }

    /** Le membre correspondant à une adresse, comme Mailchimp l'indexe. */
    public static function membre($courriel) {
        $h = md5(strtolower($courriel));
        return isset(self::$membres[$h]) ? self::$membres[$h] : null;
    }
}
