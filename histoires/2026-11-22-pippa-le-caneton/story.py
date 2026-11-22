# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Pippa and the Rainy Day"
TITLE_LINES = [("Pippa", 120), ("and the Rainy Day", 60)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "pippa", "dot"                            # noms des personnages qui parlent
VOICES = {"pippa": 300, "dot": 520}                      # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 30                                            # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                          # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Fa majeur, petite chanson de pluie qui sautille (plic, ploc)
MELODY = [65, 69, 72, 69, 70, 74, 72, None, 69, 72, 77, 76, 74, 72, 69, None,
          70, 69, 67, 69, 72, 70, 69, 67, 65, 67, 69, 72, 65, None, 77, None]
BASS = [41, 46, 48, 41, 38, 46, 48, 41]
BEAT = 0.30
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("boing", 0.4), ("boing", 1.15), ("boing", 1.9), ("boing", 2.65), ("boing", 4.6), ("boing", 5.5),
       ("sad", 7.6), ("boing", 12.5), ("noise", 14.3, 15.1), ("oops", 14.9), ("boing", 15.2),
       ("shimmer", 18.1), ("boing", 19.2), ("noise", 20.4, 22.4), ("shimmer", 22.4), ("joy", 23.6),
       ("boing", 25.0), ("shimmer", 24.6), ("boing", 25.85), ("boing", 26.55), ("boing", 27.25)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Pippa is a little duck. She loves puddles!", 3.6, 7.0),
    ("Dot the ladybug is all wet. She can't fly!", 7.2, 12.2),
    ("Pippa holds up a big leaf... whoosh! Oops!", 12.4, 17.8),
    ("Dot has an idea: the big mushroom!", 18.0, 23.4),
    ("Hooray! The sun is back, and so are Dot's friends!", 23.6, 27.2),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("pippa", 0.2, "Quack! I'm Pippa!", "right"),
    ("pippa", 2.0, "Splish, splash!", "right"),
    ("pippa", 4.3, "I love rain!", "right"),
    ("dot", 7.3, "Oh no! My wings are wet!", "left"),
    ("pippa", 10.0, "Don't worry, Dot!", "right"),
    ("pippa", 12.9, "Here, an umbrella!", "right"),
    ("pippa", 15.6, "Oopsie! All wet!", "right"),
    ("dot", 18.1, "Look! A big mushroom!", "left"),
    ("pippa", 20.4, "Flap, flap, flap!", "right"),
    ("dot", 22.5, "Dry! I can fly!", "left"),
    ("dot", 24.2, "Thank you, Pippa!", "left"),
    ("pippa", 25.8, "Quack-hooray!", "right"),
    ("pippa", 27.5, "Bye-bye!", "right"),
    ("dot", 28.1, "Bye!", "left"),
]
