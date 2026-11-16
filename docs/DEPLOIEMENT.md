# Déploiement & démonstration

## Pour une démonstration locale devant un recruteur

1. Préparer au préalable les données réelles de 2025 (ou 2023–2025).
2. Lancer `INSTALLER_ET_LANCER.bat` ou `streamlit run app.py` dans l'environnement `.venv`.
3. Présenter successivement : nationale → carte → usagers → qualité → traçabilité.
4. Expliquer la distinction **accident**, **véhicule**, **usager** et les risques de multiplication des lignes.

## Pour GitHub

Pousser uniquement le code, la documentation et les scripts. `.gitignore` exclut les gros CSV, Parquet et secrets.

## Streamlit Community Cloud

Le serveur cloud ne contient pas automatiquement les CSV officiels. Le dashboard propose un bouton de récupération des données à son premier lancement, mais les instances cloud peuvent redémarrer et leur disque peut être éphémère. Pour un service public permanent, utiliser un stockage externe persistant / entrepôt Snowflake et configurer des secrets côté hébergeur ; ne jamais écrire les identifiants dans le dépôt.

## Snowflake

Suivre le README. Les vues Snowflake sont facultatives et les coûts cloud doivent être surveillés. La variante locale est sans besoin de compte Snowflake.
