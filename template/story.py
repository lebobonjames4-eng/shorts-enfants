# ---- Texte de l'histoire (modifié chaque jour) ----
TITLE = "Pico le petit nuage"
TITLE_LINES = [("Pico", 120), ("le petit nuage", 66)]   # (texte, taille) pour la version verticale
HERO, FRIEND = "pico", "fleur"                          # noms des personnages qui parlent
VOICES = {"pico": 230, "fleur": 430}                    # hauteur de voix (Hz) : grave ~200, aigu ~450

# (texte, début, fin) en secondes — bandeau de narration
CAPTIONS = [
    ("Pico voit une petite fleur toute triste...", 5.8, 12.1),
    ("Plic, ploc ! Pico lui donne de la pluie.", 12.4, 19.9),
    ("La fleur est toute contente : merci Pico !", 20.2, 27.1),
]

# (qui, début, texte, côté de la bulle en 16:9)
LINES = [
    ("pico", 2.9, "Coucou ! Je suis Pico !", "right"),
    ("pico", 9.6, "Oh non... elle a soif !", "left"),
    ("pico", 12.7, "Plic, ploc, plic, ploc !", "left"),
    ("fleur", 19.3, "Merci Pico !", "right"),
    ("pico", 21.2, "Youpi ! Un arc-en-ciel !", "left"),
    ("pico", 27.7, "Au revoir !", "left"),
    ("fleur", 27.7, "Au revoir !", "right"),
]
