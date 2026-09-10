#!/usr/bin/env python3
"""Banc d'essai : imite la route REST de l'extension, pour de vrai, sur HTTP.

On ne simule pas `fetch` : on le laisse partir. C'est la seule façon de voir si
l'adaptateur parle bien la langue que le PHP écoute — en-tête de jeton compris.
"""
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RACINE = sys.argv[1]
PORT = int(sys.argv[2])
JETON = "jeton-de-banc"
ETAT = {"valeur": "", "revision": 0}
JOURNAL = []
VERROU = threading.Lock()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, corps):
        b = json.dumps(corps).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.split("?")[0] == "/wp-json/soha-crm/v1/etat":
            if self.headers.get("X-WP-Nonce") != JETON:
                return self._json(403, {"code": "jeton", "message": "jeton absent"})
            with VERROU:
                JOURNAL.append(["GET", 200, len(ETAT["valeur"])])
                return self._json(200, dict(ETAT))
        chemin = os.path.join(RACINE, self.path.lstrip("/").split("?")[0])
        if not os.path.isfile(chemin):
            return self._json(404, {"message": "introuvable"})
        ext = os.path.splitext(chemin)[1]
        t = {".html": "text/html", ".js": "application/javascript",
             ".css": "text/css", ".woff2": "font/woff2"}.get(ext, "application/octet-stream")
        b = open(chemin, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", t + ("; charset=utf-8" if ext in (".html", ".js", ".css") else ""))
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        if self.path.split("?")[0] != "/wp-json/soha-crm/v1/etat":
            return self._json(404, {"message": "introuvable"})
        jeton = self.headers.get("X-WP-Nonce")
        if not jeton and "_wpnonce=" in self.path:
            jeton = self.path.split("_wpnonce=")[1].split("&")[0]
        if jeton != JETON:
            return self._json(403, {"code": "jeton", "message": "jeton absent"})
        n = int(self.headers.get("Content-Length", 0))
        try:
            corps = json.loads(self.rfile.read(n).decode())
        except Exception:
            return self._json(400, {"message": "JSON invalide"})
        with VERROU:
            if not isinstance(corps, dict) or not isinstance(corps.get("valeur"), str):
                JOURNAL.append(["POST", 400, 0])
                return self._json(400, {"code": "corps", "message": "valeur manquante"})
            try:
                decode = json.loads(corps["valeur"])
            except Exception:
                JOURNAL.append(["POST", 400, 0])
                return self._json(400, {"code": "json", "message": "registre illisible"})
            if not isinstance(decode, (dict, list)):
                JOURNAL.append(["POST", 400, 0])
                return self._json(400, {"code": "forme", "message": "forme inattendue"})
            envoyee = int(corps.get("revision", ETAT["revision"]))
            if envoyee != ETAT["revision"]:
                JOURNAL.append(["POST", 409, 0])
                return self._json(409, {"code": "revision", "message": "révision périmée",
                                        "valeur": ETAT["valeur"], "revision": ETAT["revision"]})
            ETAT["valeur"] = corps["valeur"]
            ETAT["revision"] += 1
            JOURNAL.append(["POST", 200, len(corps["valeur"])])
            return self._json(200, {"revision": ETAT["revision"], "taille": len(corps["valeur"])})

    def do_PUT(self):
        """Réservé au banc : force une révision serveur, pour provoquer un conflit."""
        if self.path == "/banc/avancer":
            with VERROU:
                ETAT["revision"] += 1
            return self._json(200, {"revision": ETAT["revision"]})
        if self.path == "/banc/journal":
            with VERROU:
                return self._json(200, {"journal": JOURNAL, "etat": ETAT})
        return self._json(404, {})


ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
