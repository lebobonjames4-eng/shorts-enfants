# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Ollie and the Fallen Star"
TITLE_LINES = [("Ollie", 120), ("and the Fallen Star", 56)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "ollie", "twinkle"                             # noms des personnages qui parlent
VOICES = {"ollie": 230, "twinkle": 520}                       # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 32                                                 # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                               # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Fa majeur, petite berceuse joyeuse sous les étoiles
MELODY = [72, 69, 65, 69, 72, 77, 76, None, 74, 72, 70, 69, 67, 69, 72, None,
          72, 74, 76, 77, 76, 74, 72, 69, 70, 72, 69, 67, 65, None, 65, None]
BASS = [41, 46, 48, 41, 38, 46, 48, 41]
BEAT = 0.35
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("boing", 0.9), ("shimmer", 4.7), ("boing", 6.3), ("sad", 7.6), ("boing", 14.0),
       ("oops", 15.0), ("shimmer", 18.8), ("boing", 19.7), ("boing", 21.4), ("boing", 22.2),
       ("noise", 22.3, 24.0), ("shimmer", 22.6), ("joy", 24.3), ("shimmer", 25.2), ("shimmer", 27.2)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Ollie is a little owl. He loves the night!", 3.6, 7.0),
    ("Oh! A little star fell down. She is sad.", 7.2, 12.6),
    ("Ollie throws her up... oops! Too low!", 12.8, 18.4),
    ("Twinkle has an idea: the seesaw!", 18.6, 23.6),
    ("Boing! Twinkle is home! Look at the sky!", 23.8, 29.1),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("ollie", 0.2, "Hoo-hoo! I'm Ollie!", "right"),
    ("ollie", 1.8, "I love the night!", "right"),
    ("ollie", 4.6, "Wow! A falling star!", "right"),
    ("twinkle", 7.6, "Oh no! I fell!", "right"),
    ("ollie", 10.2, "I can help you!", "left"),
    ("ollie", 13.0, "One, two, three... up!", "left"),
    ("ollie", 15.6, "Oopsie! A star hat!", "left"),
    ("twinkle", 18.7, "I have an idea!", "right"),
    ("ollie", 20.7, "Hold on tight!", "left"),
    ("twinkle", 24.2, "I'm home! Thank you!", "right"),
    ("ollie", 26.6, "Hoo-hooray!", "left"),
    ("ollie", 29.4, "Good night!", "left"),
    ("twinkle", 29.4, "Good night!", "right"),
]
