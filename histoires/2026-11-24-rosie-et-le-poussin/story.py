# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Rosie and the Lost Chick"
TITLE_LINES = [("Rosie", 130), ("and the Lost Chick", 62)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "rosie", "pip"                               # noms des personnages qui parlent
VOICES = {"rosie": 300, "pip": 520, "cow": 140, "mama": 380}  # hauteur de voix (Hz)
DURATION = 30                                               # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                             # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Sol majeur, petite chanson de la ferme qui sautille
MELODY = [67, 71, 74, 71, 72, 76, 74, None, 71, 74, 79, 76, 74, 72, 71, None,
          69, 72, 76, 74, 72, 71, 69, None, 67, 71, 74, 72, 71, 69, 67, None]
BASS = [43, 48, 50, 43, 40, 48, 50, 43]
BEAT = 0.3
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("sad", 1.9), ("sad", 9.9), ("boing", 14.2), ("oops", 15.3), ("shimmer", 17.2),
       ("joy", 19.0), ("shimmer", 20.6), ("joy", 22.2), ("shimmer", 24.0)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Rosie the piglet loves to sing.", 3.4, 6.6),
    ("Little Pip is lost. He wants his mama!", 6.8, 11.0),
    ("Rosie calls very loud... oops, a cow!", 11.2, 15.8),
    ("Let's sing together, very loud!", 16.0, 20.4),
    ("Mama Hen is here! Time for a happy dance!", 20.6, 25.4),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("rosie", 0.2, "La-la-la! I'm Rosie!", "right"),
    ("pip", 1.9, "Peep... sniff!", "left"),
    ("rosie", 5.8, "Who's crying?", "right"),
    ("pip", 9.9, "Where's my mama?", "left"),
    ("rosie", 13.2, "MAMA HEN!", "right"),
    ("cow", 14.4, "Moo?", "left"),
    ("rosie", 15.0, "Oops! Not you!", "right"),
    ("pip", 18.2, "Peep! Peep!", "left"),
    ("rosie", 18.3, "La-la-la!", "right"),
    ("pip", 19.9, "Mama!", "left"),
    ("mama", 23.0, "Thank you, Rosie!", "left"),
    ("rosie", 25.6, "Bye-bye!", "right"),
]
