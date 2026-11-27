# Épisode du jour — mode d'emploi pour Claude

**Depuis le 28/11/2026 : plus de Shorts.** Chaque jour, une tâche programmée crée **un nouvel épisode de la
mini-série « Nuno & Friends »** : une histoire animée **de 2 à 3 minutes, en 16:9 (1920x1080)**, pour les 3-6 ans,
et la programme sur YouTube en **vidéo classique** (pas Short) via Metricool. Personne ne vérifie avant la
publication : la qualité dépend de toi.

**Lis d'abord `SERIE.md`** (la bible de la série : personnages, monde, épisodes déjà faits).

**LANGUE : la chaîne est en ANGLAIS.** Tout ce que voit ou entend le spectateur est en anglais
(titre à l'écran, narration, bulles, « The End! », titre YouTube, description, tags, hashtags).
Ce mode d'emploi reste en français, et le résumé final envoyé à l'utilisateur aussi.

## Règles de contenu
- Public : enfants de 3 à 6 ans. Histoire douce, positive, sans peur, sans violence, sans marque,
  sans personnage connu (pas de Disney, Pokémon, Pat'Patrouille, etc.). Personnages originaux uniquement.
- **Les héros sont toujours Nuno, Lulu et Flutter** (voir `SERIE.md`), avec **le même dessin** que dans
  `template/anim_pixel.py` (`goat()`, `lamb()`, `butterfly()`). Chaque épisode ajoute **un invité** original
  (nouveau, ou un invité récurrent de `SERIE.md`).
- Chaque épisode doit être **différent** des précédents (`SERIE.md` et `HISTOIRES.md`) : autre invité, autre
  problème, autre lieu ou saison ou moment (matin, soir, nuit, pluie, neige, vent, automne…), autre geste d'aide.
- Valeurs : partage, entraide, amitié, persévérance, découverte, politesse, nature.
- Anglais très simple (niveau 3-6 ans), phrases courtes, mots faciles.
- Style : pixel art (scène dessinée en basse résolution puis agrandie), texte en pixels, musique 8-bit,
  voix « dessin animé » des personnages (sons, pas de vrais mots) + conteuse (voix off).

## Structure d'un épisode (2 à 3 min, `DURATION = 120` à `180`)
Une vraie petite histoire, pas juste « problème → solution » :
1. **Ouverture (0-6 s)** : titre « Nuno & Friends » + titre de l'épisode ; les héros sont déjà à l'écran et bougent,
   première réplique avant 1 s (ex. « Good morning, Lulu! »).
2. **Présentation (≈ 15-20 s)** : on retrouve les héros dans leur prairie, ils jouent (un petit gag).
3. **Rencontre (≈ 20 s)** : l'invité a un problème (perdu, coincé, triste, a besoin de quelque chose…).
4. **Essais ratés (≈ 40-60 s)** : **deux ou trois essais** qui ratent de façon rigolote (bruitages « boing », « oops »),
   chacun d'un personnage différent (souvent Nuno fonce en premier).
5. **La bonne idée (≈ 20-30 s)** : trouvée ensemble (« We can do it together! »), et ça marche.
6. **Fête (≈ 15-20 s)** : fin joyeuse avec une surprise (danse, cadeau, arc-en-ciel, feu d'artifice, nouvel ami…),
   puis « The End! » (2,7 s, à `DURATION - 2.7`).
On peut changer de décor en cours d'épisode (ex. prairie → forêt → colline) : `scene()` choisit le fond selon `t`.
Rythme : jamais plus de 3-4 s sans qu'il se passe quelque chose (mouvement, réplique, bruitage).

## Texte, voix off et bulles
- `CAPTIONS` (bandeau + voix off) : **15 à 25 phrases** réparties sur tout l'épisode, une toutes les 6-8 s environ.
  Chaque phrase doit tenir dans son bandeau : compte environ 2,5 mots par seconde. Si `audio_mix.py` affiche
  « ATTENTION voix off trop longue », raccourcis la phrase ou allonge le bandeau.
  Écris-les pour être **lues à voix haute** : phrases naturelles, ponctuées, sans abréviation.
- `LINES` (bulles) : **30 à 45 répliques** courtes et drôles, placées **entre** deux phrases de narration
  (la conteuse parle ~0,25 s après l'arrivée du bandeau).
- Voix off : une conteuse (Piper, voix LibriTTS n° 552, 3 demi-tons plus aiguë, hors ligne). Garde les réglages
  par défaut de `voiceover.py`. Avant de fabriquer, lance une fois `./tts_setup.sh` depuis la racine du dépôt.
  Si `build_long.sh` affiche « VOIX OFF ABSENTE », la vidéo se fait quand même sans conteuse : publie-la, mais
  **signale-le dans le résumé final**.
- Musique : varie `MELODY`/`BASS` (gamme majeure, joyeuse) ; elle boucle sur toute la durée.

## Cadrage 16:9
En 16:9, **tout le monde 1280x720 est visible** (pas de zoom ni de caméra). Donc :
- place l'action au centre (x ≈ 250 à 1030), personnages bien lisibles, rien de coupé au bord ;
- les bulles s'affichent au-dessus des têtes (`ANCHORS["<nom>"] = (x, y)` dans `scene()`) ; garde de la place
  au-dessus des personnages ; le bandeau de narration est en bas (y ≈ 630-700), le titre et « The End! » en haut ;
- les personnages peuvent se déplacer d'un bout à l'autre de l'écran : c'est même mieux que de rester sur place.
`anim_vert.py`, `build.sh` et `stills.sh` (version verticale des anciens Shorts) ne servent plus.

## Comment faire
1. Copie `template/` dans `histoires/AAAA-MM-JJ-nom/` et travaille dans ce dossier.
2. Modifie `story.py` : `SERIES = "Nuno & Friends"` (ne change pas), `TITLE` = titre de l'épisode (court,
   ≤ 28 caractères pour tenir à l'écran), `DURATION`, `TITLE_OUT` (≈ 4 s), musique, `SFX`, `CAPTIONS`, `LINES`,
   `VOICES` (garde nuno 280, lulu 430, flutter 560 ; choisis une voix pour l'invité), `HERO = "nuno"`,
   `FRIEND` = l'invité.
3. Modifie `anim_pixel.py` : **garde `goat()`, `lamb()`, `butterfly()` et `ball()` tels quels** (tu peux ajouter des
   paramètres de pose sans changer l'apparence), dessine l'invité dans une nouvelle fonction, change le décor
   (`make_back`, `stream_anim`, `sun`…), et écris `scene()` (déplacements, humeurs, effets) pour toute la durée.
   `scene()` doit toujours renvoyer `img, x, y, head`. Supprime ce qui ne sert plus (ruisseau, tronc…) si le lieu change.
4. Vérifie : `./stills_long.sh` avec **9 à 12 instants** répartis sur toute la durée (un par temps fort, dont 0 et
   la fin), puis **regarde** `hsheet.png`. Corrige tout ce qui déborde, se chevauche, est illisible ou moche.
   Recommence jusqu'à ce que ce soit propre. Vérifie que les héros ressemblent bien à ceux des épisodes précédents.
5. Fabrique : `../../tts_setup.sh` (voix off) puis `./build_long.sh ../../videos/AAAA-MM-JJ-nom.mp4`
   (≈ 1 s de calcul par seconde de vidéo : lance-le avec un long timeout, 600000 ms).
   Regarde ensuite 3-4 images extraites avec ffmpeg pour vérifier.
6. Mets à jour `SERIE.md` (ligne dans « Épisodes », nouveaux lieux, invité récurrent éventuel) et ajoute une
   ligne dans `HISTOIRES.md`, puis `git add -A && git commit && git -c push.negotiate=true push origin HEAD:main`.
7. Lien public de la vidéo :
   `https://raw.githubusercontent.com/lebobonjames4-eng/shorts-enfants/main/videos/AAAA-MM-JJ-nom.mp4`
8. Programme dans Metricool (`createScheduledPost`, blogId 8158276, fuseau Europe/Paris) :
   - providers `[{"network":"youtube"}]`, media `[lien ci-dessus]`
   - youtubeData : `title` (≤ 100 caractères, en anglais, ex. « The Lost Baby Owl 🦉 Nuno & Friends | Cartoon for Kids »),
     `type: "video"` (**PAS short**), `privacy: "public"`, `madeForKids: true`, `category: "FILM_ANIMATION"`,
     `isAiGeneratedContent: false`, quelques `tags` en anglais (nuno and friends, kids cartoon, cartoon for kids,
     bedtime story, animated story, preschool…)
   - `text` (OBLIGATOIRE, c'est la description YouTube, EN ANGLAIS) : un petit paragraphe de 4 à 6 phrases,
     enthousiaste, qui présente l'épisode (héros, invité, problème, essai raté) sans dévoiler la fin et donne
     envie de regarder jusqu'au bout ; une phrase qui invite à retrouver Nuno, Lulu et Flutter dans d'autres
     épisodes. Quelques emojis. Puis une ligne vide, puis 15 à 20 hashtags : toujours
     `#nunoandfriends #kidsstory #kidsstories #cartoon #cartoonforkids #animatedstory #storytime #bedtimestory
     #preschool #kids #funny #cute #pixelart #kidscartoon` + 3 à 5 hashtags liés à l'épisode.
     Hashtags en minuscules, sans espaces à l'intérieur d'un hashtag.
   - heure : **16:00** (heure de Paris) le jour même ; si 16:00 est passé, le lendemain 16:00.
9. En cas d'échec (rendu, push, Metricool), n'invente rien : décris l'erreur dans le résumé final.

## Le dimanche : compilation (en plus de l'épisode)
Chaque **dimanche**, après l'épisode du jour, s'il y a au moins 4 épisodes de « Nuno & Friends » :
1. `./compile.sh videos/compil-AAAA-MM-JJ.mp4 <les dossiers des 7 derniers épisodes de la série, du plus ancien au plus récent>`
   (version 16:9 en 1920x1080, ≈ 15-20 min de calcul : lance-le en arrière-plan avec `nohup … > compil.log 2>&1 &`
   et vérifie `compil.log` jusqu'à la fin). Regarde 4-5 images extraites avec ffmpeg pour vérifier.
2. Commit + push, puis programme dans Metricool à **19:30** (Paris) le jour même : youtubeData `type: "video"`,
   `madeForKids: true`, `category: "FILM_ANIMATION"`, `privacy: "public"`, titre du genre
   « Nuno & Friends 🐐🐑🦋 7 Cute Stories for Kids | Cartoon Compilation », description en anglais avec
   **chapitres** (`00:00 Titre`, calculés avec les `DURATION` de chaque `story.py`) puis 12-16 hashtags.
3. Mets la compilation dans le résumé final.

## Fin de la tâche
Envoie un court résumé : titre, épisode en une phrase (avec l'invité), durée, heure de publication,
lien Metricool, et si la voix off a bien été ajoutée.
