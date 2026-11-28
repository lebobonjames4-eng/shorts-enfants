# ---- Texte de l'histoire (modifié chaque jour) ----
SERIES = "Nuno & Friends"                                  # nom de la série (affiché au-dessus du titre)
TITLE = "Pom and the Red Apple"
TITLE_LINES = [("Pom", 130), ("and the Red Apple", 60)]   # (texte, taille) pour la version verticale (inutilisé)
HERO, FRIEND = "nuno", "pom"                                # noms des personnages qui parlent
VOICES = {"nuno": 280, "lulu": 430, "flutter": 560, "pom": 360}   # hauteur de voix (Hz)
DURATION = 150                                              # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 4.0                                             # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Sol majeur, petite valse d'automne qui se balance
MELODY = [67, 71, 74, 71, 72, 76, 74, None, 71, 74, 79, 78, 76, 74, 72, None,
          69, 72, 76, 74, 72, 71, 69, None, 67, 71, 74, 72, 71, 69, 67, None,
          74, 76, 78, 79, 78, 76, 74, None, 72, 71, 72, 74, 71, 69, 67, None]
BASS = [43, 48, 50, 43, 40, 48, 50, 43, 47, 48, 50, 43]
BEAT = 0.3
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("boing", 3.6), ("boing", 5.6), ("boing", 15.6), ("oops", 16.0), ("noise", 22.0, 23.6),
       ("sad", 27.4), ("sad", 29.6), ("shimmer", 36.0), ("sad", 44.2),
       ("boing", 53.4), ("noise", 54.3, 55.4), ("oops", 54.5), ("joy", 60.8),
       ("shimmer", 67.8), ("noise", 74.4, 76.6), ("oops", 75.0), ("boing", 80.4),
       ("boing", 88.0), ("boing", 88.8), ("oops", 90.0), ("sad", 95.0),
       ("shimmer", 100.8), ("joy", 102.6), ("boing", 115.5), ("boing", 115.9), ("shimmer", 116.3),
       ("joy", 117.0), ("joy", 123.0), ("shimmer", 129.0), ("joy", 136.2), ("noise", 138.6, 140.8),
       ("joy", 141.0), ("shimmer", 143.0)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("It is a windy autumn day in Sunny Meadow.", 4.4, 8.6),
    ("Nuno and Lulu play ball under the apple tree.", 9.4, 13.8),
    ("Here comes Flutter, the little butterfly.", 20.4, 24.0),
    ("Then they hear a little sniff, sniff.", 26.4, 30.4),
    ("It is a little hedgehog. His name is Pom.", 32.2, 36.4),
    ("Pom looks up at the big red apple.", 39.6, 43.4),
    ("Nuno runs and jumps as high as he can.", 49.2, 53.0),
    ("Oh no! He lands in the pile of leaves!", 55.2, 59.2),
    ("Now Flutter flies up to the apple.", 64.6, 68.2),
    ("She pushes and pushes, but it is too heavy.", 70.0, 74.2),
    ("Whoosh! The wind blows Flutter away!", 76.4, 80.0),
    ("Lulu throws her red ball up high.", 83.2, 87.0),
    ("The apple wiggles, but it does not fall.", 89.6, 93.4),
    ("Pom is sad. The apple is still up high.", 96.2, 100.4),
    ("Lulu will throw, and Nuno will bounce the ball.", 104.0, 108.4),
    ("One, two, three! Throw, jump, and bounce!", 111.2, 114.8),
    ("The apple falls, right onto Pom's back!", 117.6, 121.4),
    ("Pom says thank you. He wants to share.", 125.2, 129.2),
    ("Four friends and four sweet apple slices.", 132.0, 135.8),
    ("Then the wind makes the leaves dance.", 138.6, 142.4),
]

# (qui, début, texte, côté de la bulle : "up" = au-dessus de la tête, "left", "right")
LINES = [
    ("nuno", 0.2, "Good afternoon, Lulu!", "up"),
    ("lulu", 1.6, "Hi, Nuno! Catch!", "up"),
    ("nuno", 8.8, "Bonk! Got it!", "up"),
    ("lulu", 14.0, "Your turn!", "up"),
    ("nuno", 16.2, "Where did it go?", "up"),
    ("lulu", 18.2, "On your head!", "up"),
    ("flutter", 24.2, "Whee! The wind!", "right"),
    ("nuno", 25.2, "Hi, Flutter!", "up"),
    ("lulu", 30.6, "Who is there?", "up"),
    ("pom", 36.6, "Hello. I'm Pom.", "up"),
    ("flutter", 37.9, "Why are you sad?", "right"),
    ("pom", 43.8, "I want that apple.", "up"),
    ("pom", 45.4, "But it's too high!", "up"),
    ("nuno", 47.0, "I can help!", "up"),
    ("nuno", 48.2, "Let's go!", "up"),
    ("nuno", 53.2, "Boing boing!", "up"),
    ("nuno", 59.4, "Too short!", "up"),
    ("pom", 60.6, "Hee hee! Leaves!", "up"),
    ("lulu", 61.8, "Are you okay?", "up"),
    ("nuno", 63.0, "I'm fine!", "up"),
    ("flutter", 68.4, "I will push it!", "left"),
    ("flutter", 74.6, "Whoa! Whoa!", "right"),
    ("flutter", 80.4, "So dizzy...", "right"),
    ("lulu", 81.7, "My turn!", "up"),
    ("lulu", 87.2, "Up you go!", "up"),
    ("nuno", 93.6, "Bonk! Hee hee!", "up"),
    ("pom", 94.8, "Oh no...", "up"),
    ("lulu", 100.6, "Wait! I have an idea!", "up"),
    ("lulu", 102.4, "We can do it together!", "up"),
    ("flutter", 108.6, "I see it from up here!", "left"),
    ("flutter", 110.0, "Ready? Now!", "left"),
    ("pom", 121.6, "I got it!", "up"),
    ("nuno", 122.8, "Hooray!", "up"),
    ("lulu", 123.8, "We did it!", "up"),
    ("pom", 129.4, "Let's share!", "up"),
    ("flutter", 130.6, "Yummy!", "right"),
    ("nuno", 136.0, "Crunch, crunch!", "up"),
    ("lulu", 137.2, "So good!", "up"),
    ("pom", 142.6, "Dance with me!", "up"),
    ("nuno", 144.0, "Best day ever!", "up"),
    ("flutter", 145.4, "Bye bye!", "right"),
]
