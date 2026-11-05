-- =====================================================================
-- Plato's Pizza : création du modèle en étoile (SQLite)
-- Prérequis : les 4 CSV importés tels quels dans les tables
--   orders, order_details, pizzas, pizza_types
--   (import DBeaver, encodage windows-1252 pour pizza_types.csv)
-- Exécution dans DBeaver : Alt+X (tout le script)
-- =====================================================================

-- 0. Activer la vérification des clés étrangères (désactivée par défaut en SQLite)
PRAGMA foreign_keys = ON;

-- 1. Supprimer les tables du modèle si elles existent, pour pouvoir rejouer le script.
--    La table de faits d'abord, car elle dépend des deux dimensions.
DROP TABLE IF EXISTS faits_ventes;
DROP TABLE IF EXISTS dim_pizza;
DROP TABLE IF EXISTS dim_commande;

-- 2. Dimension produit : une ligne par pizza vendable (recette x taille)
CREATE TABLE dim_pizza (
    pizza_id      VARCHAR NOT NULL PRIMARY KEY,
    pizza_type_id VARCHAR NOT NULL,
    name          VARCHAR NOT NULL,
    category      VARCHAR NOT NULL,
    ingredients   VARCHAR NOT NULL,
    size          VARCHAR NOT NULL,
    price         REAL    NOT NULL
);

-- 3. Dimension commande : une ligne par commande, avec son moment
CREATE TABLE dim_commande (
    order_id   INTEGER PRIMARY KEY,
    order_date NVARCHAR NOT NULL,   -- format AAAA-MM-JJ
    order_time NVARCHAR NOT NULL    -- format HH:MM:SS
);

-- 4. Table de faits : une ligne par pizza vendue dans une commande
CREATE TABLE faits_ventes (
    order_details_id INTEGER PRIMARY KEY,
    order_id         INTEGER NOT NULL,
    pizza_id         VARCHAR NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (order_id) REFERENCES dim_commande (order_id),
    FOREIGN KEY (pizza_id) REFERENCES dim_pizza (pizza_id)
);

-- 5. Remplir dim_pizza : jointure du menu (pizzas) et des recettes (pizza_types)
INSERT INTO dim_pizza (pizza_id, pizza_type_id, name, category, ingredients, size, price)
SELECT p.pizza_id, p.pizza_type_id, pt.name, pt.category, pt.ingredients, p.size, p.price
FROM pizzas p
JOIN pizza_types pt ON p.pizza_type_id = pt.pizza_type_id;

-- 6. Remplir dim_commande : une seule table source, donc pas de jointure
INSERT INTO dim_commande (order_id, order_date, order_time)
SELECT o.order_id, o.date, o.time
FROM orders o;

-- 7. Remplir faits_ventes : une seule table source, donc pas de jointure
INSERT INTO faits_ventes (order_details_id, order_id, pizza_id, quantity)
SELECT od.order_details_id, od.order_id, od.pizza_id, od.quantity
FROM order_details od;

-- 8. Contrôles (attendus : 96 / 21 350 / 48 620 / 48 620)
SELECT 'dim_pizza' AS table_name, COUNT(*) AS nb_lignes FROM dim_pizza
UNION ALL
SELECT 'dim_commande', COUNT(*) FROM dim_commande
UNION ALL
SELECT 'faits_ventes', COUNT(*) FROM faits_ventes
UNION ALL
SELECT 'jointure complète', COUNT(*)
FROM faits_ventes fv
JOIN dim_pizza dp    ON dp.pizza_id = fv.pizza_id
JOIN dim_commande dc ON dc.order_id = fv.order_id;
