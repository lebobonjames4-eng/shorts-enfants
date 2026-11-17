# Short du jour — mode d'emploi pour Claude

Chaque jour, une tâche programmée crée **une nouvelle histoire animée de 25 à 35 s pour les 3-6 ans**
et la programme sur YouTube (Shorts) via Metricool. Personne ne vérifie avant la publication :
la qualité dépend de toi.

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
  `CAPTIONS`, `LINES` et `SFX` doivent être recalés sur cette durée (« Fin ! » arrive à DURATION - 2.7).
- Français simple, phrases courtes. Bandeau de narration : 5 phrases (une par temps).
  Bulles : 8 à 12 répliques courtes et drôles. Varie aussi `MELODY`/`BASS` (gamme majeure, joyeuse).
- Chaque jour doit être **différent** des histoires de `HISTOIRES.md` : autre héros, autre ami,
  autre décor ou moment (jour, nuit, mer, neige, forêt, jardin, espace…), autre geste d'aide.
  Varie aussi les couleurs. YouTube pénalise les vidéos trop répétitives.
- Garde le style : pixel art (scène dessinée en basse résolution puis agrandie), texte en pixels,
  musique 8-bit, voix « dessin animé » (sons, pas de vrais mots).

## Accroche (très important pour les vues)
Sur les Shorts, tout se joue dans la **première seconde** : sinon le spectateur swipe.
- Le héros est **à l'écran dès la 1re image** et bouge tout de suite (pas d'entrée depuis le bord).
- Première réplique dans la bulle **avant 0,5 s** (ex. « Coucou ! Je suis Tobi ! »), avec un geste drôle.
- Le titre apparaît en moins d'une seconde et s'envole à `TITLE_OUT` (≈ 3 s) ; il ne doit jamais
  retarder l'action. Première narration vers 3,5 s.
- Les 5 temps sont serrés : environ 3-4 s par temps, pas de moment vide.
- « Fin ! » court (2,7 s) pour que la boucle du Short reparte vite.
- Titre YouTube accrocheur, si possible avec une petite question ou un enjeu
  (ex. « Le bonhomme de neige a perdu son nez ! ⛄ Histoire animée pour enfants »).

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
5. Fabrique : `./build.sh ../../videos/AAAA-MM-JJ-nom.mp4` (≈20-30 s).
6. Ajoute une ligne dans `HISTOIRES.md`, puis `git add -A && git commit && git push`.
7. Lien public de la vidéo :
   `https://raw.githubusercontent.com/lebobonjames4-eng/shorts-enfants/main/videos/AAAA-MM-JJ-nom.mp4`
8. Programme dans Metricool (`createScheduledPost`, blogId 8158276, fuseau Europe/Paris) :
   - providers `[{"network":"youtube"}]`, media `[lien ci-dessus]`
   - youtubeData : `title` (« Titre ☁️ Histoire animée pour enfants », ≤ 100 caractères),
     `type: "short"`, `privacy: "public"`, `madeForKids: true`, `category: "FILM_ANIMATION"`,
     `isAiGeneratedContent: false`, quelques `tags` (histoire pour enfants, dessin animé, conte…)
   - `text` (OBLIGATOIRE, c'est la description YouTube) : un petit paragraphe de 4 à 6 phrases,
     enthousiaste et accrocheur, qui raconte le début de l'histoire (héros, problème, essai raté)
     sans dévoiler toute la fin, dit que c'est une histoire trop cool / rigolo / mignonne et donne
     envie de regarder jusqu'au bout (ex. « Pico, un petit nuage curieux, découvre une fleur toute
     triste… Il essaie de l'aider, mais oups, rien ne se passe comme prévu ! 😂 Va-t-il réussir ?
     Une histoire trop mignonne et rigolote sur l'entraide, parfaite pour les 3-6 ans ! 🌈 »).
     Quelques emojis bienvenus. Puis une ligne vide, puis 15 à 20 hashtags :
     toujours `#shorts #histoirepourenfants #dessinanime #contepourenfants #enfants #maternelle
     #drole #rigolo #mignon #pixel #pixelart #jeu #jeuvideo #retro`
     + 3 à 6 hashtags liés à l'histoire du jour (ex. #nuage #fleur #arcenciel #entraide #amitie).
     Le but est d'attirer un maximum de spectateurs : ton fun et accrocheur dans la description.
     Hashtags en minuscules, sans accents ni espaces à l'intérieur d'un hashtag.
   - heure : **17:00** (heure de Paris) le jour même ; si 17:00 est passé, le lendemain 17:00.
9. En cas d'échec (rendu, push, Metricool), n'invente rien : décris l'erreur dans le résumé final.

## Fin de la tâche
Envoie un court résumé : titre, histoire en une phrase, heure de publication, lien Metricool.
