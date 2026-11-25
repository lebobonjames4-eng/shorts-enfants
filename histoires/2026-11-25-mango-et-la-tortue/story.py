# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Mango and the Turtle"
TITLE_LINES = [("Mango", 130), ("and the Turtle", 70)]      # (texte, taille) pour la version verticale
HERO, FRIEND = "mango", "tiki"                              # noms des personnages qui parlent
VOICES = {"mango": 330, "tiki": 210, "kiwi": 560}           # hauteur de voix (Hz)
DURATION = 30                                               # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                             # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Fa majeur, petite danse de la jungle qui chaloupe
MELODY = [65, 69, 72, 69, 70, 74, 72, None, 69, 72, 77, 76, 74, 72, 70, None,
          67, 70, 74, 72, 70, 69, 67, None, 65, 69, 72, 70, 69, 67, 65, None]
BASS = [41, 46, 48, 41, 38, 46, 48, 41]
BEAT = 0.28
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("sad", 1.9), ("sad", 10.4), ("boing", 12.3), ("oops", 13.0), ("shimmer", 15.0),
       ("boing", 18.8), ("joy", 19.3), ("shimmer", 21.6), ("joy", 23.2), ("shimmer", 25.6)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Mango the monkey loves bananas.", 3.4, 6.6),
    ("Oh no! Tiki the turtle is upside down.", 6.8, 10.3),
    ("Mango pushes... oops! Tiki just spins!", 11.3, 14.4),
    ("Kiwi helps too. One, two, three!", 16.0, 19.2),
    ("Tiki is up! Time for a jungle dance!", 21.2, 25.0),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("mango", 0.2, "Hi! I'm Mango! Yum!", "right"),
    ("tiki", 1.9, "Help! Help!", "left"),
    ("mango", 5.9, "Are you okay?", "right"),
    ("tiki", 10.4, "I can't get up!", "left"),
    ("mango", 14.6, "So dizzy!", "right"),
    ("kiwi", 15.3, "I can help!", "left"),
    ("mango", 19.4, "Hooray!", "right"),
    ("tiki", 20.0, "Thank you!", "left"),
    ("kiwi", 25.0, "Party!", "left"),
    ("mango", 25.6, "Banana for you!", "right"),
    ("tiki", 26.8, "Yum!", "left"),
]
