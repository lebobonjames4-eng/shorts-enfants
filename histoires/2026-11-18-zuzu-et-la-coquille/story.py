# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Zuzu and the Big Shell"
TITLE_LINES = [("Zuzu", 120), ("and the Big Shell", 58)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "zuzu", "pipa"                             # noms des personnages qui parlent
VOICES = {"zuzu": 260, "pipa": 440, "star": 340}          # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 32                                             # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                           # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Fa majeur, sautillant comme des bulles
MELODY = [65, 69, 72, 69, 70, 74, 72, None, 69, 72, 77, 76, 74, 72, 69, None,
          70, 69, 67, 69, 72, 70, 69, 67, 65, 67, 69, 72, 65, None, 65, None]
BASS = [41, 46, 48, 41, 38, 46, 48, 41]
BEAT = 0.36
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("boing", 1.9), ("sad", 7.5), ("boing", 15.6), ("oops", 16.1), ("shimmer", 19.0),
       ("noise", 21.5, 23.6), ("joy", 24.3), ("shimmer", 25.6), ("boing", 26.0), ("shimmer", 27.4)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Zuzu is a curious little fish.", 3.6, 7.0),
    ("Pipa the crab is sad. She needs a new shell!", 7.2, 12.7),
    ("Zuzu brings a shell... oops, too tiny!", 12.9, 18.6),
    ("Star sees a big shell. They push together!", 18.8, 24.1),
    ("Pipa has a new home! Bubble party!", 24.3, 29.1),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("zuzu", 0.2, "Hi! I'm Zuzu!", "right"),
    ("zuzu", 1.9, "Puff! Hee hee!", "right"),
    ("zuzu", 4.9, "Ooh! Who is that?", "right"),
    ("pipa", 7.7, "I need a new shell!", "right"),
    ("zuzu", 10.3, "I can help you!", "left"),
    ("zuzu", 13.9, "Try this one!", "left"),
    ("pipa", 16.3, "Oops! Too tiny!", "right"),
    ("star", 19.1, "Look! A big shell!", "right"),
    ("zuzu", 21.6, "Push, push, push!", "left"),
    ("pipa", 24.5, "My new home! Thank you!", "right"),
    ("zuzu", 26.9, "Bubble party!", "left"),
    ("zuzu", 29.6, "Bye-bye!", "left"),
    ("pipa", 29.6, "Bye-bye!", "right"),
]
