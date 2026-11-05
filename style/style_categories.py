# ---------------------------------------------------------------------
# Extrait à intégrer dans app.py : filtre catégorie stylisé
# (illustration + couleur de police + puce colorée + fond animé)
# Testé avec Streamlit 1.66
# ---------------------------------------------------------------------

# Une illustration, une couleur de police Streamlit et un code couleur précis par catégorie
STYLE_CATEGORIES = {
    "Toutes":  ("🍽️", "gray",   "#6b7280"),
    "Classic": ("🍕", "blue",   "#2a78d6"),
    "Supreme": ("🥓", "red",    "#d03b3b"),
    "Chicken": ("🍗", "orange", "#eb6834"),
    "Veggie":  ("🥦", "green",  "#1f9d55"),
}

choix_categorie = st.sidebar.radio(
    "Catégorie",
    list(STYLE_CATEGORIES),
    format_func=lambda c: f"{STYLE_CATEGORIES[c][0]} :{STYLE_CATEGORIES[c][1]}[{c}]",
)
categorie = None if choix_categorie == "Toutes" else choix_categorie

# Couleur de la catégorie choisie, réutilisée pour le style de la page
couleur = STYLE_CATEGORIES[choix_categorie][2]

# CSS injecté : fond teinté et animé, puce de sélection à la couleur de la catégorie.
# {couleur}14 = couleur à ~8 % d'opacité ; {couleur}22 = ~13 %.
# Les accolades sont doublées {{ }} car on est dans une f-string.
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{ background-color: {couleur}14; transition: background-color 0.6s ease; }}
[data-testid="stSidebar"]          {{ background-color: {couleur}22; transition: background-color 0.6s ease; }}
[data-testid="stHeader"]           {{ background: transparent; }}
[data-testid="stRadioOption"]:has(input:checked) > div > div:first-child {{
    background-color: {couleur} !important;
    border-color: {couleur} !important;
}}
</style>
""", unsafe_allow_html=True)
