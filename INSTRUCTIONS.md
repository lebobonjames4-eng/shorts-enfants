# Short du jour — mode d'emploi pour Claude

Chaque jour, une tâche programmée crée **une nouvelle histoire animée de 25 à 35 s pour les 3-6 ans**
et la programme sur YouTube (Shorts) via Metricool. Personne ne vérifie avant la publication :
la qualité dépend de toi.

**LANGUE : depuis le 18/11/2026, la chaîne est en ANGLAIS.** Tout ce que voit le spectateur est en anglais
(titre à l'écran, narration, bulles, « The End! », titre YouTube, description, tags, hashtags).
Ce mode d'emploi reste en français, et le résumé final envoyé à l'utilisateur aussi.

## Règles de contenu
- Public : enfants de 3 à 6 ans. Histoire douce, positive, sans peur, sans violence, sans marque,
  sans personnage connu (pas de Disney, Pokémon, Pat'Patrouille, etc.). Personnages originaux uniquement.
- L'histoire doit être **un peu développée**, pas juste « problème → solution ». Structure en 5 temps :
  1. présentation du héros (avec un trait de caractère : curieux, maladroit, gourmand, timide…) ;
  2. rencontre avec un ami qui a un problème ;
  3. **un premier essai qui rate de façon rigolote** (bruitage "oops" ou "boing") ;
  4. une bonne idée, souvent trouvée ensemble, et ça marche ;
  5. une fin joyeuse avec une petite surprise (cadeau, danse, arc-en-ciel, feu d'artifice, nouvel ami…).
  Valeurs : partage, entraide, amitié, persévérance, découverte, politesse, nature.
- Un 3e personnage secondaire est le bienvenu (oiseau, papillon, escargot…), s'il reste lisible.
- Durée : `DURATION = 25` à `35` dans `story.py` (un Short court et regardé jusqu'au bout marche mieux qu'un long). Toutes les animations de `scene()` et les temps de
  `CAPTIONS`, `LINES` et `SFX` doivent être recalés sur cette durée (« The End! » arrive à DURATION - 2.7).
- Anglais très simple (niveau 3-6 ans), phrases courtes, mots faciles à lire et à comprendre. Bandeau de narration : 5 phrases (une par temps).
  Bulles : 8 à 12 répliques courtes et drôles. Varie aussi `MELODY`/`BASS` (gamme majeure, joyeuse).
- Chaque jour doit être **différent** des histoires de `HISTOIRES.md` : autre héros, autre ami,
  autre décor ou moment (jour, nuit, mer, neige, forêt, jardin, espace…), autre geste d'aide.
  Varie aussi les couleurs. YouTube pénalise les vidéos trop répétitives.
- Garde le style : pixel art (scène dessinée en basse résolution puis agrandie), texte en pixels,
  musique 8-bit, voix « dessin animé » des personnages (sons, pas de vrais mots).

## Voix off (depuis le 23/11/2026)
Une conteuse (voix de synthèse Piper, anglais, hors ligne) lit à voix haute les 5 phrases de `CAPTIONS`.
- Avant `./build.sh`, lance une fois `./tts_setup.sh` depuis la racine du dépôt (télécharge Piper et la voix
  depuis GitHub dans `~/.cache/tts`, ≈ 85 Mo). `voiceover.py` (copié avec `template/`) fait le reste.
- Écris les `CAPTIONS` pour être **lues à voix haute** : phrases naturelles, ponctuées, sans abréviation.
  Chaque phrase doit tenir dans son bandeau : compte environ 2,5 mots par seconde. Si `audio_mix.py` affiche
  « ATTENTION voix off trop longue », raccourcis la phrase ou allonge le bandeau.
- Évite les répliques de bulles pendant la voix off (la conteuse parle ~0,25 s après l'arrivée du bandeau) :
  place-les plutôt entre deux phrases de narration. Les petites voix sont baissées automatiquement sous la conteuse.
- Si `build.sh` affiche « VOIX OFF ABSENTE » (téléchargement ou Piper bloqué), la vidéo se fait quand même sans
  conteuse : publie-la, mais **signale-le dans le résumé final**.

## Cadrage : des personnages GRANDS (depuis le 22/11/2026)
Sur un téléphone, de petits personnages perdus en bas d'un grand ciel = swipe. `anim_vert.py` (template) montre
donc le monde **zoomé x1,5** : seule une fenêtre de **480 unités de large** et de **y = 240 à 720** est visible
dans la version verticale.
- Garde toute l'action (héros, ami, bulles, objets importants) entre **y = 300 et y = 720** et dans 480 unités de large.
  Les éléments très hauts (soleil, lune, étoiles) vont dans le panneau du haut (`anim_vert.py`).
- Définis `cam(t)` dans `anim_pixel.py` : le centre x de la caméra, qui **suit l'action** (fonction `path()` avec
  des pans doux de ~1 s). Sans `cam`, la caméra se centre entre le héros et l'ami.
- Bulles : remplis `ANCHORS["<nom>"] = (x, y)` (point au-dessus de la tête) dans `scene()` ; `anim_vert` les place.
- Exemple complet : `histoires/2026-11-22-pippa-le-caneton/`.
- Dans `vsheet.png`, vérifie que **personne n'est coupé** au bord et que les personnages occupent une bonne
  partie de l'écran.

## Accroche (très important pour les vues)
Sur les Shorts, tout se joue dans la **première seconde** : sinon le spectateur swipe.
- Le héros **et l'ami** sont **à l'écran dès la 1re image** ; l'enjeu se voit tout de suite (l'ami est déjà triste,
  coincé, mouillé…) et le héros bouge (pas d'entrée depuis le bord).
- Première réplique dans la bulle **avant 0,5 s** (ex. « Coucou ! Je suis Tobi ! »), avec un geste drôle.
- Le titre apparaît en moins d'une seconde et s'envole à `TITLE_OUT` (≈ 3 s) ; il ne doit jamais
  retarder l'action. Première narration vers 3,5 s.
- Les 5 temps sont serrés : environ 3-4 s par temps, pas de moment vide.
- « The End! » court (2,7 s) pour que la boucle du Short reparte vite.
- Titre YouTube accrocheur et COURT (≤ 50 caractères avant l'emoji), centré sur l'enjeu de l'ami ou une question,
  pas sur le nom du héros (ex. « The Snowman Lost His Nose! ⛄ Animated Story for Kids »,
  « Can Bunny Get Home Before Dark? 🌙 Animated Story for Kids »).

## Comment faire
1. Copie `template/` dans `histoires/AAAA-MM-JJ-nom/` et travaille dans ce dossier.
2. Modifie `story.py` (titre, narration, répliques, voix, noms HERO/FRIEND).
3. Modifie le dessin dans `anim_pixel.py` : remplace ou adapte `pico()` (héros), `flower()` (ami),
   le décor (`make_sky`, `make_hills`, `sun`, `rainbow`…), les déplacements et humeurs dans `scene()`.
   `scene()` doit toujours renvoyer `img, x, y, head` (position du héros, et point au-dessus de la tête
   de l'ami pour les bulles). La partie haute de l'écran vertical (titre, narration, « Fin ! ») est
   dans `anim_vert.py` (ciel `make_top_sky`, soleil). Adapte-la si le décor change (ex. nuit = lune).
4. Vérifie : `./stills.sh` avec 6 à 8 instants répartis sur toute la durée (un par temps fort), puis **regarde** `vsheet.png`. Inclus toujours l'instant 0 : la toute première image doit déjà montrer le héros et donner envie. Corrige tout ce qui déborde,
   se chevauche, est illisible ou moche. Recommence jusqu'à ce que ce soit propre.
5. Fabrique : `../../tts_setup.sh` (voix off) puis `./build.sh ../../videos/AAAA-MM-JJ-nom.mp4` (≈20-30 s).
6. Ajoute une ligne dans `HISTOIRES.md`, puis `git add -A && git commit && git push`.
7. Lien public de la vidéo :
   `https://raw.githubusercontent.com/lebobonjames4-eng/shorts-enfants/main/videos/AAAA-MM-JJ-nom.mp4`
8. Programme dans Metricool (`createScheduledPost`, blogId 8158276, fuseau Europe/Paris) :
   - providers `[{"network":"youtube"}]`, media `[lien ci-dessus]`
   - youtubeData : `title` (« Title ☁️ Animated Story for Kids », ≤ 100 caractères, en anglais),
     `type: "short"`, `privacy: "public"`, `madeForKids: true`, `category: "FILM_ANIMATION"`,
     `isAiGeneratedContent: false`, quelques `tags` en anglais (kids story, cartoon for kids, bedtime story, animated story…)
   - `text` (OBLIGATOIRE, c'est la description YouTube, EN ANGLAIS) : un petit paragraphe de 4 à 6
     phrases, enthousiaste et accrocheur, qui raconte le début de l'histoire (héros, problème, essai
     raté) sans dévoiler toute la fin, dit que c'est une histoire super mignonne / drôle et donne
     envie de regarder jusqu'au bout (ex. « Pico, a curious little cloud, finds a very sad flower…
     He tries to help, but oops, nothing goes as planned! 😂 Will he make it? A super cute and
     funny story about helping friends, perfect for kids ages 3-6! 🌈 »).
     Quelques emojis bienvenus. Puis une ligne vide, puis 15 à 20 hashtags :
     toujours `#shorts #kidsstory #kidsstories #cartoon #cartoonforkids #animatedstory
     #storytime #bedtimestory #preschool #kids #funny #cute #pixel #pixelart #retro`
     + 3 à 5 hashtags liés à l'histoire du jour (ex. #cloud #flower #rainbow #kindness #friendship).
     Le but est d'attirer un maximum de spectateurs : ton fun et accrocheur dans la description.
     Hashtags en minuscules, sans espaces à l'intérieur d'un hashtag.
   - heure : **16:00** (heure de Paris) le jour même ; si 16:00 est passé, le lendemain 16:00.
9. En cas d'échec (rendu, push, Metricool), n'invente rien : décris l'erreur dans le résumé final.

## Le dimanche : compilation longue (en plus du Short)
Chez les 3-6 ans, beaucoup de vues viennent des vidéos longues (regardées sur tablette ou TV). Chaque **dimanche**,
après le Short du jour :
1. `./compile.sh videos/compil-AAAA-MM-JJ.mp4 <les 7 derniers dossiers d'histoires en anglais, du plus ancien au plus récent>`
   (version 16:9 en 1920x1080, ≈1 min de calcul). Regarde 4-5 images extraites avec ffmpeg pour vérifier.
2. Commit + push, puis programme dans Metricool à **19:30** (Paris) le jour même : youtubeData `type: "video"`
   (PAS short), `madeForKids: true`, `category: "FILM_ANIMATION"`, `privacy: "public"`, titre du genre
   « 7 Cute Animal Stories for Kids 🐻🦉🐸 Bedtime Stories Compilation », description en anglais avec
   **chapitres** (`00:00 Titre`, calculés avec les `DURATION` de chaque `story.py`) puis 12-16 hashtags.
3. Mets la compilation dans le résumé final.

## Fin de la tâche
Envoie un court résumé : titre, histoire en une phrase, heure de publication, lien Metricool,
et si la voix off a bien été ajoutée.
