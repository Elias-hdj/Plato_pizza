# Finaliser le projet Plato's Pizza : la marche à suivre

Ton dossier de projet : `C:\Users\Utilisateur\Documents\Data_Analyst_Formation\02_Projets\Nouveau dossier`

---

## Étape 1 : tout fermer

- **Streamlit :** dans le terminal où il tourne, appuie sur `Ctrl + C`.
- **DBeaver :** ferme-le complètement. Sinon, la base `plato_pizza.db` reste verrouillée et ne pourra pas être recréée.

## Étape 2 : organiser le dossier

Dans ton dossier de projet :

1. Crée un dossier `data` et **déplace-y les 4 CSV** : `orders.csv`, `order_details.csv`, `pizzas.csv` et `pizza_types.csv`.
2. Crée un dossier `assets`, puis à l'intérieur un dossier `illustrations`.

## Étape 3 : récupérer les fichiers finaux

Télécharge depuis le fil de discussion (ou la bibliothèque du projet) et place chaque fichier ainsi :

| Fichier | Où le mettre |
|---|---|
| `app.py` | dossier du projet (**remplace** l'ancien) |
| `README.md` | dossier du projet |
| `requirements.txt` | dossier du projet |
| `preparer_base.py` | dossier du projet |
| `creation_base.sql` | dossier du projet (remplace l'ancien) |
| `analyse.sql` | dossier du projet (remplace l'ancien) |
| `Pizza_exploration_analyse.ipynb` | dossier du projet (remplace l'ancien) |
| `onglet_vue.png`, `onglet_rythme.png`, `onglet_carte.png`, `onglet_comportement.png`, `onglet_reco.png` | `assets\illustrations\` |

Si tu as un son `coupe_pizza.mp3`, il va dans `assets\`. Ce son est facultatif : sans lui, l'app fabrique un son de découpe.

Ton dossier doit ressembler à ceci :

```
Nouveau dossier\
├── data\                 (les 4 CSV)
├── assets\
│   └── illustrations\    (les 5 images)
├── app.py
├── analyse.sql
├── creation_base.sql
├── preparer_base.py
├── Pizza_exploration_analyse.ipynb
├── README.md
└── requirements.txt
```

## Étape 4 : ouvrir un terminal dans le dossier

Dans l'Explorateur Windows, ouvre ton dossier de projet. Clique dans la **barre d'adresse**, tape `cmd` puis appuie sur Entrée : un terminal s'ouvre directement au bon endroit.

> Si `python` n'est pas reconnu, utilise plutôt **Anaconda Prompt**, puis tape :
> `cd "C:\Users\Utilisateur\Documents\Data_Analyst_Formation\02_Projets\Nouveau dossier"`

## Étape 5 : installer les bibliothèques

```
python -m pip install -r requirements.txt
```

## Étape 6 : recréer la base

```
python preparer_base.py
```

Tu dois voir ces 3 lignes à la fin :

```
dim_pizza            96 lignes  OK
dim_commande     21 350 lignes  OK
faits_ventes     48 620 lignes  OK
```

Cette étape prouve au jury que ta base est **reproductible** (c'est le livrable n°1).

## Étape 7 : lancer et tester l'application

```
python -m streamlit run app.py
```

Coche chaque point :

- [ ] Les 5 KPI s'affichent : 817 860 €, 21 350, 49 574, 38.31 €, 2.32.
- [ ] Les 5 onglets s'ouvrent, avec un bandeau, une image et des graphiques.
- [ ] Choisir **Veggie** : la page et les graphiques passent en vert.
- [ ] Bouger le curseur **Taille** : le couteau coupe la pizza et le son se joue.
- [ ] Cliquer **Greek XL** avec **Classic** : tout passe en turquoise.
- [ ] Cliquer **Greek XL** avec **Veggie** : un message « Aucune vente… » s'affiche, sans erreur rouge.
- [ ] Réduire la période à un seul mois : tout se met à jour.

## Étape 8 : vérifier le notebook

Ouvre `Pizza_exploration_analyse.ipynb` dans Jupyter ou VS Code. Clique sur **Redémarrer et tout exécuter** (Restart & Run All), puis vérifie qu'aucune cellule n'affiche d'erreur.

## Étape 9 : préparer le rendu

- Fais un **zip** du dossier : clic droit, *Envoyer vers*, *Dossier compressé*. Ou pousse-le sur GitHub si c'est demandé.
- Avant de zipper, supprime le dossier `__pycache__` s'il existe.

## Étape 10 : préparer la démonstration (5 minutes)

1. **Le contexte (30 s) :** la direction veut comprendre son activité 2015 et décider.
2. **La base (1 min) :** le modèle en étoile, avec 1 table de faits et 2 dimensions. Explique pourquoi `pizzas` et `pizza_types` ont été fusionnés dans `dim_pizza`.
3. **L'app (3 min) :**
   - les KPI ;
   - un filtre catégorie en direct ;
   - la heatmap (les plannings) ;
   - le Top et le Flop des recettes ;
   - les 38 % de commandes d'une seule pizza.
4. **Les recommandations et les limites (30 s) :** l'onglet 🎯.

### Les questions probables du jury

- *Pourquoi un schéma en étoile ?* Pour avoir une seule jointure par analyse et un grain clair (une ligne de commande). Le CA se calcule toujours avec `SUM(quantity * price)`.
- *Pourquoi `COUNT(DISTINCT order_id)` ?* Une commande a plusieurs lignes. `COUNT(*)` compterait les lignes, pas les commandes.
- *À quoi sert `@st.cache_data` ?* Streamlit relance tout le script à chaque clic. Le cache évite de réinterroger la base pour les mêmes filtres.
- *Pourquoi des requêtes paramétrées (`:categorie`) ?* Pour la sécurité (pas d'injection SQL) et pour réutiliser une seule requête quels que soient les filtres.
- *Quelle est la limite principale ?* Pas de coûts : on parle de chiffre d'affaires, pas de marge. Retirer une pizza doit se valider avec les marges.
