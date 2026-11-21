# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Momo and the Leaf Boat"
TITLE_LINES = [("Momo", 120), ("and the Leaf Boat", 60)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "momo", "shelly"                          # noms des personnages qui parlent
VOICES = {"momo": 210, "shelly": 470}                    # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 30                                            # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                          # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Sol majeur, petite ritournelle sautillante de mare
MELODY = [67, 71, 74, 71, 72, 76, 74, None, 71, 74, 79, 78, 76, 74, 71, None,
          72, 71, 69, 71, 74, 72, 71, 69, 67, 69, 71, 74, 67, None, 67, None]
BASS = [43, 48, 50, 43, 40, 48, 50, 43]
BEAT = 0.32
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("boing", 0.3), ("boing", 1.1), ("boing", 1.9), ("sad", 7.5), ("boing", 9.2), ("boing", 9.9),
       ("boing", 12.6), ("boing", 14.0), ("oops", 14.9), ("noise", 14.9, 15.9), ("shimmer", 18.6),
       ("boing", 19.4), ("noise", 20.3, 23.3), ("boing", 23.3), ("joy", 24.0), ("shimmer", 24.4),
       ("boing", 24.6), ("shimmer", 26.0)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Momo is a little frog. He loves to jump!", 3.6, 7.0),
    ("Shelly the snail wants to cross the pond.", 7.2, 12.4),
    ("Momo jumps with Shelly... splash! Oops!", 12.6, 18.2),
    ("Shelly has an idea: a leaf boat!", 18.4, 23.5),
    ("Hooray! The big flower opens for them!", 23.7, 27.1),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("momo", 0.2, "Ribbit! I'm Momo!", "right"),
    ("momo", 2.2, "Boing, boing!", "right"),
    ("momo", 4.3, "Hi, dragonfly!", "right"),
    ("shelly", 7.3, "Oh no! I can't swim!", "right"),
    ("momo", 10.5, "I can help you!", "left"),
    ("momo", 12.9, "One, two... jump!", "left"),
    ("momo", 15.7, "Splash! Oopsie!", "left"),
    ("shelly", 18.5, "I have an idea!", "right"),
    ("momo", 20.5, "Kick, kick, kick!", "left"),
    ("shelly", 24.2, "Thank you, Momo!", "right"),
    ("momo", 25.9, "Ribbit-hooray!", "left"),
    ("momo", 27.5, "Bye-bye!", "left"),
    ("shelly", 28.1, "Bye!", "right"),
]
