# ---------------------------------------------------------------------
# Plato's Pizza : création de la base SQLite plato_pizza.db à partir des 4 CSV
#
# Étapes :
#   1. Les 4 CSV du dossier data/ sont chargés tels quels dans des tables "brutes"
#      (orders, order_details, pizzas, pizza_types) : c'est la zone de staging.
#   2. Le script creation_base.sql construit le modèle en étoile à partir de ces tables :
#      dim_pizza, dim_commande et faits_ventes, avec clés primaires, clés étrangères et contrôles.
#   3. Des comptages vérifient que rien n'a été perdu ou dupliqué en route.
#
# Lancement (depuis le dossier du projet) :  python preparer_base.py
# Même résultat que l'import des CSV dans DBeaver suivi de l'exécution de creation_base.sql.
# L'application appelle aussi creer_base() toute seule si la base est absente
# (par exemple au premier lancement sur Streamlit Community Cloud).
# ---------------------------------------------------------------------
import sqlite3
from pathlib import Path

import pandas as pd

DOSSIER = Path(__file__).parent
DOSSIER_CSV = DOSSIER / "data"
BASE = DOSSIER / "plato_pizza.db"

# pizza_types.csv contient des caractères accentués encodés en latin-1 (ex. "’Nduja")
ENCODAGES = {"pizza_types": "latin-1"}

# Nombre de lignes attendu dans chaque table du modèle en étoile
ATTENDU = {"dim_pizza": 96, "dim_commande": 21350, "faits_ventes": 48620}


def creer_base(afficher=True):
    connexion = sqlite3.connect(BASE)

    # 1. Staging : une table par CSV, remplacée si elle existe déjà
    for table in ["orders", "order_details", "pizzas", "pizza_types"]:
        df = pd.read_csv(DOSSIER_CSV / f"{table}.csv", encoding=ENCODAGES.get(table, "utf-8"))
        df.to_sql(table, connexion, index=False, if_exists="replace")
        if afficher:
            print(f"{table:<15} {len(df):>7,} lignes importées".replace(",", " "))

    # 2. Modèle en étoile
    connexion.executescript((DOSSIER / "creation_base.sql").read_text(encoding="utf-8"))

    # 3. Contrôles : chaque table doit avoir le nombre de lignes attendu
    for table, nb_attendu in ATTENDU.items():
        nb = connexion.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        statut = "OK" if nb == nb_attendu else f"ATTENTION : {nb_attendu} attendues"
        if afficher:
            print(f"{table:<15} {nb:>7,} lignes  {statut}".replace(",", " "))

    connexion.close()
    if afficher:
        print(f"Base prête : {BASE}")


if __name__ == "__main__":
    creer_base()
