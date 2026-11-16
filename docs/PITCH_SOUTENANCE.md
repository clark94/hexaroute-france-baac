# Pitch de démonstration – HexaRoute

**Problème** : comment explorer à grande échelle les accidents corporels routiers français tout en évitant les erreurs de comptage liées aux jointures de données ?

**Source** : bases annuelles BAAC du ministère de l'Intérieur, via data.gouv.fr, quatre fichiers par année.

**Architecture** : téléchargement API et SHA256 → contrôle qualité et normalisation → agrégation des véhicules/usagers avant jointure → stockage analytique Parquet → SQL DuckDB / Snowflake → visualisation Streamlit.

**Démo (5 minutes)** :

1. Montrer filtres annuels et départementaux ; expliquer le périmètre des accidents corporels.
2. Faire varier les années et observer les tendances mensuelles et les heures.
3. Ouvrir la carte et expliquer la différence entre points affichés et total enregistré.
4. Montrer les usagers et la lecture prudente de la gravité.
5. Afficher le tableau qualité, les doublons de clés, les limites et la traçabilité.

**Limites** : comptages ≠ risque routier ; absence de mesure d'exposition au trafic ; catégories de gravité administratives ; coordonnées manquantes possibles.

**Perspectives** : rattachement à des données de trafic pour des taux comparables ; suivi de qualité automatisé ; stockage d'exécution en Snowflake ; déploiement permanent.
