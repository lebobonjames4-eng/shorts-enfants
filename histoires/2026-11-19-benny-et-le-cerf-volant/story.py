# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Benny and the Stuck Kite"
TITLE_LINES = [("Benny", 120), ("and the Stuck Kite", 56)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "benny", "lila"                            # noms des personnages qui parlent
VOICES = {"benny": 205, "lila": 455}                      # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 32                                             # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                           # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Sol majeur, balancé comme des feuilles qui dansent
MELODY = [67, 71, 74, 71, 72, 76, 74, None, 71, 74, 79, 78, 76, 74, 71, None,
          72, 71, 69, 71, 74, 72, 71, 69, 67, 69, 71, 74, 67, None, 67, None]
BASS = [43, 48, 50, 43, 40, 48, 50, 43]
BEAT = 0.34
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("boing", 1.8), ("boing", 4.7), ("sad", 7.6), ("boing", 14.2), ("oops", 15.0),
       ("shimmer", 18.8), ("boing", 21.4), ("shimmer", 22.9), ("noise", 23.6, 25.8),
       ("joy", 24.3), ("boing", 26.6), ("shimmer", 27.4)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Benny is a big, clumsy bear cub.", 3.6, 7.0),
    ("Lila the squirrel is sad. Her kite is stuck!", 7.2, 12.6),
    ("Benny jumps... oops! Too high!", 12.8, 18.4),
    ("Lila has an idea. They help each other!", 18.6, 23.6),
    ("Whoosh! The kite flies high! Hooray!", 23.8, 29.1),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("benny", 0.2, "Hi! I'm Benny!", "right"),
    ("benny", 1.8, "Big bear hug!", "right"),
    ("benny", 4.6, "Crunch, crunch!", "right"),
    ("lila", 7.6, "My kite is stuck!", "right"),
    ("benny", 10.2, "I can help you!", "left"),
    ("benny", 13.0, "Jump! Hup!", "left"),
    ("benny", 15.6, "Oopsie! Leaves on my nose!", "left"),
    ("lila", 18.7, "I have an idea!", "right"),
    ("benny", 20.7, "Hop on my head!", "left"),
    ("lila", 24.2, "My kite! Thank you!", "right"),
    ("benny", 26.6, "Wheee!", "left"),
    ("benny", 29.6, "Bye-bye!", "left"),
    ("lila", 29.6, "Bye-bye!", "right"),
]
