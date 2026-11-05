# 🍕 Plato's Pizza : pilotage de l'activité 2015

Application d'aide à la décision pour la direction de Plato's Pizza. Elle s'appuie sur une base SQL relationnelle construite à partir de l'historique des commandes de l'année 2015.

L'objectif est de comprendre l'activité (ventes, affluence, carte, comportement d'achat) et de proposer des recommandations chiffrées.

**Outils :** SQL (SQLite, DBeaver), Python (pandas, Plotly) et Streamlit.

🌐 **Application en ligne :** *(ajoute ici l'adresse Streamlit Cloud après le déploiement)*

📦 **Déploiement :** voir [DEPLOIEMENT.md](DEPLOIEMENT.md).

---

## 1. Contenu du projet

```
plato_pizza/
├── data/                              Les 4 fichiers CSV d'origine
│   ├── orders.csv
│   ├── order_details.csv
│   ├── pizzas.csv
│   └── pizza_types.csv
├── creation_base.sql                  Création du modèle en étoile (tables, clés, contrôles)
├── preparer_base.py                   Construit plato_pizza.db à partir des CSV en une commande
├── analyse.sql                        Les requêtes d'analyse métier (Q1 à Q12)
├── Pizza_exploration_analyse.ipynb    Exploration, contrôle qualité et visualisation en Python
├── app.py                             L'application Streamlit
├── assets/illustrations/              Images des bandeaux de l'application
├── .streamlit/config.toml             Thème de l'application
├── requirements.txt                   Bibliothèques Python nécessaires
├── DEPLOIEMENT.md                     Mise en ligne sur GitHub et Streamlit Cloud
└── README.md
```

La base `plato_pizza.db` n'est pas versionnée. Elle se reconstruit à partir des CSV, soit avec `preparer_base.py`, soit automatiquement au premier lancement de l'application.

---

## 2. Installation

Il faut **Python 3.10 ou plus récent**. Ouvre un terminal dans le dossier du projet, puis installe les dépendances :

```bash
python -m pip install -r requirements.txt
```

> 💡 Sous Windows, si `pip` ou `streamlit` sont bloqués par la sécurité du poste, passe toujours par `python -m ...` comme ci-dessus.

---

## 3. Préparer la base de données

### Option A : en une commande (recommandé)

```bash
python preparer_base.py
```

Le script :
1. charge les 4 CSV dans des tables brutes (zone de « staging ») ;
2. exécute `creation_base.sql` pour construire le modèle en étoile ;
3. vérifie les volumes.

Résultat attendu :

```
dim_pizza            96 lignes  OK
dim_commande     21 350 lignes  OK
faits_ventes     48 620 lignes  OK
```

### Option B : dans DBeaver

1. Crée une connexion SQLite vers un nouveau fichier `plato_pizza.db`.
2. Importe les 4 CSV : clic droit sur la base, puis *Importer des données*. Garde les noms de tables `orders`, `order_details`, `pizzas` et `pizza_types`.
3. Ouvre `creation_base.sql` et exécute le script complet avec Alt+X.

---

## 4. Lancer l'application

```bash
python -m streamlit run app.py
```

L'application s'ouvre dans le navigateur, à l'adresse http://localhost:8501. Si la base n'existe pas encore, l'application la crée elle-même au premier lancement.

---

## 5. Le modèle de données

On utilise un **schéma en étoile** : une table de faits au centre, entourée de deux dimensions.

| Table | Rôle | Clé | Lignes |
|---|---|---|---|
| `faits_ventes` | Une ligne = une pizza (référence + taille) dans une commande, avec sa quantité | `order_details_id` | 48 620 |
| `dim_pizza` | Le produit : nom, catégorie, ingrédients, taille, prix | `pizza_id` | 96 |
| `dim_commande` | Le moment : date et heure de la commande | `order_id` | 21 350 |

**Pourquoi ce modèle ?**
- `pizzas` et `pizza_types` décrivent le même produit : on les fusionne dans une seule dimension `dim_pizza`. Une requête n'a ainsi qu'une jointure à faire pour obtenir le produit.
- Le **grain** de la table de faits est la ligne de commande. Le chiffre d'affaires se calcule toujours de la même façon : `SUM(quantity * price)`.
- Les **clés étrangères** et la contrainte `CHECK (quantity > 0)` garantissent la cohérence des données chargées.
- Le prix est stocké dans `dim_pizza`, car le fichier source ne donne qu'un prix par pizza pour toute l'année : on fait l'hypothèse de prix fixes (voir *Limites*).

---

## 6. L'analyse

`analyse.sql` contient une requête par question métier. Toutes acceptent les mêmes paramètres, alimentés par les filtres de l'application : `:date_debut`, `:date_fin`, `:categorie` et `:taille`.

| Requête | Question métier |
|---|---|
| Q1 | Indicateurs clés : CA, commandes, pizzas, panier moyen, pizzas par commande |
| Q2 | Évolution mensuelle du CA |
| Q3, Q4, Q11 | Affluence par heure, par jour de la semaine, et croisement jour × heure |
| Q5a, Q5b | Les 10 meilleurs et les 10 plus faibles jours |
| Q6 | Classement des recettes (fonction fenêtre `RANK()`) |
| Q7, Q8 | Poids des catégories et des tailles (part du CA avec `SUM() OVER ()`) |
| Q9 | Ingrédients les plus utilisés (CTE récursive qui découpe la liste d'ingrédients) |
| Q10, Q12 | Taille des commandes et panier moyen par créneau horaire |

Le notebook `Pizza_exploration_analyse.ipynb` complète le SQL côté Python. Il contient le contrôle qualité des CSV (valeurs manquantes, doublons, types), les visualisations, et une vérification croisée des résultats SQL avec pandas.

---

## 7. L'application Streamlit

**Filtres** (barre latérale) : période, catégorie (avec une couleur par catégorie), taille, et un accès dédié à la Greek pour les tailles XL et XXL. XL et XXL n'existent que pour cette recette.

| Onglet | Ce qu'on y trouve |
|---|---|
| 📈 Vue d'ensemble | CA mensuel, 10 meilleurs et 10 plus faibles jours |
| ⏰ Rythme de l'activité | Commandes par heure, CA par jour de la semaine, carte de chaleur jour × heure |
| 🍕 Performance de la carte | Top 5 et Flop 5 des recettes, poids des catégories et des tailles, ingrédients |
| 🧺 Comportement d'achat | Pizzas par commande, panier moyen et volume par créneau horaire |
| 🎯 Recommandations | 6 recommandations chiffrées, limites de l'analyse, prochaines étapes |

Chaque onglet commence par un bandeau avec la question métier et 3 chiffres clés. Chaque graphique est suivi d'une conclusion (💡) recalculée selon les filtres.

**Choix techniques :**
- `@st.cache_resource` pour la connexion à la base, ouverte une seule fois ;
- `@st.cache_data` pour les résultats de requêtes, qui ne sont pas recalculés si les filtres n'ont pas changé ;
- requêtes **paramétrées** (`:categorie`, `:taille`…), jamais de texte concaténé dans le SQL ;
- un garde-fou affiche un message clair quand une combinaison de filtres ne renvoie aucune vente.

---

## 8. Principaux enseignements (année 2015)

- **817 860 €** de chiffre d'affaires, **21 350 commandes** et **49 574 pizzas** ; panier moyen de **38,31 €**, soit **2,32 pizzas** par commande.
- Un CA **stable** d'un mois sur l'autre, entre 64 k€ et 73 k€.
- Deux **coups de feu** : 12 h à 13 h, puis 17 h à 19 h. Le **vendredi** est le jour le plus fort, le **dimanche** le plus calme.
- Les 4 catégories pèsent chacune environ un quart du CA. La **taille L** représente 46 % du CA, alors que XL et XXL (la Greek) restent marginales.
- **38 % des commandes ne contiennent qu'une pizza.**
- Thai Chicken est la recette qui rapporte le plus, Brie Carre celle qui rapporte le moins.

## 9. Recommandations

1. **Caler les plannings** sur les heures de pointe et alléger les heures creuses.
2. **Faire grossir le panier** des commandes d'une seule pizza : 2e pizza à prix réduit, menu, suggestion au moment de la commande.
3. **Animer le jour le plus calme** (le dimanche) avec une offre ciblée.
4. **Retravailler ou retirer** les recettes du Flop 5, qui pèsent moins de 9 % du CA. La décision est à valider avec les marges.
5. **Simplifier les grandes tailles** : mettre la L en avant, s'interroger sur la XXL.
6. **Développer une offre groupes** sur le créneau où le panier est le plus élevé (le déjeuner).

## 10. Limites

- **Une seule année** de données : pas de comparaison avec l'année précédente, ni de saisonnalité confirmée.
- **Pas de coûts** : on analyse le chiffre d'affaires, pas la marge.
- **Pas d'identifiant client** : la fidélité et la fréquence ne sont pas mesurables.
- **Pas de contexte** : on ne connaît ni le canal (sur place, à emporter, livraison), ni les promotions, ni la météo.
- **Prix supposés fixes** sur toute l'année.
- **7 jours sans commande** sur 365 : fermetures ou données manquantes ?
- Avec un filtre catégorie ou taille, une « commande » est une commande contenant au moins une pizza du périmètre : le panier moyen filtré n'est donc pas le panier complet du client.
- Les gains chiffrés sont des **estimations** à confirmer par un test.

---

*Projet réalisé dans le cadre de la formation Data Analyst.*
