# =====================================================================
# 1. Imports
# =====================================================================
# importation des bibliothèques nécessaires
import streamlit as st
import sqlite3 as sql
import pandas as pd
import io, wave, base64
import numpy as np
from pathlib import Path
import plotly.express as px


# =====================================================================
# 2. Configuration de la page (toujours la première commande Streamlit)
# =====================================================================
st.set_page_config(page_title="Plato's Pizza", page_icon="🍕", layout="wide")


# =====================================================================
# 3. Connexion et chargement des données
# =====================================================================
# Connexion à la base SQLite, ouverte une seule fois puis réutilisée :
# Streamlit relit le script à chaque interaction, le cache évite de rouvrir la base à chaque clic.
@st.cache_resource
def get_connection():
    # Path(__file__).parent : la base est cherchée à côté de app.py, d'où que l'on lance l'application
    base = Path(__file__).parent / "plato_pizza.db"
    # Si la base n'existe pas encore (ex. premier lancement sur Streamlit Cloud),
    # ou si elle est vide ou incomplète (pas de table dim_commande),
    # on la construit à partir des CSV du dossier data/ avec le script preparer_base.py
    base_complete = False
    if base.exists():
        with sql.connect(base) as test:
            base_complete = test.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'dim_commande'"
            ).fetchone()[0] == 1
    if not base_complete:
        from preparer_base import creer_base
        with st.spinner("Première ouverture : création de la base de données à partir des CSV..."):
            creer_base(afficher=False)
    return sql.connect(base, check_same_thread=False)


# Résultat de requête mis en cache : si les mêmes filtres sont redemandés,
# le résultat est servi depuis la mémoire au lieu de réinterroger la base.
@st.cache_data
def charger(requete, params):
    return pd.read_sql(requete, get_connection(), params=params)


# Mise en forme commune à tous les graphiques : même hauteur, fond transparent
# (pour laisser voir la teinte de la catégorie) et marges réduites.
# Une fonction évite de répéter les mêmes lignes sous chaque graphique.
def mise_en_forme(fig, hauteur=400):
    fig.update_layout(
        height=hauteur,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=60, b=40, l=10, r=10),
        legend_title_text="",
    )
    return fig


# Jours de la semaine en français (pandas renvoie 0 = lundi ... 6 = dimanche)
JOURS_FR = ["Lun.", "Mar.", "Mer.", "Jeu.", "Ven.", "Sam.", "Dim."]
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]


def nom_mois(aaaa_mm):
    # "2015-07" -> "juillet 2015"
    return f"{MOIS_FR[int(aaaa_mm[5:]) - 1]} {aaaa_mm[:4]}"


def format_euros(valeur, decimales=0):
    # 12345.6 -> "12 346 €" (séparateur de milliers français)
    return f"{valeur:,.{decimales}f} €".replace(",", " ")


# Illustrations des onglets, dessinées en SVG (des formes simples : cercles, lignes, chemins).
# Elles n'ont pas de couleur fixe : "currentColor" prend la couleur du filtre catégorie.
ILLUSTRATIONS = {
    # Une courbe qui monte, posée sur un axe
    "vue": '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
           '<path d="M8 8v48h48"/><polyline points="14,44 24,32 34,38 46,20 54,24"/>'
           '<circle cx="24" cy="32" r="3" fill="currentColor"/><circle cx="46" cy="20" r="3" fill="currentColor"/></svg>',
    # Une horloge
    "rythme": '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">'
              '<circle cx="32" cy="34" r="22"/><path d="M32 20v14l10 6"/><path d="M26 6h12M32 6v6"/>'
              '<path d="M50 14l4-4"/></svg>',
    # Une pizza coupée en parts, avec du pepperoni
    "carte": '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">'
             '<circle cx="32" cy="32" r="24"/><circle cx="32" cy="32" r="18" stroke-width="1.5"/>'
             '<path d="M32 8v48M8 32h48M15 15l34 34M49 15L15 49" stroke-width="1.5"/>'
             '<circle cx="24" cy="22" r="3" fill="currentColor"/><circle cx="41" cy="27" r="3" fill="currentColor"/>'
             '<circle cx="28" cy="42" r="3" fill="currentColor"/><circle cx="42" cy="41" r="2.5" fill="currentColor"/></svg>',
    # Une cible avec sa flèche
    "reco": '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">'
            '<circle cx="30" cy="34" r="22"/><circle cx="30" cy="34" r="13"/><circle cx="30" cy="34" r="4" fill="currentColor"/>'
            '<path d="M30 34L54 10M46 10h8v8"/></svg>',
    # Un panier de courses
    "comportement": '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
                    '<path d="M8 24h48l-6 28H14z"/><path d="M20 24l8-14M44 24l-8-14"/>'
                    '<path d="M24 32v12M32 32v12M40 32v12"/></svg>',
}


# Images d'illustration des onglets : assets/illustrations/onglet_vue.png, onglet_rythme.png...
# Pour mettre tes propres photos, dépose un fichier .jpg du même nom (ex. onglet_vue.jpg) :
# il est utilisé en priorité. S'il n'y a aucune image, le bandeau s'affiche sans.
DOSSIER_IMAGES = Path(__file__).parent / "assets" / "illustrations"


@st.cache_data
def image_base64(nom):
    # Dans du HTML, une image locale doit être "embarquée" : on la convertit en texte base64.
    for extension, type_mime in [(".jpg", "image/jpeg"), (".jpeg", "image/jpeg"), (".png", "image/png")]:
        fichier = DOSSIER_IMAGES / f"{nom}{extension}"
        if fichier.exists():
            return f"data:{type_mime};base64,{base64.b64encode(fichier.read_bytes()).decode()}"
    return None


def bandeau(illustration, titre, question, chiffres):
    # Bandeau en haut d'un onglet : une icône, la question métier, 3 chiffres clés et une image.
    # chiffres = liste de couples (libellé, valeur), par ex. [("Heure de pointe", "12 h"), ...]
    # Le HTML est écrit sur une seule ligne : en Markdown, une ligne indentée de 4 espaces
    # serait affichée comme du code au lieu d'être interprétée.
    puces = "".join(f'<div class="bd-chiffre"><span>{lib}</span><b>{val}</b></div>' for lib, val in chiffres)
    image = image_base64(f"onglet_{illustration}")
    bloc_image = f'<img class="bd-image" src="{image}" alt="{titre}">' if image else ""
    st.markdown(
        f'<div class="bandeau"><div class="bd-illu">{ILLUSTRATIONS[illustration]}</div>'
        f'<div class="bd-texte"><div class="bd-titre">{titre}</div><div class="bd-question">{question}</div>'
        f'<div class="bd-chiffres">{puces}</div></div>{bloc_image}</div>',
        unsafe_allow_html=True,
    )


# =====================================================================
# 4. Requêtes SQL (définies en haut : elles doivent exister avant d'être utilisées)
# =====================================================================
# Une variable par question métier, copiée de analyse.sql (Q1 à Q12).
# Toutes utilisent les mêmes paramètres :date_debut, :date_fin, :categorie, :taille.
# Q7 ignore :categorie, Q8 ignore :taille, Q10 et Q12 n'utilisent que les dates :
# les paramètres en trop dans le dictionnaire params sont simplement ignorés.

REQ_KPI = """
-- Q1. Bilan de la période : les 5 indicateurs clés ----------------------
SELECT
    ROUND(SUM(fv.quantity * dp.price), 2)                                   AS chiffre_affaires,
    COUNT(DISTINCT fv.order_id)                                             AS nb_commandes,
    SUM(fv.quantity)                                                        AS pizzas_vendues,
    ROUND(SUM(fv.quantity * dp.price) / COUNT(DISTINCT fv.order_id), 2)     AS panier_moyen,
    ROUND(1.0 * SUM(fv.quantity) / COUNT(DISTINCT fv.order_id), 2)          AS pizzas_par_commande
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille);
"""

REQ_MENSUEL = """
-- Q2. Évolution mensuelle du CA et des commandes ---------------------
SELECT
    strftime('%Y-%m', dc.order_date)            AS mois,
    ROUND(SUM(fv.quantity * dp.price), 2)       AS chiffre_affaires,
    COUNT(DISTINCT fv.order_id)                 AS nb_commandes,
    SUM(fv.quantity)                            AS pizzas_vendues
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille)
GROUP BY mois
ORDER BY mois;
"""

REQ_HEURES = """
-- Q3. Activité et panier moyen par heure de la journée --------------
-- nb_jours_ouverts permet de calculer une moyenne de commandes par jour et par heure
SELECT
    CAST(strftime('%H', dc.order_time) AS INTEGER)                  AS heure,
    COUNT(DISTINCT fv.order_id)                                     AS nb_commandes,
    ROUND(SUM(fv.quantity * dp.price), 2)                           AS chiffre_affaires,
    ROUND(SUM(fv.quantity * dp.price) / COUNT(DISTINCT fv.order_id), 2) AS panier_moyen,
    COUNT(DISTINCT dc.order_date)                                   AS nb_jours_ouverts,
    ROUND(1.0 * COUNT(DISTINCT fv.order_id)
              / COUNT(DISTINCT dc.order_date), 1)                   AS commandes_moy_par_jour
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille)
GROUP BY heure
ORDER BY heure;
"""

REQ_JOURS = """
-- Q4. Activité et panier moyen par jour de la semaine ---------------
-- strftime('%w') renvoie 0 = dimanche ... 6 = samedi ; on remet lundi en premier
SELECT
    CASE strftime('%w', dc.order_date)
        WHEN '1' THEN '1-Lundi'    WHEN '2' THEN '2-Mardi'   WHEN '3' THEN '3-Mercredi'
        WHEN '4' THEN '4-Jeudi'    WHEN '5' THEN '5-Vendredi' WHEN '6' THEN '6-Samedi'
        ELSE '7-Dimanche'
    END                                                             AS jour_semaine,
    COUNT(DISTINCT fv.order_id)                                     AS nb_commandes,
    ROUND(SUM(fv.quantity * dp.price), 2)                           AS chiffre_affaires,
    ROUND(SUM(fv.quantity * dp.price) / COUNT(DISTINCT fv.order_id), 2) AS panier_moyen,
    COUNT(DISTINCT dc.order_date)                                   AS nb_jours,
    ROUND(1.0 * COUNT(DISTINCT fv.order_id) / COUNT(DISTINCT dc.order_date), 1) AS commandes_moy_par_jour,
    ROUND(SUM(fv.quantity * dp.price) / COUNT(DISTINCT dc.order_date), 2) AS ca_moyen_par_jour
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille)
GROUP BY jour_semaine
ORDER BY jour_semaine;
"""

REQ_TOP_JOURS = """
-- Q5a. Les 10 meilleurs jours (CA) ----------------------------------
SELECT
    dc.order_date                               AS jour,
    ROUND(SUM(fv.quantity * dp.price), 2)       AS chiffre_affaires,
    COUNT(DISTINCT fv.order_id)                 AS nb_commandes
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille)
GROUP BY jour
ORDER BY chiffre_affaires DESC
LIMIT 10;
"""

REQ_FLOP_JOURS = """
-- Q5b. Les 10 jours les plus faibles (CA) ---------------------------
SELECT
    dc.order_date                               AS jour,
    ROUND(SUM(fv.quantity * dp.price), 2)       AS chiffre_affaires,
    COUNT(DISTINCT fv.order_id)                 AS nb_commandes
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille)
GROUP BY jour
ORDER BY chiffre_affaires ASC
LIMIT 10;
"""

REQ_RECETTES = """
-- Q6. Classement des recettes (toutes tailles confondues) ------------
-- Streamlit affiche les 5 premières (top) et les 5 dernières (flop)
SELECT
    dp.name                                                         AS pizza,
    dp.category                                                     AS categorie,
    SUM(fv.quantity)                                                AS pizzas_vendues,
    ROUND(SUM(fv.quantity * dp.price), 2)                           AS chiffre_affaires,
    RANK() OVER (ORDER BY SUM(fv.quantity * dp.price) DESC)         AS rang_ca,
    RANK() OVER (ORDER BY SUM(fv.quantity) DESC)                    AS rang_quantite
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille)
GROUP BY dp.pizza_type_id, dp.name, dp.category
ORDER BY chiffre_affaires DESC;
"""

REQ_CATEGORIES = """
-- Q7. Poids de chaque catégorie --------------------------------------
-- La fonction fenêtre SUM(...) OVER () donne le total pour calculer la part en %
SELECT
    dp.category                                                     AS categorie,
    SUM(fv.quantity)                                                AS pizzas_vendues,
    ROUND(SUM(fv.quantity * dp.price), 2)                           AS chiffre_affaires,
    ROUND(100.0 * SUM(fv.quantity * dp.price)
               / SUM(SUM(fv.quantity * dp.price)) OVER (), 1)       AS part_ca_pct
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:taille IS NULL OR dp.size = :taille)
GROUP BY dp.category
ORDER BY chiffre_affaires DESC;
"""

REQ_TAILLES = """
-- Q8. Ventes par taille ----------------------------------------------
SELECT
    dp.size                                                         AS taille,
    SUM(fv.quantity)                                                AS pizzas_vendues,
    ROUND(SUM(fv.quantity * dp.price), 2)                           AS chiffre_affaires,
    ROUND(100.0 * SUM(fv.quantity * dp.price)
               / SUM(SUM(fv.quantity * dp.price)) OVER (), 1)       AS part_ca_pct,
    ROUND(SUM(fv.quantity * dp.price) / SUM(fv.quantity), 2)        AS prix_moyen
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id
WHERE dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
GROUP BY dp.size
ORDER BY CASE dp.size WHEN 'S' THEN 1 WHEN 'M' THEN 2 WHEN 'L' THEN 3
                      WHEN 'XL' THEN 4 ELSE 5 END;
"""

REQ_INGREDIENTS = """
-- Q9. Ingrédients les plus consommés ---------------------------------
-- La colonne ingredients est une liste "a, b, c" : une CTE récursive la
-- découpe en une ligne par ingrédient, puis on pondère par les quantités vendues.
WITH RECURSIVE decoupe(pizza_id, ingredient, reste) AS (
    SELECT pizza_id, '', ingredients || ','
    FROM dim_pizza
    UNION ALL
    SELECT pizza_id,
           TRIM(substr(reste, 1, instr(reste, ',') - 1)),
           substr(reste, instr(reste, ',') + 1)
    FROM decoupe
    WHERE reste <> ''
)
SELECT
    d.ingredient                                AS ingredient,
    SUM(fv.quantity)                            AS pizzas_vendues_avec,
    COUNT(DISTINCT dp.pizza_type_id)            AS nb_recettes
FROM decoupe d
JOIN dim_pizza dp       ON dp.pizza_id = d.pizza_id
JOIN faits_ventes fv    ON fv.pizza_id = d.pizza_id
JOIN dim_commande dc    ON dc.order_id = fv.order_id
WHERE d.ingredient <> ''
  AND dc.order_date BETWEEN :date_debut AND :date_fin
  AND (:categorie IS NULL OR dp.category = :categorie)
  AND (:taille    IS NULL OR dp.size     = :taille)
GROUP BY d.ingredient
ORDER BY pizzas_vendues_avec DESC;
"""

REQ_TAILLE_COMMANDES = """
-- Q10. Taille des commandes (nombre de pizzas par commande) ----------
-- Sous-requête : une ligne par commande avec son nombre de pizzas et son montant
SELECT
    nb_pizzas,
    COUNT(*)                                    AS nb_commandes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_commandes_pct,
    ROUND(AVG(montant), 2)                      AS montant_moyen
FROM (
    SELECT fv.order_id,
           SUM(fv.quantity)                     AS nb_pizzas,
           SUM(fv.quantity * dp.price)          AS montant
    FROM faits_ventes fv
    JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
    JOIN dim_commande dc ON dc.order_id = fv.order_id
    WHERE dc.order_date BETWEEN :date_debut AND :date_fin
    GROUP BY fv.order_id
) AS commandes
GROUP BY nb_pizzas
ORDER BY nb_pizzas;
"""

REQ_CRENEAUX = """
-- Q11. Zones creuses : commandes moyennes par jour de semaine x heure --
-- Résultat "long" (une ligne par couple jour/heure) : Streamlit le pivote en carte de chaleur.
-- Moyenne = commandes du créneau / nombre de jours de ce type dans la période.
WITH jours AS (
    SELECT strftime('%w', order_date) AS num_jour,
           COUNT(DISTINCT order_date) AS nb_jours
    FROM dim_commande
    WHERE order_date BETWEEN :date_debut AND :date_fin
    GROUP BY num_jour
)
SELECT
    CASE c.num_jour
        WHEN '1' THEN '1-Lundi'    WHEN '2' THEN '2-Mardi'   WHEN '3' THEN '3-Mercredi'
        WHEN '4' THEN '4-Jeudi'    WHEN '5' THEN '5-Vendredi' WHEN '6' THEN '6-Samedi'
        ELSE '7-Dimanche'
    END                                                     AS jour_semaine,
    c.heure,
    c.nb_commandes,
    ROUND(1.0 * c.nb_commandes / j.nb_jours, 1)             AS commandes_moy
FROM (
    SELECT strftime('%w', dc.order_date)                    AS num_jour,
           CAST(strftime('%H', dc.order_time) AS INTEGER)   AS heure,
           COUNT(DISTINCT fv.order_id)                      AS nb_commandes
    FROM faits_ventes fv
    JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
    JOIN dim_commande dc ON dc.order_id = fv.order_id
    WHERE dc.order_date BETWEEN :date_debut AND :date_fin
      AND (:categorie IS NULL OR dp.category = :categorie)
      AND (:taille    IS NULL OR dp.size     = :taille)
    GROUP BY num_jour, heure
) AS c
JOIN jours j ON j.num_jour = c.num_jour
ORDER BY jour_semaine, c.heure;
"""

REQ_PANIER_CRENEAU = """
-- Q12. Panier moyen par créneau horaire ---------------------------------
-- Créneaux métier : matin < 12h, déjeuner 12h-14h, après-midi 14h-17h,
-- dîner 17h-20h, soirée >= 20h. Calcul au niveau commande (sans filtre produit).
SELECT
    creneau,
    COUNT(*)                                                AS nb_commandes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)      AS part_commandes_pct,
    ROUND(SUM(montant), 2)                                  AS chiffre_affaires,
    ROUND(AVG(montant), 2)                                  AS panier_moyen,
    ROUND(AVG(nb_pizzas), 2)                                AS pizzas_par_commande
FROM (
    SELECT fv.order_id,
           CASE
               WHEN CAST(strftime('%H', dc.order_time) AS INTEGER) < 12 THEN '1-Matin (<12h)'
               WHEN CAST(strftime('%H', dc.order_time) AS INTEGER) < 14 THEN '2-Déjeuner (12h-14h)'
               WHEN CAST(strftime('%H', dc.order_time) AS INTEGER) < 17 THEN '3-Après-midi (14h-17h)'
               WHEN CAST(strftime('%H', dc.order_time) AS INTEGER) < 20 THEN '4-Dîner (17h-20h)'
               ELSE '5-Soirée (>=20h)'
           END                                              AS creneau,
           SUM(fv.quantity)                                 AS nb_pizzas,
           SUM(fv.quantity * dp.price)                      AS montant
    FROM faits_ventes fv
    JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
    JOIN dim_commande dc ON dc.order_id = fv.order_id
    WHERE dc.order_date BETWEEN :date_debut AND :date_fin
    GROUP BY fv.order_id, creneau
) AS commandes
GROUP BY creneau
ORDER BY creneau;
"""

# Jours ouverts dans la période (jours avec au moins une commande), pour les limites de l'analyse
REQ_JOURS_OUVERTS = """
SELECT COUNT(DISTINCT order_date)                                   AS jours_ouverts,
       CAST(julianday(:date_fin) - julianday(:date_debut) + 1 AS INTEGER) AS jours_calendrier
FROM dim_commande
WHERE order_date BETWEEN :date_debut AND :date_fin;
"""

REQ_BORNES = "SELECT MIN(order_date) AS date_min, MAX(order_date) AS date_max FROM dim_commande"
bornes = charger(REQ_BORNES, None)   # pas de paramètre pour cette requête

date_min = pd.to_datetime(bornes.loc[0, "date_min"]).date()
date_max = pd.to_datetime(bornes.loc[0, "date_max"]).date()


# =====================================================================
# 5. Titre et introduction
# =====================================================================
st.title(f"Plato's Pizza : pilotage de l'activité {date_min.year}")
st.caption("Tableau de bord d’aide à la décision : ventes, affluence et performance de la carte")
st.write(" Ce tableau de bord présente l’activité de la pizzeria sur l’année 2015. Utilisez les filtres pour analyser une période, une catégorie ou une taille, et identifier les leviers d’action : organisation des équipes, évolution de la carte, panier moyen.")


# =====================================================================
# 6. Filtres de la sidebar : période, catégorie, taille et Greek
# =====================================================================
st.sidebar.header("Filtres d'analyse")

# 6a. Période : le widget renvoie un tuple (date_début, date_fin)
periode = st.sidebar.slider(
    "Période",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)
date_debut, date_fin = periode

# 6b. Catégorie : une illustration, une couleur de police Streamlit et un code couleur précis par catégorie
STYLE_CATEGORIES = {
    "Toutes":  ("🍽️", "gray",   "#6b7280"),
    "Classic": ("🍕", "blue",   "#2a78d6"),
    "Supreme": ("🥓", "red",    "#d03b3b"),
    "Chicken": ("🍗", "orange", "#eb6834"),
    "Veggie":  ("🥦", "green",  "#1f9d55"),
}

# Dictionnaire catégorie -> couleur, pour colorer chaque barre selon SA catégorie
COULEURS_CAT = {cat: style[2] for cat, style in STYLE_CATEGORIES.items()}

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

# 6c. Le son de découpe.
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

# 6d. Taille (curseur couteau) et édition spéciale Greek
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

# Taille affichée : la Greek déclenche aussi la découpe ("Greek XL" / "Greek XXL")
taille_affichee = f"Greek {format_greek}" if format_greek else choix_taille

# 6e. Détecter un changement de taille.
#    session_state garde la taille précédente et compte les coupes d'une exécution à l'autre.
a_change = st.session_state.get("taille_precedente", taille_affichee) != taille_affichee
if a_change:
    st.session_state["nb_coupes"] = st.session_state.get("nb_coupes", 0) + 1
st.session_state["taille_precedente"] = taille_affichee
nb_coupes = st.session_state.get("nb_coupes", 0)

# Astuce : le navigateur ne rejoue pas un élément identique à celui déjà affiché.
# On rend donc chaque animation et chaque son légèrement différents grâce au compteur nb_coupes.
zone_animation = st.sidebar.empty()
son_actif = st.sidebar.toggle("🔊 Effets sonores", value=True)

if a_change:
    # L'animation : un couteau tranche la pizza, puis les deux moitiés s'écartent.
    #     La classe alterne entre v0 et v1 : le nom de l'animation CSS change, ce qui la relance.
    zone_animation.markdown(f"""
<div class="coupe-pizza v{nb_coupes % 2}">
  <div class="moitie gauche"></div>
  <div class="moitie droite"></div>
  <div class="couteau">🔪</div>
</div>
<p class="coupe-texte v{nb_coupes % 2}">Taille {taille_affichee}, à la coupe !</p>
""", unsafe_allow_html=True)

    # Le son : un contenu différent à chaque coupe, donc rejoué à chaque fois
    if son_actif:
        if FICHIER_SON.exists():
            # Les octets nuls ajoutés à la fin sont ignorés à la lecture mais rendent le fichier unique
            son = FICHIER_SON.read_bytes() + bytes(nb_coupes % 50 + 1)
            st.sidebar.audio(son, format="audio/mpeg", autoplay=True)
        else:
            st.sidebar.audio(son_decoupe(nb_coupes % 50), format="audio/wav", autoplay=True)

# 6f. Le style : la poignée du curseur des tailles devient un couteau 🔪 qui fait un mouvement
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


# =====================================================================
# 7. Paramètres envoyés aux requêtes SQL
# =====================================================================
params = {
    "date_debut": str(date_debut),
    "date_fin": str(date_fin),
    "categorie": categorie,
    "taille": taille,
}


# =====================================================================
# 8. Indicateurs clés (KPI)
# =====================================================================
kpi = charger(REQ_KPI, params)

# Garde-fou : si aucun résultat (ex. Veggie + Greek XL), on prévient et on arrête le script
# avant le formatage des KPI. COUNT renvoie 0 (et non NULL), c'est donc la colonne à tester.
if kpi.loc[0, "nb_commandes"] == 0:
    st.warning("Aucune vente ne correspond à ces filtres. Élargis la catégorie ou la taille.")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)
ca = kpi.loc[0, "chiffre_affaires"]

col1.metric("Chiffre d'affaires", f"{ca:,.0f} €".replace(",", " "))
col2.metric("Nombre de commandes", f"{kpi.loc[0, 'nb_commandes']:,.0f}".replace(",", " "))
col3.metric("Pizzas vendues", f"{kpi.loc[0, 'pizzas_vendues']:,.0f}".replace(",", " "))
col4.metric("Panier moyen", f"{kpi.loc[0, 'panier_moyen']:,.2f} €".replace(",", " "))
col5.metric("Pizzas par commande", f"{kpi.loc[0, 'pizzas_par_commande']:,.2f}".replace(",", " "))


# =====================================================================
# 9. Onglets et graphiques
# =====================================================================
# Style des bandeaux et des onglets, à la couleur du filtre (catégorie, ou turquoise pour la Greek)
st.markdown(f"""
<style>
.bandeau {{
    display: flex; align-items: center; gap: 22px; flex-wrap: wrap;
    margin: 6px 0 18px; padding: 18px 22px; border-radius: 14px;
    background: linear-gradient(120deg, {couleur}24, {couleur}08);
    border: 1px solid {couleur}40;
    animation: bd-entree 0.5s ease-out;
}}
.bd-illu {{
    flex: none; width: 76px; height: 76px; border-radius: 50%;
    display: grid; place-items: center;
    background: {couleur}1f; color: {couleur};
}}
.bd-illu svg {{ width: 44px; height: 44px; }}
.bd-texte {{ flex: 1; min-width: 240px; }}
.bd-image {{
    flex: none; width: 260px; max-width: 100%; aspect-ratio: 16 / 9; object-fit: cover;
    border-radius: 12px; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.10);
}}
.bd-titre {{ font-size: 1.35rem; font-weight: 700; line-height: 1.2; }}
.bd-question {{ opacity: 0.75; margin: 2px 0 12px; }}
.bd-chiffres {{ display: flex; gap: 10px; flex-wrap: wrap; }}
.bd-chiffre {{
    padding: 6px 12px; border-radius: 8px; background: rgba(255, 255, 255, 0.65);
    border-left: 3px solid {couleur}; line-height: 1.25;
}}
.bd-chiffre span {{ display: block; font-size: 0.75rem; opacity: 0.7; }}
.bd-chiffre b {{ font-size: 1.05rem; }}
@keyframes bd-entree {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}

/* Onglets : plus grands, onglet actif à la couleur du filtre */
[data-testid="stTab"] p {{ font-size: 1.02rem; font-weight: 600; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: {couleur} !important; }}
[data-testid="stTab"][aria-selected="true"] > div:last-child {{
    background-color: {couleur} !important; border-color: {couleur} !important;
}}
</style>
""", unsafe_allow_html=True)

onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs(["📈 Vue d'ensemble", "⏰ Rythme de l'activité", "🍕 Performance de la carte", "🧺 Comportement d'achat", "🎯 Recommandations"])

# Règle d'indentation des onglets :
#   4 espaces sous "with ongletX:"  -> dans l'onglet, pleine largeur
#   8 espaces sous "with gauche:"   -> dans la colonne de gauche de cet onglet
# Chaque graphique est suivi d'un "💡" : la conclusion à retenir, recalculée selon les filtres.


# ---------------------------------------------------------------------
# Onglet 1 : vue d'ensemble. Comment évolue le CA, et quels jours sortent du lot ?
# ---------------------------------------------------------------------
with onglet1:
    df_mensuel = charger(REQ_MENSUEL, params)
    # Les 10 meilleurs et les 10 plus faibles jours : repérer les événements (fêtes, vacances, météo...)
    df_top_jours = charger(REQ_TOP_JOURS, params)
    df_flop_jours = charger(REQ_FLOP_JOURS, params)
    for df in (df_top_jours, df_flop_jours):
        dates = pd.to_datetime(df["jour"])
        # "2015-11-27" -> "Ven. 27/11" : plus lisible pour le gérant
        df["date"] = [f"{JOURS_FR[d.dayofweek]} {d:%d/%m}" for d in dates]

    mois_max = df_mensuel.loc[df_mensuel["chiffre_affaires"].idxmax()]
    bandeau(
        "vue",
        "Vue d'ensemble",
        "Comment évolue le chiffre d'affaires, et quels jours sortent du lot ?",
        [
            ("Chiffre d'affaires", format_euros(ca)),
            ("Meilleur mois", nom_mois(mois_max["mois"])),
            ("Meilleur jour", f"{df_top_jours.loc[0, 'date']} · {format_euros(df_top_jours.loc[0, 'chiffre_affaires'])}"),
        ],
    )

    fig = px.line(
        df_mensuel,
        x="mois",
        y="chiffre_affaires",
        title="Évolution mensuelle du chiffre d'affaires",
        markers=True,
        labels={"mois": "Mois", "chiffre_affaires": "Chiffre d'affaires (€)"},
        color_discrete_sequence=[couleur],
    )
    fig.update_traces(line_width=3, marker_size=9)
    fig.update_yaxes(rangemode="tozero")        # l'axe part de 0 : on ne grossit pas les écarts
    st.plotly_chart(mise_en_forme(fig))

    if len(df_mensuel) > 1:
        mois_max = df_mensuel.loc[df_mensuel["chiffre_affaires"].idxmax()]
        mois_min = df_mensuel.loc[df_mensuel["chiffre_affaires"].idxmin()]
        st.caption(f"💡 Meilleur mois : {nom_mois(mois_max['mois'])} ({format_euros(mois_max['chiffre_affaires'])}). "
                   f"Mois le plus faible : {nom_mois(mois_min['mois'])} ({format_euros(mois_min['chiffre_affaires'])}).")

    gauche, droite = st.columns(2)

    with gauche:
        fig = px.bar(
            df_top_jours,
            x="chiffre_affaires",
            y="date",
            orientation="h",
            title="Les 10 meilleurs jours",
            labels={"chiffre_affaires": "Chiffre d'affaires (€)", "date": "", "nb_commandes": "Commandes"},
            hover_data=["nb_commandes"],
            color_discrete_sequence=[couleur],
        )
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(mise_en_forme(fig))

    with droite:
        fig = px.bar(
            df_flop_jours,
            x="chiffre_affaires",
            y="date",
            orientation="h",
            title="Les 10 jours les plus faibles",
            labels={"chiffre_affaires": "Chiffre d'affaires (€)", "date": "", "nb_commandes": "Commandes"},
            hover_data=["nb_commandes"],
            color_discrete_sequence=["#9ca3af"],     # gris : ce sont les jours "à expliquer"
        )
        fig.update_yaxes(categoryorder="total descending")
        st.plotly_chart(mise_en_forme(fig))


# ---------------------------------------------------------------------
# Onglet 2 : rythme de l'activité. Quand les clients commandent-ils (heures, jours, créneaux) ?
# ---------------------------------------------------------------------
with onglet2:
    df_heures = charger(REQ_HEURES, params)
    df_jours = charger(REQ_JOURS, params)
    df_jours["jour"] = df_jours["jour_semaine"].str[2:]     # "1-Lundi" -> "Lundi"
    df_creneaux = charger(REQ_CRENEAUX, params)
    df_creneaux["jour"] = df_creneaux["jour_semaine"].str[2:]

    heure_pointe = df_heures.loc[df_heures["commandes_moy_par_jour"].idxmax(), "heure"]
    jour_fort = df_jours.loc[df_jours["ca_moyen_par_jour"].idxmax(), "jour"]
    creux = df_creneaux.loc[df_creneaux["commandes_moy"].idxmin()]
    bandeau(
        "rythme",
        "Rythme de l'activité",
        "Quand les clients commandent-ils ? De quoi organiser les plannings de l'équipe.",
        [
            ("Heure de pointe", f"{heure_pointe} h"),
            ("Jour le plus fort", jour_fort),
            ("Créneau le plus creux", f"{creux['jour']} {creux['heure']} h"),
        ],
    )

    gauche, droite = st.columns(2)

    with gauche:
        fig = px.bar(
            df_heures,
            x="heure",
            y="commandes_moy_par_jour",
            title="Commandes moyennes par heure de la journée",
            labels={"heure": "Heure", "commandes_moy_par_jour": "Commandes moyennes par jour"},
            color_discrete_sequence=[couleur],
        )
        fig.update_xaxes(dtick=1, ticksuffix=" h")
        st.plotly_chart(mise_en_forme(fig))
        pointe = df_heures.nlargest(2, "commandes_moy_par_jour")["heure"].sort_values().tolist()
        st.caption(f"💡 Heures de pointe : {' et '.join(f'{h} h' for h in pointe)}. "
                   "C'est là qu'il faut le plus de monde en cuisine et en livraison.")

    with droite:
        fig = px.bar(
            df_jours,
            x="jour",
            y="ca_moyen_par_jour",
            title="Chiffre d'affaires moyen par jour de la semaine",
            labels={"jour": "Jour de la semaine", "ca_moyen_par_jour": "Chiffre d'affaires moyen (€)"},
            text_auto=",.0f",
            color_discrete_sequence=[couleur],
        )
        st.plotly_chart(mise_en_forme(fig))
        j_max = df_jours.loc[df_jours["ca_moyen_par_jour"].idxmax()]
        j_min = df_jours.loc[df_jours["ca_moyen_par_jour"].idxmin()]
        if j_max["jour"] != j_min["jour"]:
            st.caption(f"💡 {j_max['jour']} est le jour le plus fort ({format_euros(j_max['ca_moyen_par_jour'])} en moyenne), "
                       f"{j_min['jour']} le plus calme ({format_euros(j_min['ca_moyen_par_jour'])}).")

    # Heatmap : 4 espaces, donc dans l'onglet mais hors des colonnes (pleine largeur)
    grille = df_creneaux.pivot(index="jour_semaine", columns="heure", values="commandes_moy")
    grille.index = grille.index.str[2:]
    grille = grille.fillna(0)
    fig = px.imshow(
        grille,
        aspect="auto",
        color_continuous_scale=["white", couleur],
        title="Commandes moyennes par jour et par heure : où renforcer, où alléger l'équipe",
        labels=dict(x="Heure", y="", color="Commandes / jour"),
    )
    fig.update_xaxes(dtick=1, ticksuffix=" h")
    st.plotly_chart(mise_en_forme(fig, hauteur=420))
    st.caption("💡 Les cases les plus foncées sont les créneaux à renforcer ; les plus claires, "
               "les créneaux où l'on peut alléger l'équipe ou lancer une offre.")


# ---------------------------------------------------------------------
# Onglet 3 : performance de la carte. Quelles recettes, catégories, tailles et ingrédients
# rapportent le plus (à mettre en avant) et le moins (à retravailler ou retirer) ?
# ---------------------------------------------------------------------
with onglet3:
    df_recettes = charger(REQ_RECETTES, params)
    # Noms plus courts à l'écran : "The Thai Chicken Pizza" -> "Thai Chicken"
    df_recettes["pizza"] = df_recettes["pizza"].str.replace("The ", "").str.replace(" Pizza", "")
    # Le tableau est trié par CA décroissant : head = les meilleures, tail = les plus faibles
    top = df_recettes.head(5)
    flop = df_recettes.tail(5)
    df_categories = charger(REQ_CATEGORIES, params)
    df_tailles = charger(REQ_TAILLES, params)

    bandeau(
        "carte",
        "Performance de la carte",
        "Quelles recettes mettre en avant, lesquelles retravailler ou retirer ?",
        [
            ("Recette n°1", top.iloc[0]["pizza"]),
            ("Catégorie n°1", df_categories.loc[df_categories["chiffre_affaires"].idxmax(), "categorie"]),
            ("Taille n°1", df_tailles.loc[df_tailles["chiffre_affaires"].idxmax(), "taille"]),
        ],
    )

    gauche, droite = st.columns(2)

    with gauche:
        fig = px.bar(
            top,
            x="chiffre_affaires",
            y="pizza",
            orientation="h",
            title="Top 5 des recettes (chiffre d'affaires)",
            labels={"chiffre_affaires": "Chiffre d'affaires (€)", "pizza": "", "categorie": "Catégorie"},
            color="categorie",
            color_discrete_map=COULEURS_CAT,
        )
        fig.update_yaxes(categoryorder="total ascending")     # la plus grosse barre en haut
        st.plotly_chart(mise_en_forme(fig))

    with droite:
        fig = px.bar(
            flop,
            x="chiffre_affaires",
            y="pizza",
            orientation="h",
            title="Flop 5 des recettes (chiffre d'affaires)",
            labels={"chiffre_affaires": "Chiffre d'affaires (€)", "pizza": "", "categorie": "Catégorie"},
            color="categorie",
            color_discrete_map=COULEURS_CAT,
        )
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(mise_en_forme(fig))

    if len(df_recettes) > 1:
        st.caption(f"💡 {top.iloc[0]['pizza']} rapporte {top.iloc[0]['chiffre_affaires'] / flop.iloc[-1]['chiffre_affaires']:.1f} fois "
                   f"plus que {flop.iloc[-1]['pizza']}. Les recettes du Flop sont à retravailler (prix, recette, visibilité) ou à retirer.")

    # Poids des catégories et des tailles

    gauche, droite = st.columns(2)

    with gauche:
        fig = px.pie(
            df_categories,
            names="categorie",
            values="chiffre_affaires",
            hole=0.55,
            title="Part du chiffre d'affaires par catégorie",
            color="categorie",
            color_discrete_map=COULEURS_CAT,
        )
        fig.update_traces(textinfo="label+percent", sort=False)
        st.plotly_chart(mise_en_forme(fig))
        st.caption("Ce graphique compare toujours les 4 catégories : il ignore le filtre catégorie.")

    with droite:
        fig = px.bar(
            df_tailles,
            x="taille",
            y="part_ca_pct",
            title="Part du chiffre d'affaires par taille",
            labels={"taille": "Taille", "part_ca_pct": "Part du CA (%)", "prix_moyen": "Prix moyen (€)"},
            text="part_ca_pct",
            hover_data=["prix_moyen", "pizzas_vendues"],
            color_discrete_sequence=[couleur],
        )
        fig.update_traces(texttemplate="%{text:.1f} %", textposition="outside", cliponaxis=False)
        st.plotly_chart(mise_en_forme(fig))
        st.caption("Ce graphique compare toujours toutes les tailles : il ignore le filtre taille.")

    # Les ingrédients les plus consommés : utile pour les achats et les stocks
    df_ingredients = charger(REQ_INGREDIENTS, params).head(10)
    fig = px.bar(
        df_ingredients,
        x="pizzas_vendues_avec",
        y="ingredient",
        orientation="h",
        title="Les 10 ingrédients les plus utilisés (en nombre de pizzas vendues)",
        labels={"pizzas_vendues_avec": "Pizzas vendues contenant l'ingrédient", "ingredient": "",
                "nb_recettes": "Nombre de recettes"},
        hover_data=["nb_recettes"],
        color_discrete_sequence=[couleur],
    )
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(mise_en_forme(fig, hauteur=420))
    st.caption("💡 Ces ingrédients sont prioritaires pour les achats : une rupture de stock toucherait le plus de commandes.")


# ---------------------------------------------------------------------
# Onglet 4 : comportement d'achat. Combien de pizzas par commande, et quel panier selon le moment ?
# Ces requêtes travaillent au niveau de la commande entière : seuls les filtres de période s'appliquent.
# ---------------------------------------------------------------------
with onglet4:
    df_taille_cmd = charger(REQ_TAILLE_COMMANDES, params)
    # Au-delà de 6 pizzas, les commandes sont rares (groupes, entreprises) : on les regroupe en "7+"
    df_taille_cmd["nb_pizzas_lib"] = df_taille_cmd["nb_pizzas"].apply(lambda n: str(n) if n <= 6 else "7+")
    df_taille_cmd = df_taille_cmd.groupby("nb_pizzas_lib", as_index=False, sort=False)[["nb_commandes", "part_commandes_pct"]].sum()

    df_panier = charger(REQ_PANIER_CRENEAU, params)
    df_panier["creneau"] = df_panier["creneau"].str[2:]     # "1-Matin (<12h)" -> "Matin (<12h)"

    part_une_pizza = df_taille_cmd.loc[df_taille_cmd["nb_pizzas_lib"] == "1", "part_commandes_pct"].sum()
    meilleur_panier = df_panier.loc[df_panier["panier_moyen"].idxmax()]
    bandeau(
        "comportement",
        "Comportement d'achat",
        "Combien commandent les clients, et à quel moment le panier est-il le plus élevé ? "
        "(commandes analysées en entier : seul le filtre de période s'applique)",
        [
            # Panier moyen sur les commandes entières : CA total des créneaux / nombre de commandes
            ("Panier moyen", format_euros(df_panier["chiffre_affaires"].sum() / df_panier["nb_commandes"].sum(), 2).replace(".", ",")),
            ("Commandes d'une seule pizza", f"{part_une_pizza:.0f} %"),
            ("Plus gros panier", meilleur_panier["creneau"].split(" (")[0]),
        ],
    )

    gauche, droite = st.columns(2)

    with gauche:
        fig = px.bar(
            df_taille_cmd,
            x="nb_pizzas_lib",
            y="part_commandes_pct",
            title="Nombre de pizzas par commande",
            labels={"nb_pizzas_lib": "Pizzas dans la commande", "part_commandes_pct": "Part des commandes (%)",
                    "nb_commandes": "Commandes"},
            text="part_commandes_pct",
            hover_data=["nb_commandes"],
            color_discrete_sequence=[couleur],
        )
        fig.update_xaxes(type="category")     # "1", "2"... "7+" sont des catégories, pas des nombres
        fig.update_traces(texttemplate="%{text:.0f} %", textposition="outside", cliponaxis=False)
        st.plotly_chart(mise_en_forme(fig))
        st.caption(f"💡 {part_une_pizza:.0f} % des commandes ne contiennent qu'une pizza : "
                   "un levier pour augmenter le panier (menu, 2e pizza à prix réduit, boisson).")

    with droite:
        fig = px.bar(
            df_panier,
            x="creneau",
            y="panier_moyen",
            title="Panier moyen par créneau horaire",
            labels={"creneau": "", "panier_moyen": "Panier moyen (€)", "nb_commandes": "Commandes",
                    "part_commandes_pct": "Part des commandes (%)"},
            text="panier_moyen",
            hover_data=["nb_commandes", "part_commandes_pct"],
            color_discrete_sequence=[couleur],
        )
        fig.update_traces(texttemplate="%{text:.2f} €", textposition="outside", cliponaxis=False)
        st.plotly_chart(mise_en_forme(fig))
        c_max = df_panier.loc[df_panier["panier_moyen"].idxmax()]
        st.caption(f"💡 Panier moyen le plus élevé : créneau {c_max['creneau']}, "
                   f"{format_euros(c_max['panier_moyen'], 2).replace('.', ',')}.")

    # Volume de commandes par créneau : où se concentre l'activité
    fig = px.bar(
        df_panier,
        x="part_commandes_pct",
        y="creneau",
        orientation="h",
        title="Répartition des commandes par créneau horaire",
        labels={"part_commandes_pct": "Part des commandes (%)", "creneau": "", "chiffre_affaires": "CA (€)"},
        text="part_commandes_pct",
        hover_data=["chiffre_affaires"],
        color_discrete_sequence=[couleur],
    )
    fig.update_yaxes(categoryorder="array", categoryarray=df_panier["creneau"].tolist()[::-1])
    fig.update_traces(texttemplate="%{text:.1f} %", textposition="outside", cliponaxis=False)
    st.plotly_chart(mise_en_forme(fig, hauteur=320))


# ---------------------------------------------------------------------
# Onglet 5 : recommandations et limites. Que doit faire le gérant, et jusqu'où peut-on se fier à l'analyse ?
# Les constats sont recalculés sur TOUTE la carte pour la période choisie (filtres catégorie et taille
# ignorés) : une recommandation porte sur la pizzeria entière, pas sur une seule catégorie.
# ---------------------------------------------------------------------
with onglet5:
    params_global = {**params, "categorie": None, "taille": None}

    g_kpi = charger(REQ_KPI, params_global)
    g_heures = charger(REQ_HEURES, params_global)
    g_jours = charger(REQ_JOURS, params_global)
    g_jours["jour"] = g_jours["jour_semaine"].str[2:]
    g_recettes = charger(REQ_RECETTES, params_global)
    g_recettes["pizza"] = g_recettes["pizza"].str.replace("The ", "").str.replace(" Pizza", "")
    g_tailles = charger(REQ_TAILLES, params_global)
    g_taille_cmd = charger(REQ_TAILLE_COMMANDES, params_global)
    g_panier = charger(REQ_PANIER_CRENEAU, params_global)
    g_panier["creneau"] = g_panier["creneau"].str[2:]
    g_ouverture = charger(REQ_JOURS_OUVERTS, params_global)

    # --- Les chiffres qui fondent les recommandations
    ca_total = g_kpi.loc[0, "chiffre_affaires"]
    prix_moyen_pizza = ca_total / g_kpi.loc[0, "pizzas_vendues"]

    pointes = g_heures.nlargest(4, "commandes_moy_par_jour").sort_values("heure")
    heures_pointe = ", ".join(f"{h} h" for h in pointes["heure"])
    seuil_creux = g_heures["commandes_moy_par_jour"].max() * 0.25
    heures_creuses = ", ".join(f"{h} h" for h in g_heures.loc[g_heures["commandes_moy_par_jour"] < seuil_creux, "heure"])

    j_fort = g_jours.loc[g_jours["ca_moyen_par_jour"].idxmax()]
    j_faible = g_jours.loc[g_jours["ca_moyen_par_jour"].idxmin()]

    une_pizza = g_taille_cmd.loc[g_taille_cmd["nb_pizzas"] == 1]
    nb_une_pizza = int(une_pizza["nb_commandes"].sum())
    part_une_pizza = une_pizza["part_commandes_pct"].sum()
    # Hypothèse illustrative : 10 % des commandes d'une seule pizza en ajoutent une deuxième
    gain_2e_pizza = nb_une_pizza * 0.10 * prix_moyen_pizza

    flop5 = g_recettes.tail(5)
    part_flop5 = flop5["chiffre_affaires"].sum() / g_recettes["chiffre_affaires"].sum() * 100
    derniere = g_recettes.iloc[-1]

    def part_taille(t):
        return g_tailles.loc[g_tailles["taille"] == t, "part_ca_pct"].sum()

    panier_max = g_panier.loc[g_panier["panier_moyen"].idxmax()]
    jours_ouverts = int(g_ouverture.loc[0, "jours_ouverts"])
    jours_calendrier = int(g_ouverture.loc[0, "jours_calendrier"])

    bandeau(
        "reco",
        "Recommandations et limites",
        "Que faire concrètement, et jusqu'où peut-on se fier à ces chiffres ? "
        "(calculé sur toute la carte, pour la période choisie)",
        [
            ("Recommandations", "6"),
            ("Gain estimé « 2e pizza »", format_euros(gain_2e_pizza)),
            ("Jours ouverts", f"{jours_ouverts} / {jours_calendrier}"),
        ],
    )

    # --- Les recommandations : constat chiffré -> action -> indicateur à suivre
    st.subheader("Recommandations")
    st.caption("Chaque recommandation part d'un constat chiffré tiré de la base, propose une action, "
               "et donne l'indicateur à suivre dans cette application pour mesurer son effet.")

    RECOMMANDATIONS = [
        {
            "titre": "Caler les plannings sur les coups de feu",
            "priorite": ":red-badge[Priorité haute]",
            "constat": f"Les heures de pointe sont {heures_pointe}. À l'inverse, {heures_creuses or 'aucune heure'} "
                       f"reçoivent moins d'un quart de l'activité de l'heure la plus chargée.",
            "action": "Renforcer cuisine et livraison sur les pointes du midi et du soir, alléger l'équipe sur les "
                      "heures creuses et y placer la préparation (pâtes, garnitures).",
            "suivi": "Heatmap jour × heure (onglet Rythme) et commandes moyennes par heure.",
        },
        {
            "titre": "Faire grossir le panier des commandes d'une seule pizza",
            "priorite": ":red-badge[Priorité haute]",
            "constat": f"{part_une_pizza:.0f} % des commandes ({nb_une_pizza:,} commandes) ne contiennent qu'une pizza. ".replace(",", " ")
                       + f"Une pizza rapporte en moyenne {format_euros(prix_moyen_pizza, 2).replace('.', ',')}.",
            "action": "Proposer une 2e pizza à prix réduit, un menu pizza + boisson + dessert, et une suggestion "
                      f"au moment de la commande. Si 10 % de ces clients ajoutaient une pizza : environ "
                      f"{format_euros(gain_2e_pizza)} de CA supplémentaire sur la période (estimation à tester).",
            "suivi": "Part des commandes d'une pizza et panier moyen (onglet Comportement d'achat).",
        },
        {
            "titre": "Animer les jours les plus calmes",
            "priorite": ":orange-badge[Priorité moyenne]",
            "constat": f"Un {j_fort['jour'].lower()} rapporte en moyenne {format_euros(j_fort['ca_moyen_par_jour'])}, "
                       f"un {j_faible['jour'].lower()} seulement {format_euros(j_faible['ca_moyen_par_jour'])} "
                       f"(écart de {format_euros(j_fort['ca_moyen_par_jour'] - j_faible['ca_moyen_par_jour'])} par jour).",
            "action": f"Créer une offre ciblée le {j_faible['jour'].lower()} (formule famille, happy hour), "
                      "et vérifier que l'équipe est dimensionnée au plus juste ce jour-là.",
            "suivi": "CA moyen par jour de la semaine (onglet Rythme).",
        },
        {
            "titre": "Revoir les recettes les moins vendues",
            "priorite": ":orange-badge[Priorité moyenne]",
            "constat": f"Les 5 recettes les plus faibles ne pèsent que {part_flop5:.1f} % du CA. "
                       f"La dernière, {derniere['pizza']}, rapporte {format_euros(derniere['chiffre_affaires'])}.",
            "action": "Pour chacune : la retravailler (prix, recette, photo, place sur le menu) ou la retirer pour "
                      "simplifier la carte et réduire les achats d'ingrédients spécifiques. Décision à valider avec les marges.",
            "suivi": "Top 5 / Flop 5 des recettes (onglet Carte).",
        },
        {
            "titre": "Simplifier les grandes tailles",
            "priorite": ":blue-badge[À étudier]",
            "constat": f"La taille L fait {part_taille('L'):.1f} % du CA. XL et XXL n'existent que pour la Greek "
                       f"et ne pèsent que {part_taille('XL') + part_taille('XXL'):.1f} % du CA.",
            "action": "Mettre la taille L en avant sur le menu. Supprimer la XXL, ou la garder comme produit d'appel "
                      "pour les groupes si elle a une vraie raison d'être.",
            "suivi": "Part du CA par taille (onglet Carte) et filtre Greek XL / XXL.",
        },
        {
            "titre": "Mettre en avant les créneaux à fort panier",
            "priorite": ":blue-badge[À étudier]",
            "constat": f"Le panier moyen le plus élevé se fait au créneau {panier_max['creneau']} "
                       f"({format_euros(panier_max['panier_moyen'], 2).replace('.', ',')}) : "
                       "ce sont souvent des commandes de groupe.",
            "action": "Développer une offre « bureaux et groupes » sur ce créneau (commande à l'avance, livraison groupée).",
            "suivi": "Panier moyen par créneau horaire (onglet Comportement d'achat).",
        },
    ]

    # Affichage en grille de 2 colonnes : une carte par recommandation
    for i in range(0, len(RECOMMANDATIONS), 2):
        colonnes = st.columns(2)
        for j, (colonne, reco) in enumerate(zip(colonnes, RECOMMANDATIONS[i:i + 2])):
            with colonne:
                with st.container(border=True):
                    st.markdown(f"**{i + j + 1}. {reco['titre']}** {reco['priorite']}")
                    st.markdown(f"📊 **Constat :** {reco['constat']}")
                    st.markdown(f"✅ **Action :** {reco['action']}")
                    st.markdown(f"📈 **À suivre :** {reco['suivi']}")

    # --- Les limites : ce que les données ne permettent pas de dire
    st.subheader("Limites de l'analyse")
    st.caption("Ces limites ne remettent pas en cause les constats, mais elles disent jusqu'où on peut les pousser.")

    LIMITES = [
        ("📅 Une seule année de données",
         "Les ventes couvrent 2015 uniquement : impossible de comparer à l'année précédente ou de confirmer "
         "une saisonnalité. Un mois fort peut être un hasard de calendrier."),
        ("💶 Du chiffre d'affaires, pas de la marge",
         "La base ne contient ni coût des ingrédients ni coût du personnel. Une recette qui rapporte peu "
         "peut être très rentable, et inversement : retirer une pizza doit se décider avec les marges."),
        ("👤 Pas de données clients",
         "Il n'y a pas d'identifiant client : on ne peut mesurer ni la fidélité, ni la fréquence de visite, "
         "ni le profil des clients. Une commande n'est pas un client."),
        ("🛵 Pas de canal ni de contexte",
         "On ne sait pas si la commande est sur place, à emporter ou livrée, ni s'il y avait une promotion, "
         "un événement ou une météo particulière. Les jours exceptionnels restent donc à expliquer."),
        ("🏷️ Des prix supposés fixes",
         "Chaque pizza a un seul prix dans pizzas.csv, appliqué à toute l'année. Si les prix ont changé "
         "en cours d'année, le chiffre d'affaires calculé est approximatif."),
        (f"🚪 {jours_calendrier - jours_ouverts} jour(s) sans aucune commande sur la période",
         f"La pizzeria a enregistré des commandes {jours_ouverts} jours sur {jours_calendrier}. On ne sait pas si "
         "les autres jours sont des fermetures ou des données manquantes : les moyennes « par jour » ne comptent "
         "que les jours ouverts."),
        ("🔎 Le sens des filtres",
         "Avec un filtre catégorie ou taille, une « commande » est une commande contenant au moins une pizza "
         "de ce périmètre, et le CA ne compte que ces pizzas. Le panier moyen filtré n'est donc pas le panier "
         "complet du client. Certains graphiques ignorent volontairement un filtre, c'est indiqué sous chacun."),
        ("🧪 Des gains estimés, pas garantis",
         "Les montants de gain (comme l'offre « 2e pizza ») reposent sur des hypothèses simples. "
         "Ils servent à comparer les pistes ; seul un test sur quelques semaines confirmera l'effet réel."),
    ]

    gauche, droite = st.columns(2)
    for k, (titre, texte) in enumerate(LIMITES):
        with (gauche if k % 2 == 0 else droite):
            with st.expander(titre):
                st.write(texte)

    # --- Prochaines étapes
    st.subheader("Prochaines étapes")
    st.markdown(
        "1. **Tester** l'offre « 2e pizza » et la formule du jour le plus calme pendant 4 à 6 semaines, puis comparer "
        "les indicateurs avant / après dans cette application.\n"
        "2. **Collecter** les coûts matière par recette pour passer du chiffre d'affaires à la marge.\n"
        "3. **Ajouter** le canal de vente (sur place, emporter, livraison) et un identifiant client anonyme.\n"
        "4. **Charger** les années suivantes dans la base pour suivre l'évolution d'une année sur l'autre."
    )
