# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Zip and the Rocket"
TITLE_LINES = [("Zip", 130), ("and the Rocket", 72)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "zip", "blip"                            # noms des personnages qui parlent
VOICES = {"zip": 250, "blip": 470}                      # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 28                                           # durée en secondes (« The End! » à DURATION - 2.7)
TITLE_OUT = 3.0                                         # le titre s'envole à ce moment

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
# Ré majeur, petite chanson spatiale qui sautille
MELODY = [62, 66, 69, 74, 73, 71, 69, None, 66, 69, 71, 74, 76, 74, 73, None,
          71, 69, 66, 64, 66, 69, 71, None, 74, 73, 71, 69, 66, 64, 62, None]
BASS = [38, 43, 45, 38, 35, 43, 45, 38]
BEAT = 0.28
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t) ("click", t)
SFX = ([("boing", 0.7 + i) for i in range(7)] +
       [("sad", 8.4), ("boing", 9.6), ("boing", 14.1), ("oops", 15.0), ("shimmer", 16.2)] +
       [("click", 18.0 + 0.36 * i) for i in range(7)] +
       [("joy", 20.2), ("boing", 20.6), ("noise", 21.2, 23.6), ("shimmer", 23.5), ("joy", 24.2),
        ("shimmer", 25.4)])

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Zip is a little robot. He loves to bounce!", 3.5, 7.0),
    ("Blip's rocket won't start. He can't fly home!", 7.2, 11.4),
    ("Zip pushes and pushes... boing! Oops!", 11.6, 16.0),
    ("A big key! Let's wind it up together!", 16.2, 21.0),
    ("Whoosh! Up they go! Look, fireworks!", 21.2, 25.2),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("zip", 0.2, "Beep-boop! I'm Zip!", "right"),
    ("blip", 1.9, "Oh no...", "left"),
    ("blip", 7.3, "My rocket won't go!", "left"),
    ("zip", 9.4, "I can help, Blip!", "right"),
    ("zip", 11.9, "Push! Push!", "right"),
    ("zip", 15.2, "Oopsie!", "right"),
    ("blip", 16.4, "Look! A big key!", "left"),
    ("zip", 18.3, "Wind, wind, wind!", "right"),
    ("blip", 20.3, "It works! Hop in!", "left"),
    ("zip", 22.6, "Hooray!", "right"),
    ("blip", 23.9, "Thank you, Zip!", "left"),
    ("zip", 25.7, "Bye-bye!", "right"),
]
