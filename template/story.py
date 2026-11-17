# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Pico le petit nuage"
TITLE_LINES = [("Pico", 120), ("le petit nuage", 66)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "pico", "fleur"                          # noms des personnages qui parlent
VOICES = {"pico": 230, "fleur": 430}                    # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 30                                           # durée en secondes (« Fin ! » à DURATION - 2.7)
TITLE_OUT = 3.0                                         # le titre s'envole à ce moment (lettres affichées en < 1 s)

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
MELODY = [76, 79, 81, 79, 76, 74, 72, 74, 76, 79, 76, 74, 72, 74, 72, None]
BASS = [48, 45, 41, 43]
BEAT = 0.4
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("sad", 9.5), ("noise", 12.4, 19.2), ("joy", 18.9), ("shimmer", 20.6)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Pico voit une petite fleur toute triste...", 3.8, 12.1),
    ("Plic, ploc ! Pico lui donne de la pluie.", 12.4, 19.9),
    ("La fleur est toute contente : merci Pico !", 20.2, 27.1),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("pico", 0.2, "Coucou ! Je suis Pico !", "right"),
    ("pico", 9.6, "Oh non... elle a soif !", "left"),
    ("pico", 12.7, "Plic, ploc, plic, ploc !", "left"),
    ("fleur", 19.3, "Merci Pico !", "right"),
    ("pico", 21.2, "Youpi ! Un arc-en-ciel !", "left"),
    ("pico", 27.7, "Au revoir !", "left"),
    ("fleur", 27.7, "Au revoir !", "right"),
]
