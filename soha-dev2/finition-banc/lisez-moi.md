# Le banc du contrôle après import

Quatre contrôles, éprouvés sur un vrai WordPress avec de vrais défauts
fabriqués exprès. Un contrôle qu'on n'a jamais vu trouver quelque chose ne
protège de rien.

    sh ../crm-banc/wordpress/preparer.sh          # le même WordPress jetable
    cp -r ../finition-modele wordpress/wp-content/plugins/centre-soha
    sh banc.sh

29 vérifications. Le banc fabrique, dans la base : une pièce jointe en double
(`-1`) à côté de son originale, un nom qui finit par un chiffre (qui n'est pas
un doublon), un « -2 » sans jumeau (qui n'en est pas un non plus), une page qui
demande une image absente, un formulaire sans destinataire à côté d'un
formulaire correct, un formulaire qui n'envoie pas de courriel du tout, et des
liens vers un mauvais préfixe à côté de liens justes.

Il fait aussi croire à WordPress qu'il est installé dans `/dev` — comme le site
de Mala. Sans ça, on éprouverait le seul cas où le contrôle des liens ne
s'applique pas.

## Trois défauts que ce banc a trouvés dans mes propres contrôles

1. **Les images n'étaient jamais retrouvées.** Elementor range son arbre en
   JSON, où les barres obliques sont échappées : `http:\/\/…\/wp-content\/…`.
   Chercher une adresse normale là-dedans ne trouve rien — et ne rien trouver
   ressemble beaucoup à n'avoir rien à trouver. C'est exactement le piège qui
   avait déjà fait rater le premier recensement des images, en juillet.

2. **Le contrôle des liens accusait tout un site installé à la racine.** Là, il
   n'y a pas de préfixe à comparer : `/dev2/contact/` y est une adresse comme
   une autre. Le contrôle se tait maintenant, et le dit.

3. **Le banc lui-même mentait.** Pour simuler l'installation dans `/dev`, il
   filtrait `home_url` — qui reçoit l'adresse complète, chemin compris. Les
   adresses d'images devenaient `…/wp-content/uploads/x.webp/dev/`, et le
   contrôle des images paraissait aveugle pour une raison qui n'était pas la
   sienne. Il filtre l'option, désormais.
