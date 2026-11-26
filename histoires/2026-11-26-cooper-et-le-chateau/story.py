# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Cooper and the Sandcastle"
TITLE_LINES = [("Cooper", 125), ("and the Sandcastle", 58)]  # (texte, taille) pour la version verticale
HERO, FRIEND = "cooper", "pebble"                           # noms des personnages qui parlent
VOICES = {"cooper": 300, "pebble": 420, "gus": 230}         # hauteur de voix (Hz)
DURATION = 30                                               # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                             # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Sol majeur, petite chanson de plage qui sautille
MELODY = [67, 71, 74, 71, 72, 76, 74, None, 71, 74, 79, 78, 76, 74, 72, None,
          69, 72, 76, 74, 72, 71, 69, None, 67, 71, 74, 72, 71, 69, 67, None]
BASS = [43, 48, 50, 43, 40, 48, 50, 43]
BEAT = 0.3
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("sad", 1.9), ("sad", 10.4), ("boing", 12.3), ("oops", 12.8), ("shimmer", 15.0),
       ("boing", 15.9), ("boing", 18.8), ("joy", 19.3), ("shimmer", 19.7), ("shimmer", 24.3),
       ("joy", 25.3)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Cooper the crab loves to dance sideways.", 3.4, 6.6),
    ("Oh no! A big wave broke Pebble's sandcastle.", 6.8, 10.4),
    ("Cooper builds a tower... oops! It falls!", 11.2, 14.4),
    ("Gus has a bucket. Fill it and flip!", 15.8, 19.2),
    ("A big new castle! Gus puts a flag on top!", 21.0, 25.0),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("cooper", 0.2, "Hi! I'm Cooper!", "right"),
    ("pebble", 1.8, "My castle! Waaah!", "left"),
    ("cooper", 6.0, "Why so sad?", "right"),
    ("pebble", 10.5, "It fell down!", "left"),
    ("cooper", 14.5, "Sandy head!", "right"),
    ("gus", 15.0, "Try my bucket!", "left"),
    ("cooper", 19.4, "Hooray!", "right"),
    ("pebble", 20.0, "Thank you!", "left"),
    ("gus", 25.0, "Ta-da!", "left"),
    ("cooper", 25.6, "Dance party!", "right"),
    ("pebble", 26.6, "Yay!", "left"),
]
