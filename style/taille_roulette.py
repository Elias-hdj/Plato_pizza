# ---------------------------------------------------------------------
# Extrait à intégrer dans app.py : filtre TAILLE avec couteau à pizza
# - seule la poignée du curseur des tailles devient un couteau 🔪 qui "coupe" quand on le fait glisser
# - à CHAQUE changement de taille : animation d'une pizza coupée + son de découpe (désactivable)
# Testé avec Streamlit 1.66.  Imports nécessaires en haut de app.py :
#   import io, wave
#   from pathlib import Path
#   import numpy as np
# ---------------------------------------------------------------------

# 1. Le son de découpe.
#    Si tu ajoutes un vrai enregistrement dans assets/coupe_pizza.mp3, il est utilisé en priorité.
#    Sinon, un son de croûte qui craque est fabriqué en Python.
FICHIER_SON = Path(__file__).parent / "assets" / "coupe_pizza.mp3"

@st.cache_data
def son_decoupe(variante=0):
    # variante : ajoute quelques millisecondes de silence pour que chaque son soit un
    # "nouveau fichier" aux yeux du navigateur (sinon il ne rejoue pas le même son)
    frequence = 22050
    duree = 0.55
    n = int(frequence * duree)
    rng = np.random.default_rng(3)
    signal = np.zeros(n)
    # La croûte qui craque : une série de petits craquements rapprochés
    for debut in np.sort(rng.uniform(0, duree - 0.05, 70)):
        i = int(debut * frequence)
        longueur = int(rng.uniform(0.002, 0.008) * frequence)
        craquement = rng.uniform(-1, 1, longueur) * np.exp(-np.linspace(0, 6, longueur))
        signal[i:i + longueur] += craquement * rng.uniform(0.3, 1.0)
    # Adoucir les aigus pour un son plus "croustillant" que "grésillant"
    signal = np.convolve(signal, np.ones(6) / 6, mode="same")
    # Volume : montée rapide, tenue pendant la coupe, puis fin nette
    t = np.linspace(0, duree, n)
    enveloppe = np.clip(t / 0.03, 0, 1) * np.clip((duree - t) / 0.08, 0, 1)
    signal = signal * enveloppe
    signal = np.concatenate([signal / np.abs(signal).max(), np.zeros(variante + 1)])
    signal = (signal * 0.6 * 32767).astype(np.int16)
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(frequence)
        f.writeframes(signal.tobytes())
    return tampon.getvalue()

# 2. Le curseur des tailles.
#    key="filtre_taille" donne à ce widget une classe CSS à lui (.st-key-filtre_taille) :
#    le style ne touchera QUE ce curseur, pas celui de la période.
choix_taille = st.sidebar.select_slider(
    "🔪 Taille",
    options=["Toutes", "S", "M", "L", "XL", "XXL"],
    key="filtre_taille",
)
taille = None if choix_taille == "Toutes" else choix_taille

# 3. Détecter un changement de taille.
#    session_state garde la taille précédente et compte les coupes d'une exécution à l'autre.
a_change = st.session_state.get("taille_precedente", choix_taille) != choix_taille
if a_change:
    st.session_state["nb_coupes"] = st.session_state.get("nb_coupes", 0) + 1
st.session_state["taille_precedente"] = choix_taille
nb_coupes = st.session_state.get("nb_coupes", 0)

# Astuce : le navigateur ne rejoue pas un élément identique à celui déjà affiché.
# On rend donc chaque animation et chaque son légèrement différents grâce au compteur nb_coupes.
zone_animation = st.sidebar.empty()
son_actif = st.sidebar.toggle("🔊 Effets sonores", value=True)

if a_change:
    # 3a. L'animation : un couteau tranche la pizza, puis les deux moitiés s'écartent.
    #     La classe alterne entre v0 et v1 : le nom de l'animation CSS change, ce qui la relance.
    zone_animation.markdown(f"""
<div class="coupe-pizza v{nb_coupes % 2}">
  <div class="moitie gauche"></div>
  <div class="moitie droite"></div>
  <div class="couteau">🔪</div>
</div>
<p class="coupe-texte v{nb_coupes % 2}">Taille {choix_taille}, à la coupe !</p>
""", unsafe_allow_html=True)

    # 3b. Le son : un contenu différent à chaque coupe, donc rejoué à chaque fois
    if son_actif:
        if FICHIER_SON.exists():
            # Les octets nuls ajoutés à la fin sont ignorés à la lecture mais rendent le fichier unique
            son = FICHIER_SON.read_bytes() + bytes(nb_coupes % 50 + 1)
            st.sidebar.audio(son, format="audio/mpeg", autoplay=True)
        else:
            st.sidebar.audio(son_decoupe(nb_coupes % 50), format="audio/wav", autoplay=True)

# 4. Le style : la poignée du curseur des tailles devient un couteau 🔪 qui fait un mouvement
#    de coupe pendant le glissement. Le lecteur audio est masqué.
st.markdown("""
<style>
.st-key-filtre_taille div:has(> div > input[type="range"]) {
    width: 30px !important; height: 30px !important;
    background: transparent !important; border: none !important; box-shadow: none !important;
}
.st-key-filtre_taille div:has(> div > input[type="range"])::before {
    content: "🔪";
    font-size: 24px; line-height: 30px;
    display: block; text-align: center;
    transform: rotate(-45deg);
}
.st-key-filtre_taille div:has(> div > input[type="range"]):active::before {
    animation: coupe 0.25s ease-in-out infinite alternate;
}
@keyframes coupe {
    from { transform: rotate(-60deg) translateY(-2px); }
    to   { transform: rotate(-25deg) translateY(3px); }
}
[data-testid="stAudio"] { display: none; }

/* Animation de la pizza coupée */
.coupe-pizza { position: relative; width: 96px; height: 96px; margin: 14px auto 4px; }
.coupe-pizza .moitie {
    position: absolute; inset: 0; border-radius: 50%;
    background:
        radial-gradient(circle at 34% 38%, #9e2a1e 0 7%, transparent 8%),
        radial-gradient(circle at 66% 64%, #9e2a1e 0 7%, transparent 8%),
        radial-gradient(circle at 70% 30%, #9e2a1e 0 6%, transparent 7%),
        radial-gradient(circle at 30% 70%, #2f7d32 0 4%, transparent 5%),
        radial-gradient(circle at 58% 45%, #2f7d32 0 4%, transparent 5%),
        radial-gradient(circle, #f3c969 0 56%, #c8402c 57% 64%, #d9a05b 65% 100%);
}
.coupe-pizza .gauche { clip-path: inset(0 50% 0 0); }
.coupe-pizza .droite { clip-path: inset(0 0 0 50%); }
.coupe-pizza .couteau {
    position: absolute; left: 50%; top: -34px; font-size: 30px;
    transform: translateX(-50%) rotate(45deg);
}
.coupe-texte { text-align: center; font-size: 0.85rem; opacity: 0; }

/* Deux jeux d'animations identiques (v0 / v1) : changer de nom relance l'animation */
.v0 .couteau { animation: tranche-0 0.9s ease-in forwards; }
.v1 .couteau { animation: tranche-1 0.9s ease-in forwards; }
.v0 .gauche  { animation: ecarte-gauche-0 1.6s ease forwards; }
.v1 .gauche  { animation: ecarte-gauche-1 1.6s ease forwards; }
.v0 .droite  { animation: ecarte-droite-0 1.6s ease forwards; }
.v1 .droite  { animation: ecarte-droite-1 1.6s ease forwards; }
.coupe-texte.v0 { animation: apparait-0 0.4s 1.1s forwards; }
.coupe-texte.v1 { animation: apparait-1 0.4s 1.1s forwards; }

@keyframes tranche-0 { 0% { top: -34px; opacity: 0; } 15% { opacity: 1; } 80% { top: 72px; opacity: 1; } 100% { top: 90px; opacity: 0; } }
@keyframes tranche-1 { 0% { top: -34px; opacity: 0; } 15% { opacity: 1; } 80% { top: 72px; opacity: 1; } 100% { top: 90px; opacity: 0; } }
@keyframes ecarte-gauche-0 { 0%, 55% { transform: none; } 100% { transform: translateX(-9px) rotate(-8deg); } }
@keyframes ecarte-gauche-1 { 0%, 55% { transform: none; } 100% { transform: translateX(-9px) rotate(-8deg); } }
@keyframes ecarte-droite-0 { 0%, 55% { transform: none; } 100% { transform: translateX(9px) rotate(8deg); } }
@keyframes ecarte-droite-1 { 0%, 55% { transform: none; } 100% { transform: translateX(9px) rotate(8deg); } }
@keyframes apparait-0 { to { opacity: 1; } }
@keyframes apparait-1 { to { opacity: 1; } }
</style>
""", unsafe_allow_html=True)
