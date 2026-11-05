-- =====================================================================
-- Plato's Pizza : requêtes d'analyse (SQLite) sur le modèle en étoile
-- Une requête par question du cadrage (Q1 à Q10).
--
-- Paramètres communs, alimentés par les filtres Streamlit :
--   :date_debut  date de début incluse, format 'AAAA-MM-JJ'  (ex. '2015-01-01')
--   :date_fin    date de fin incluse,   format 'AAAA-MM-JJ'  (ex. '2015-12-31')
--   :categorie   'Classic', 'Chicken', 'Supreme', 'Veggie', ou NULL = toutes
--   :taille      'S', 'M', 'L', 'XL', 'XXL', ou NULL = toutes
--
-- Dans DBeaver : à l'exécution, une fenêtre demande la valeur de chaque
-- paramètre. Saisis les dates entre apostrophes, et NULL pour "toutes".
--
-- Définitions communes :
--   CA            = SUM(quantity * price)
--   commandes     = COUNT(DISTINCT order_id)   (et non COUNT(*))
--   pizzas        = SUM(quantity)
-- Avec un filtre catégorie ou taille, "commandes" = commandes contenant
-- au moins une pizza de ce périmètre.
-- =====================================================================


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


-- CONTRÔLES DE COHÉRENCE ---------------------------------------------
-- La somme des CA par catégorie (Q7) et par taille (Q8) doit égaler le CA de Q1.
SELECT
    (SELECT ROUND(SUM(fv.quantity * dp.price), 2)
       FROM faits_ventes fv JOIN dim_pizza dp ON dp.pizza_id = fv.pizza_id)  AS ca_total,
    (SELECT ROUND(SUM(ca), 2) FROM (
        SELECT SUM(fv.quantity * dp.price) AS ca
        FROM faits_ventes fv JOIN dim_pizza dp ON dp.pizza_id = fv.pizza_id
        GROUP BY dp.category))                                               AS somme_ca_categories,
    (SELECT ROUND(SUM(ca), 2) FROM (
        SELECT SUM(fv.quantity * dp.price) AS ca
        FROM faits_ventes fv JOIN dim_pizza dp ON dp.pizza_id = fv.pizza_id
        GROUP BY dp.size))                                                   AS somme_ca_tailles;
