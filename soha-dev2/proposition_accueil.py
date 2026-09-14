#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centre Soha — la proposition de trame pour l'accueil, rendue.

Une proposition de mise en page ne se décrit pas, elle se regarde. Ce script
fabrique la page telle qu'elle serait : **les vraies photos, les vrais textes**,
pas un mot inventé et pas un gris de remplissage.

Ce qui change, et pourquoi
--------------------------
L'accueil avait cinq sections et **deux** façons de les mettre en page, toutes
en une seule colonne. Ici, cinq sections et cinq traitements distincts — la
variété n'est pas décorative : c'est elle qui dit au lecteur qu'il change de
sujet.

Le déséquilibre qu'on voyait sans le nommer : dans « Tu soignes, tu enseignes »,
deux cartes empilées à gauche et **une photo de 719 px** à droite. Le titre
« Espaces professionnels » finissait tout en bas, seul. Les trois photos sont
maintenant recadrées à la même hauteur.

    python3 proposition_accueil.py --site <dossier> --sortie proposition.html
"""

import argparse
import base64
import mimetypes
import os
import sys

# Les cinq portes, dans l'ordre où elles existent déjà sur la page.
PORTES = [
    ("01", "Se ressourcer", "soha-accueil-001.webp",
     "Yoga, qi gong, méditation, chant, théâtre, gymnastique sensorielle. "
     "Une douzaine de pratiques, chaque semaine, en salle et parfois en ligne. "
     "Aucune expérience demandée.", "Voir la semaine"),
    ("02", "Prendre soin de soi", "soha-accueil-003.webp",
     "Neuf thérapeutes et accompagnant·es : polarité, ostéopathie, massothérapie, "
     "hypnose, reiki, cranio-sacré, chant postural. Chacun·e prend ses propres "
     "rendez-vous.", "Voir les thérapeutes"),
    ("03", "Se transformer", "soha-accueil-005.webp",
     "Des formations professionnelles et des ateliers découverte, portés par le "
     "Centre ou par ses partenaires. Certains durent une soirée, d'autres toute "
     "une fin de semaine.", "Voir ce qui vient"),
    ("04", "Studio Podcast", "soha-accueil-007.webp",
     "Trois caméras, un son professionnel, deux heures à toi. Pour un balado, "
     "une capsule, ou le tournage d'une formation en ligne.", "Voir les formules"),
    ("05", "Espaces professionnels", "soha-accueil-009.webp",
     "Cinq salles, de la petite salle de soins à l'Espace Soha et ses 2 200 pi². "
     "Table, son, chauffage, climatisation : tout est déjà là.", "Voir les salles"),
]

REPERES = [
    ("Sur le Plateau", "961 Rachel Est, au cœur du quartier."),
    ("Ouvert sept jours", "Du matin au soir, selon les cours et les rendez-vous."),
    ("Membres en règle", "La plupart des thérapeutes peuvent émettre des reçus d'assurance."),
    ("On se reconnaît", "Les mêmes visages d'une semaine à l'autre."),
]


def uri(site, nom):
    chemin = os.path.join(site, "medias", nom)
    if not os.path.isfile(chemin):
        raise SystemExit("Image absente : %s" % chemin)
    t, _ = mimetypes.guess_type(chemin)
    return "data:%s;base64,%s" % (t or "image/webp",
                                  base64.b64encode(open(chemin, "rb").read()).decode())


def police(site, nom):
    chemin = os.path.join(site, "assets/polices", nom)
    if not os.path.isfile(chemin):
        return ""
    return "data:font/woff2;base64," + base64.b64encode(open(chemin, "rb").read()).decode()


def construire(site):
    hero = uri(site, "soha-accueil-plate-b4c136c1.webp")
    faces = []
    for f, fam, poids, style in (
            ("fraunces-v38-latin-500.woff2", "Fraunces", "500", "normal"),
            ("fraunces-v38-latin-600.woff2", "Fraunces", "600", "normal"),
            ("fraunces-v38-latin-italic.woff2", "Fraunces", "400", "italic"),
            ("schibsted-grotesk-v7-latin-regular.woff2", "Schibsted Grotesk", "400", "normal"),
            ("schibsted-grotesk-v7-latin-600.woff2", "Schibsted Grotesk", "600", "normal"),
            ("schibsted-grotesk-v7-latin-700.woff2", "Schibsted Grotesk", "700", "normal"),
            ("dm-mono-v16-latin-regular.woff2", "DM Mono", "400", "normal")):
        u = police(site, f)
        if u:
            faces.append("@font-face{font-family:'%s';font-weight:%s;font-style:%s;"
                         "font-display:swap;src:url(%s) format('woff2')}" % (fam, poids, style, u))

    grandes = "".join(
        '<article class="pr-porte pr-porte--large">'
        '<div class="pr-vue pr-vue--16x10"><img src="%s" alt=""%.0s></div>'
        '<p class="pr-num">%s</p><h3>%s</h3><p class="pr-dit">%s</p>'
        '<p class="pr-lien"><a href="#">%s <span aria-hidden="true">→</span></a></p>'
        '</article>' % (uri(site, img), titre, num, titre, texte, lien)
        for num, titre, img, texte, lien in PORTES[:2])

    petites = "".join(
        '<article class="pr-porte">'
        '<div class="pr-vue pr-vue--carre"><img src="%s" alt=""%.0s></div>'
        '<p class="pr-num">%s</p><h3>%s</h3><p class="pr-dit">%s</p>'
        '<p class="pr-lien"><a href="#">%s <span aria-hidden="true">→</span></a></p>'
        '</article>' % (uri(site, img), titre, num, titre, texte, lien)
        for num, titre, img, texte, lien in PORTES[2:])

    reperes = "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (t, d) for t, d in REPERES)

    return FEUILLE % {"faces": "\n".join(faces), "hero": hero,
                      "grandes": grandes, "petites": petites, "reperes": reperes}


FEUILLE = """<style>
%(faces)s
/* La proposition est rendue dans son propre monde : tout est préfixé « pr- »
   pour qu'aucune règle du document qui l'entoure ne vienne la fausser. */
.pr-ecran{--encre:#0E1A15;--ivoire:#F4F0E7;--papier:#FBF8F3;--soigner:#19A7DB;
  /* Trois teintes que j'avais INVENTÉES, et qui n'existent nulle part dans le
     CSS réellement livré : #0F7FA6 (4,30 — sous le seuil), #5A6862 et #E2DACC.
     Les deux dernières sont des quasi-doublons de teintes vraies, à 1,05 et
     1,02 — un écart que personne ne voit, et une dette que tout le monde paie.
     Elles cèdent la place aux valeurs que la feuille du site emploie déjà :
     #5A6460 (75 emplois) et #E0D8CA (65). L'italique reprend Soigner du canon. */
  --doux:#5A6460;--filet:#E0D8CA;
  --serif:"Fraunces",Georgia,"Times New Roman",serif;
  --sans:"Schibsted Grotesk",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"DM Mono",ui-monospace,Menlo,monospace;
  background:var(--papier);color:var(--encre);font-family:var(--sans);
  font-size:19px;line-height:1.6;border:1px solid var(--filet);overflow:hidden}
.pr-ecran *{box-sizing:border-box}
.pr-ecran img{display:block;width:100%%;height:100%%;object-fit:cover}
.pr-ecran h1,.pr-ecran h2,.pr-ecran h3{font-family:var(--serif);font-weight:500;
  margin:0;text-wrap:balance;letter-spacing:-.012em}
.pr-ecran h1{font-size:clamp(1.9rem,3.6vw,2.9rem);line-height:1.06}
.pr-ecran h2{font-size:clamp(1.6rem,3vw,2.4rem);line-height:1.12}
.pr-ecran h3{font-size:24px;line-height:1.2}
.pr-ecran p{margin:0}
/* L'italique sur fond clair reste ENCRE : l'italique porte déjà l'accent, et
   Soigner sur ivoire ne mesure que 2,43. C'est la clause que je viens de
   proposer — je n'allais pas l'enfreindre dans la ligne d'à côté. */
.pr-ecran em{font-style:italic;color:var(--encre)}
/* 12 px en #0F7FA6 donne 4,30 sur ivoire — sous le seuil de 4,5. L'étiquette
   passe à l'encre adoucie ; le bleu reste, sur le filet qui la précède. */
.pr-etiq{font-family:var(--mono);font-size:12px;letter-spacing:.16em;
  text-transform:uppercase;color:#3F4A45}
.pr-chapeau{color:var(--doux);max-width:46ch}
.pr-dit{font-size:16px;color:var(--doux)}
.pr-num{font-family:var(--mono);font-size:12px;color:var(--doux)}
/* Les sept liens « Voir … » — le geste principal de chaque porte — mesuraient
   20 px de haut à TOUTES les largeurs, quand le site livré impose déjà 44 px
   (WCAG 2.2, cible tactile). La boîte monte donc à 44 px.
   Et le filet quitte le BORD de la boîte pour se poser sur les LETTRES : un
   `border-bottom` sur une boîte de 44 px aurait flotté vingt pixels sous le
   mot. C'est exactement l'erreur que j'ai faite trois fois ce matin. */
.pr-lien a{display:inline-flex;align-items:center;min-height:44px;
  font-size:14px;font-weight:600;color:var(--encre);
  text-decoration:underline;text-decoration-color:var(--soigner);
  text-decoration-thickness:1.5px;text-underline-offset:4px}
.pr-lien a:hover{text-decoration-thickness:3px}
.pr-bouton{display:inline-flex;align-items:center;justify-content:center;
  min-height:44px;padding:14px 27px;font-size:14px;font-weight:600;
  text-decoration:none;color:var(--encre);border:1px solid var(--soigner);
  border-radius:0;transition:background-color 140ms cubic-bezier(.22,.61,.36,1),
  color 140ms cubic-bezier(.22,.61,.36,1)}
.pr-bouton:hover{background:var(--soigner);color:#fff}
.pr-bouton--clair{color:var(--ivoire);border-color:var(--ivoire)}
.pr-bouton--clair:hover{background:var(--ivoire);color:var(--encre)}
.pr-bouton--fantome{color:var(--ivoire);border-color:rgba(244,240,231,.34)}
.pr-bouton--fantome:hover{background:rgba(244,240,231,.12);color:var(--ivoire)}
.pr-geste{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px}

/* A — le héros. La photo tient la hauteur du texte : plus de colonne vide. */
.pr-hero{display:grid;grid-template-columns:6fr 6fr;gap:48px;align-items:center;
  padding:96px 40px;background:var(--ivoire)}
.pr-hero-dit{display:flex;flex-direction:column;gap:18px}
.pr-hero-vue{margin:0;display:flex;flex-direction:column;gap:10px}
.pr-hero-vue img{aspect-ratio:4/3}
.pr-hero-vue figcaption{font-family:var(--mono);font-size:12px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--doux)}

/* B et C — deux bandes de portes, deux échelles différentes. */
.pr-bande{padding:120px 40px 48px}
.pr-bande + .pr-bande{padding-top:48px}
.pr-tete{display:flex;flex-direction:column;gap:12px;margin-bottom:36px;max-width:62ch}
.pr-grille{display:grid;gap:32px;align-items:stretch}
.pr-grille--deux{grid-template-columns:repeat(2,1fr)}
.pr-grille--trois{grid-template-columns:repeat(3,1fr)}
.pr-porte{display:flex;flex-direction:column;gap:8px;height:100%%}
.pr-porte .pr-lien{margin-top:auto;padding-top:8px}
.pr-porte h3{margin-top:2px}
/* Le cadrage fait le rythme : 16/10 pour les deux grandes, carré pour les trois
   petites. C'est ce qui distingue les deux bandes sans changer de matière —
   et c'est ce qui empêche une photo de 719 px de faire chavirer la rangée. */
.pr-vue{overflow:hidden;background:var(--filet)}
.pr-vue--16x10{aspect-ratio:16/10}
.pr-vue--carre{aspect-ratio:1/1}

/* D — le lieu. Fond encre : la rupture se voit avant d'être lue. */
.pr-lieu{display:grid;grid-template-columns:7fr 5fr;gap:56px;align-items:center;
  padding:96px 40px;margin-top:72px;background:var(--encre);color:var(--ivoire)}
.pr-lieu h2{color:var(--ivoire)}
.pr-lieu .pr-etiq{color:var(--soigner)}
.pr-lieu em{color:var(--soigner)}
.pr-lieu-dit{display:flex;flex-direction:column;gap:16px;max-width:52ch}
.pr-lieu-dit p{color:rgba(244,240,231,.82)}
.pr-reperes{margin:0;display:grid;gap:1px;background:rgba(244,240,231,.16);align-self:start}
.pr-reperes > div{background:var(--encre);padding:16px 0 16px 20px}
.pr-reperes dt{font-family:var(--sans);font-size:16px;font-weight:600;color:var(--ivoire)}
.pr-reperes dd{margin:2px 0 0;font-size:14px;color:rgba(244,240,231,.66)}

/* E — la sortie. Courte : la page se referme au lieu de s'éteindre. */
.pr-sortie{padding:72px 40px 96px}
.pr-sortie h2{margin-bottom:28px}
.pr-chemins{display:grid;grid-template-columns:repeat(2,1fr);gap:40px;
  border-top:1px solid var(--filet);padding-top:28px}
.pr-chemins > div{display:flex;flex-direction:column;gap:10px}

@media (max-width:900px){
  .pr-hero,.pr-lieu{grid-template-columns:1fr;gap:32px;padding:56px 22px}
  .pr-bande{padding:64px 22px 32px}
  .pr-sortie{padding:48px 22px 64px}
  .pr-grille--deux,.pr-grille--trois,.pr-chemins{grid-template-columns:1fr}
  .pr-vue--carre{aspect-ratio:16/10}
}
@media (prefers-reduced-motion:reduce){.pr-ecran *{transition:none!important}}
</style>

<div class="pr-ecran" lang="fr">

<!-- A · le héros : deux colonnes, la photo cadrée à la hauteur du texte -->
<section class="pr-hero">
  <div class="pr-hero-dit">
    <p class="pr-etiq">Depuis le 961 Rachel Est</p>
    <h1>Au 961 Rachel, la porte est la&nbsp;même pour tout le monde.</h1>
    <p class="pr-chapeau">On prend soin les uns des autres. Sur le Plateau,
    sept jours sur sept.</p>
    <p class="pr-geste"><a class="pr-bouton" href="#">Voir la semaine</a></p>
  </div>
  <figure class="pr-hero-vue">
    <img src="%(hero)s" alt="Un soin, un matin au 961">
    <figcaption>Planche 01 — un soin, un matin au 961</figcaption>
  </figure>
</section>

<!-- B · deux portes larges -->
<section class="pr-bande">
  <header class="pr-tete">
    <p class="pr-etiq">Pour toi</p>
    <h2>Un cours, ou une paire de <em>mains</em></h2>
    <p class="pr-chapeau">Un mardi soir en groupe, une heure sur une table de
    massage, un atelier un samedi. Tu prends ce dont tu as besoin, quand tu en
    as besoin.</p>
  </header>
  <div class="pr-grille pr-grille--deux">%(grandes)s</div>
</section>

<!-- C · trois portes en bande, autre échelle, autre cadrage -->
<section class="pr-bande">
  <header class="pr-tete">
    <p class="pr-etiq">Pour ta pratique</p>
    <h2>Tu soignes, tu enseignes, tu enregistres</h2>
    <p class="pr-chapeau">Il te faut une salle prête à l'heure dite, un son qui
    tient, et personne pour te presser. C'est exactement ce que nous préparons.</p>
  </header>
  <div class="pr-grille pr-grille--trois">%(petites)s</div>
</section>

<!-- D · le lieu : bande sur encre, aucune photo, rupture franche -->
<section class="pr-lieu">
  <div class="pr-lieu-dit">
    <p class="pr-etiq">Le lieu</p>
    <h2>Deux portes <em>voisines</em></h2>
    <p>Le 961 pour les cours, les formations et le studio. Le 957, juste à côté,
    pour les soins, à l'étage.</p>
    <p>Un lieu change ce qui s'y passe. Une salle trop froide, un mur trop mince,
    un plancher qui craque — et l'heure est perdue. Nous nous occupons du
    chauffage, du son, des tapis et du silence, pour qu'il ne te reste qu'à faire
    ce que tu es venu·e faire.</p>
    <p>Que tu viennes pour une séance ou pour y installer ta pratique, la porte
    est la même.</p>
    <p class="pr-geste">
      <a class="pr-bouton pr-bouton--clair" href="#">Venir nous voir</a>
      <a class="pr-bouton pr-bouton--fantome" href="#">Louer une salle</a>
    </p>
  </div>
  <dl class="pr-reperes">%(reperes)s</dl>
</section>

<!-- E · la sortie : deux chemins, court -->
<section class="pr-sortie">
  <h2>Par où commencer</h2>
  <div class="pr-chemins">
    <div>
      <h3>Tu viens prendre soin de toi</h3>
      <p class="pr-dit">Choisis un cours ou une thérapeute, et réserve en ligne.
      C'est ta première fois ?</p>
      <p class="pr-lien"><a href="#">Lis ceci d'abord <span aria-hidden="true">→</span></a></p>
    </div>
    <div>
      <h3>Tu cherches un lieu pour travailler</h3>
      <p class="pr-dit">Une salle de soins à la demi-journée, une grande salle pour
      une formation, le studio pour un tournage. Dis-nous ce qu'il te faut.</p>
      <p class="pr-lien"><a href="#">Voir les espaces <span aria-hidden="true">→</span></a></p>
    </div>
  </div>
</section>

</div>
"""


def main():
    ap = argparse.ArgumentParser(description="La proposition de trame pour l'accueil.")
    ap.add_argument("--site", required=True, help="dossier du site statique (pour les médias)")
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    open(a.sortie, "w", encoding="utf-8").write(construire(a.site))
    print("Écrit dans « %s » — %.2f Mo" % (a.sortie, os.path.getsize(a.sortie) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
