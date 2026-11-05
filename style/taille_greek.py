# ---------------------------------------------------------------------
# Extrait à intégrer dans app.py : tailles S/M/L + édition spéciale Greek (XL / XXL)
# Testé avec Streamlit 1.66.
#
# Pourquoi : XL et XXL n'existent que pour une seule recette, la Greek (une Classic).
# Dans le curseur, ces deux crans donnaient des résultats vides avec la plupart des catégories.
# On les sort donc du curseur et on les présente comme une "édition spéciale".
#
# Où le placer : il REMPLACE la partie "2. Le curseur des tailles" de l'extrait couteau
# (taille_roulette.py). Il doit venir APRÈS le filtre catégorie, car il utilise
# les variables categorie et couleur. Le reste de l'extrait couteau (son, animation, CSS) ne change pas.
# ---------------------------------------------------------------------

TURQUOISE = "#0f97a6"

# On lit d'abord le choix Greek mémorisé par Streamlit (None si aucun bouton n'est actif).
# On en a besoin AVANT de créer le curseur, pour pouvoir le griser.
format_greek = st.session_state.get("filtre_greek")

# Le curseur couteau, sans XL ni XXL. Il est grisé quand une Greek est sélectionnée.
choix_taille = st.sidebar.select_slider(
    "🔪 Taille",
    options=["Toutes", "S", "M", "L"],
    key="filtre_taille",
    disabled=format_greek is not None,
)

# L'édition spéciale : deux boutons. Un second clic sur le bouton actif le désélectionne.
format_greek = st.sidebar.segmented_control(
    "Édition spéciale : la Greek",
    options=["XL", "XXL"],
    format_func=lambda t: f"Greek {t}",
    key="filtre_greek",
)

# La taille réellement envoyée aux requêtes SQL (paramètre :taille)
if format_greek:
    taille = format_greek
    couleur = TURQUOISE          # les graphiques passent en turquoise
    if categorie not in (None, "Classic"):
        st.sidebar.caption("La Greek est une Classic : choisis Classic ou Toutes pour la voir.")
else:
    taille = None if choix_taille == "Toutes" else choix_taille

# Le style : un encadré turquoise, un drapeau grec dessiné en CSS et le bouton actif en turquoise.
# Le drapeau est dessiné en CSS car l'emoji 🇬🇷 s'affiche "GR" sous Windows.
# Il fait 27 x 18 px : 9 bandes de 2 px, avec un carré bleu de 10 px et sa croix blanche.
st.markdown(f"""
<style>
.st-key-filtre_greek {{
    width: 100% !important;
    padding: 10px 12px; border-radius: 10px;
    border: 1px solid {TURQUOISE}66; background: {TURQUOISE}14;
}}
.st-key-filtre_greek [data-testid="stWidgetLabel"] p {{ font-weight: 600; color: {TURQUOISE}; }}
.st-key-filtre_greek [data-testid="stWidgetLabel"] p::before {{
    content: ""; display: inline-block; width: 27px; height: 18px;
    margin-right: 8px; vertical-align: -4px; border-radius: 2px;
    background:
        linear-gradient(#fff, #fff) 0 4px / 10px 2px no-repeat,
        linear-gradient(#fff, #fff) 4px 0 / 2px 10px no-repeat,
        linear-gradient(#0d5eaf, #0d5eaf) 0 0 / 10px 10px no-repeat,
        repeating-linear-gradient(#0d5eaf 0 2px, #fff 2px 4px);
}}
.st-key-filtre_greek button {{ border-color: {TURQUOISE}88; }}
.st-key-filtre_greek button[aria-checked="true"] {{
    background: {TURQUOISE} !important; border-color: {TURQUOISE} !important;
}}
.st-key-filtre_greek button[aria-checked="true"] p {{ color: #fff !important; }}
</style>
""", unsafe_allow_html=True)

# Bonus : quand une Greek est choisie, le fond de la page passe aussi en turquoise.
# Ce style est injecté après celui des catégories, donc il prend le dessus.
if format_greek:
    st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{ background-color: {TURQUOISE}14; }}
[data-testid="stSidebar"]          {{ background-color: {TURQUOISE}22; }}
</style>
""", unsafe_allow_html=True)
