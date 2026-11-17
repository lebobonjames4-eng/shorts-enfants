# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Tobi et le nez perdu"
TITLE_LINES = [("Tobi", 120), ("et le nez perdu", 64)]  # (texte, taille) pour la version verticale
HERO, FRIEND = "tobi", "flocon"                         # noms des personnages qui parlent
VOICES = {"tobi": 300, "flocon": 210}                   # hauteur de voix (Hz) : grave ~200, aigu ~450
DURATION = 48                                           # durée en secondes (« Fin ! » à DURATION - 2.7)

# Musique 8-bit : notes MIDI (60 = do), None = silence. BEAT = durée d'une note (s).
MELODY = [67, 71, 74, 71, 72, 76, 74, 71, 67, 69, 71, 74, 72, 71, 69, None,
          71, 74, 79, 76, 74, 72, 71, 69, 67, 71, 69, 66, 67, None, 67, None]
BASS = [43, 48, 50, 43, 40, 48, 50, 43]
BEAT = 0.38
# Bruitages : ("sad", t) ("noise", t0, t1) ("joy", t) ("shimmer", t) ("boing", t) ("oops", t)
SFX = [("boing", 6.7), ("sad", 12.6), ("boing", 21.5), ("boing", 24.3), ("oops", 24.9),
       ("shimmer", 28.6), ("boing", 33.5), ("joy", 34.6), ("shimmer", 36.8), ("shimmer", 39.5)]

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Voici Tobi, un petit pingouin un peu maladroit.", 6.0, 11.5),
    ("Il rencontre Flocon, un bonhomme de neige tout triste.", 11.8, 19.5),
    ("Tobi essaie avec un poisson... mais ça glisse !", 19.8, 28.4),
    ("Un oiseau apporte une carotte. Ensemble, c'est mieux !", 28.7, 36.6),
    ("Surprise ! Des lumières magiques dansent dans le ciel !", 36.9, 44.9),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("tobi", 3.0, "Coucou ! Moi, c'est Tobi !", "right"),
    ("tobi", 7.4, "Oups ! Hi hi !", "right"),
    ("flocon", 13.0, "Snif... J'ai perdu mon nez !", "right"),
    ("tobi", 16.0, "Je vais t'aider !", "left"),
    ("flocon", 23.0, "Hi hi, ça chatouille !", "right"),
    ("tobi", 25.6, "Oups ! Raté !", "left"),
    ("tobi", 31.3, "Une carotte ! Merci !", "left"),
    ("flocon", 35.2, "Mon nez ! Merci Tobi !", "right"),
    ("tobi", 38.4, "Youpi ! On danse !", "left"),
    ("flocon", 41.2, "C'est magique !", "right"),
    ("tobi", 45.4, "Au revoir !", "left"),
    ("flocon", 45.4, "Au revoir !", "right"),
]
