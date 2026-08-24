# Éditeur du Centre Soha

Site du Centre Soha rendu à partir de fichiers de contenu, avec un éditeur
en ligne (Sveltia CMS, compatible Decap — gratuit).

## Où est quoi
- `content/cours/`  : un fichier par cours (ce que l'éditeur modifie)
- `content/pages/`  : les textes/photos d'en-tête des pages
- `media/`          : les photos téléversées depuis l'éditeur
- `admin/`          : l'éditeur (page /admin + sa configuration)
- `build.py`        : le générateur (contenu -> pages du site)
- `site/`           : le dossier publié (fabriqué par build.py)

## Refabriquer le site
    python3 build.py

## Mettre en ligne
Voir le guide « soha_mise-en-ligne-editeur ».
