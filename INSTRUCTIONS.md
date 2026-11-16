# Short du jour — mode d'emploi pour Claude

Chaque jour, une tâche programmée crée **une nouvelle histoire animée de 30 s pour les 3-6 ans**
et la programme sur YouTube (Shorts) via Metricool. Personne ne vérifie avant la publication :
la qualité dépend de toi.

## Règles de contenu
- Public : enfants de 3 à 6 ans. Histoire douce, positive, sans peur, sans violence, sans marque,
  sans personnage connu (pas de Disney, Pokémon, Pat'Patrouille, etc.). Personnages originaux uniquement.
- Une histoire = un petit problème + une aide/gentillesse + une fin joyeuse. Valeurs : partage, entraide,
  amitié, découverte, politesse, nature.
- Français simple, phrases courtes. Bandeau de narration : 3 phrases. Bulles : 5 à 7 répliques courtes.
- Chaque jour doit être **différent** des histoires de `HISTOIRES.md` : autre héros, autre ami,
  autre décor ou moment (jour, nuit, mer, neige, forêt, jardin, espace…), autre geste d'aide.
  Varie aussi les couleurs. YouTube pénalise les vidéos trop répétitives.
- Garde le style : pixel art (scène dessinée en basse résolution puis agrandie), texte en pixels,
  musique 8-bit, voix « dessin animé » (sons, pas de vrais mots).

## Comment faire
1. Copie `template/` dans `histoires/AAAA-MM-JJ-nom/` et travaille dans ce dossier.
2. Modifie `story.py` (titre, narration, répliques, voix, noms HERO/FRIEND).
3. Modifie le dessin dans `anim_pixel.py` : remplace ou adapte `pico()` (héros), `flower()` (ami),
   le décor (`make_sky`, `make_hills`, `sun`, `rainbow`…), les déplacements et humeurs dans `scene()`.
   `scene()` doit toujours renvoyer `img, x, y, head` (position du héros, et point au-dessus de la tête
   de l'ami pour les bulles). La partie haute de l'écran vertical (titre, narration, « Fin ! ») est
   dans `anim_vert.py` (ciel `make_top_sky`, soleil). Adapte-la si le décor change (ex. nuit = lune).
4. Vérifie : `./stills.sh 3.5 10 16 22 28` puis **regarde** `vsheet.png`. Corrige tout ce qui déborde,
   se chevauche, est illisible ou moche. Recommence jusqu'à ce que ce soit propre.
5. Fabrique : `./build.sh ../../videos/AAAA-MM-JJ-nom.mp4` (≈15 s).
6. Ajoute une ligne dans `HISTOIRES.md`, puis `git add -A && git commit && git push`.
7. Lien public de la vidéo :
   `https://raw.githubusercontent.com/lebobonjames4-eng/shorts-enfants/main/videos/AAAA-MM-JJ-nom.mp4`
8. Programme dans Metricool (`createScheduledPost`, blogId 8158276, fuseau Europe/Paris) :
   - providers `[{"network":"youtube"}]`, media `[lien ci-dessus]`
   - youtubeData : `title` (« Titre ☁️ Histoire animée pour enfants », ≤ 100 caractères),
     `type: "short"`, `privacy: "public"`, `madeForKids: true`, `category: "FILM_ANIMATION"`,
     `isAiGeneratedContent: false`, quelques `tags` (histoire pour enfants, dessin animé, conte…)
   - `text` (OBLIGATOIRE, c'est la description YouTube) : 2-3 phrases qui racontent l'histoire
     et sa petite leçon (ex. « Pico aide une fleur qui a soif. Une histoire douce sur l'entraide
     pour les 3-6 ans ! »), puis une ligne vide, puis 15 à 20 hashtags :
     toujours `#shorts #histoirepourenfants #dessinanime #contepourenfants #enfants #maternelle
     #drole #rigolo #mignon #pixel #pixelart #jeu #jeuvideo #retro`
     + 3 à 6 hashtags liés à l'histoire du jour (ex. #nuage #fleur #arcenciel #entraide #amitie).
     Le but est d'attirer un maximum de spectateurs : ton fun et accrocheur dans la description.
     Hashtags en minuscules, sans accents ni espaces à l'intérieur d'un hashtag.
   - heure : **17:00** (heure de Paris) le jour même ; si 17:00 est passé, le lendemain 17:00.
9. En cas d'échec (rendu, push, Metricool), n'invente rien : décris l'erreur dans le résumé final.

## Fin de la tâche
Envoie un court résumé : titre, histoire en une phrase, heure de publication, lien Metricool.
