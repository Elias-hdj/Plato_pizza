# Guide de déploiement : GitHub + Streamlit Community Cloud

Ce guide sert à publier le projet sur GitHub, puis à mettre l'application en ligne gratuitement sur **Streamlit Community Cloud**. On obtient ainsi une adresse publique du type `https://plato-pizza.streamlit.app`.

---

## Partie 1 : mettre le projet sur GitHub

### 1.1 Créer le dépôt

1. Connecte-toi sur [github.com](https://github.com). Clique sur **+** (en haut à droite), puis sur **New repository**.
2. Remplis le formulaire :
   - **Repository name :** `plato-pizza`
   - **Description :** *Analyse des ventes d'une pizzeria : SQL, Python et Streamlit*
   - Choisis **Public**. Streamlit Community Cloud déploie gratuitement les dépôts publics.
   - Ne coche **pas** *Add a README* : le projet a déjà le sien.
3. Clique sur **Create repository**.

### 1.2 Envoyer les fichiers

Choisis **une** des deux méthodes.

**Méthode A : par le navigateur (sans rien installer)**

1. Sur la page du dépôt vide, clique sur le lien **uploading an existing file**.
2. Dézippe `plato-pizza.zip` sur ton PC, ouvre le dossier `plato-pizza`, sélectionne **tout son contenu** et glisse-le dans la page.
3. Vérifie que les dossiers `data`, `assets` et `.streamlit` apparaissent dans la liste.
4. En bas, dans *Commit changes*, écris « Version finale du projet Plato's Pizza », puis clique sur **Commit changes**.

> Le fichier `.gitignore` commence par un point, et Windows peut le masquer. Il n'est pas indispensable : si tu ne le vois pas, ce n'est pas grave.

**Méthode B : en ligne de commande avec Git**

Dans un terminal ouvert dans le dossier `plato-pizza` :

```bash
git init
git add .
git commit -m "Version finale du projet Plato's Pizza"
git branch -M main
git remote add origin https://github.com/TON-PSEUDO/plato-pizza.git
git push -u origin main
```

Remplace `TON-PSEUDO` par ton nom d'utilisateur GitHub.

### 1.3 Ce que le dépôt doit contenir

```
plato-pizza/
├── .streamlit/config.toml     Thème de l'application
├── assets/illustrations/      Les 5 images des bandeaux
├── data/                      Les 4 CSV
├── app.py                     L'application Streamlit
├── analyse.sql                Les requêtes d'analyse
├── creation_base.sql          Le modèle en étoile
├── preparer_base.py           Construction de la base à partir des CSV
├── Pizza_exploration_analyse.ipynb
├── requirements.txt
├── README.md
├── DEPLOIEMENT.md
└── .gitignore
```

La base `plato_pizza.db` **n'est pas** dans le dépôt, et c'est voulu. L'application la reconstruit toute seule à partir des CSV au premier lancement. C'est la preuve que ta base est **reproductible**.

---

## Partie 2 : déployer sur Streamlit Community Cloud

1. Va sur [share.streamlit.io](https://share.streamlit.io) et clique sur **Continue with GitHub**. Autorise Streamlit à lire tes dépôts.
2. Clique sur **Create app**, puis sur **Deploy a public app from GitHub**.
3. Remplis le formulaire :
   - **Repository :** `TON-PSEUDO/plato-pizza`
   - **Branch :** `main`
   - **Main file path :** `app.py`
   - **App URL :** choisis un nom court, par exemple `plato-pizza`.
4. Ouvre **Advanced settings** et choisis **Python 3.12**.
5. Clique sur **Deploy**.

Le premier déploiement prend 2 à 4 minutes, le temps d'installer les bibliothèques de `requirements.txt`. Au premier affichage, le message « Création de la base de données… » apparaît quelques secondes, puis le tableau de bord s'affiche.

### Mettre à jour l'application

Chaque modification envoyée sur GitHub (nouveau commit sur `main`) est **redéployée automatiquement** en une minute environ.

### Si quelque chose ne marche pas

| Symptôme | Cause probable | Solution |
|---|---|---|
| `ModuleNotFoundError: plotly` | `requirements.txt` absent ou mal nommé | Vérifie qu'il est à la racine du dépôt, avec ce nom exact. |
| `FileNotFoundError: data/orders.csv` | Les CSV ne sont pas dans `data/` | Ils doivent être dans `data/`, avec ces noms exacts en minuscules. |
| Les images des bandeaux n'apparaissent pas | Dossier mal placé | Le chemin doit être `assets/illustrations/onglet_vue.png`, etc. |
| L'application « s'endort » | Normal sur l'offre gratuite après quelques jours sans visite | Clique sur **Yes, get this app back up!**, puis attends 30 secondes. |
| Pas de son à la découpe | Les navigateurs bloquent le son tant qu'on n'a pas cliqué sur la page | Clique une fois n'importe où, puis bouge le curseur. |

En cas d'erreur, le détail se trouve dans **Manage app**, en bas à droite de l'application déployée : ce sont les journaux du serveur.

---

## Partie 3 : finaliser

1. Copie l'adresse de ton application, par exemple `https://plato-pizza.streamlit.app`.
2. Sur GitHub, ajoute-la au README à l'endroit prévu (ligne « Application en ligne »).
3. Ajoute-la aussi dans la section **About** du dépôt : clique sur la roue dentée à droite du dépôt, puis remplis le champ **Website**.
4. Pour la soutenance, ouvre l'application en ligne **avant** de passer, pour qu'elle soit déjà réveillée.
