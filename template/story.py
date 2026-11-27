# ---- Texte de l'histoire (modifié chaque jour) ----
SERIES = "Nuno & Friends"                                  # nom de la série (affiché au-dessus du titre)
TITLE = "Nuno and the Little Stream"
TITLE_LINES = [("Nuno", 130), ("and the Little Stream", 54)]  # (texte, taille) pour la version verticale
HERO, FRIEND = "nuno", "lulu"                               # noms des personnages qui parlent
VOICES = {"nuno": 280, "lulu": 430, "flutter": 560}         # hauteur de voix (Hz)
DURATION = 30                                               # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                             # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Fa majeur, petite chanson de montagne qui gambade
MELODY = [65, 69, 72, 77, 76, 72, 74, None, 70, 74, 77, 74, 72, 69, 67, None,
          65, 67, 69, 72, 74, 72, 69, None, 72, 70, 69, 67, 69, 65, 65, None]
BASS = [41, 46, 48, 41, 38, 46, 48, 41]
BEAT = 0.28
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("sad", 1.8), ("sad", 10.5), ("boing", 11.6), ("noise", 12.3, 13.3), ("oops", 12.4),
       ("shimmer", 14.8), ("boing", 18.9), ("joy", 19.1), ("shimmer", 19.4), ("boing", 23.3),
       ("shimmer", 24.0), ("joy", 25.2)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Nuno the little goat loves to jump high.", 3.4, 6.6),
    ("Oh no! Lulu's ball is across the stream.", 7.0, 10.4),
    ("Nuno jumps... splash! He lands in the water!", 11.3, 14.5),
    ("They push the old log together. One, two, three!", 15.9, 19.3),
    ("A bridge! Lulu crosses and gets her ball!", 21.0, 24.6),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("nuno", 0.2, "Hi! I'm Nuno!", "right"),
    ("lulu", 1.6, "My ball! Waaah!", "left"),
    ("nuno", 6.6, "What's wrong?", "right"),
    ("lulu", 10.5, "I can't swim!", "left"),
    ("nuno", 14.6, "So wet!", "right"),
    ("flutter", 15.2, "Push the log!", "left"),
    ("nuno", 19.4, "A bridge!", "right"),
    ("lulu", 20.1, "Hooray!", "left"),
    ("lulu", 24.8, "Catch!", "left"),
    ("nuno", 25.6, "Again! Again!", "right"),
    ("flutter", 26.6, "New friends!", "left"),
]
