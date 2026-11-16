## Présentation du projet

**HexaRoute** est un tableau de bord interactif consacré à l’analyse des accidents corporels de la circulation en France. Il s’appuie sur les données ouvertes BAAC, disponibles sur data.gouv.fr. Chaque millésime comprend quatre fichiers : caractéristiques, lieux, véhicules et usagers.

### Préparation des données

Un même accident peut impliquer plusieurs véhicules et plusieurs usagers. Une jointure directe entre les fichiers peut donc multiplier les lignes et fausser les comptages. Pour calculer les indicateurs au niveau de l’accident, le pipeline agrège les données des véhicules et des usagers par identifiant d’accident avant la jointure. Le détail des usagers est conservé séparément pour permettre leur analyse.

Le pipeline Python télécharge et normalise les fichiers, conserve leurs empreintes SHA-256 et produit des tables Parquet. Les données préparées ont également été chargées dans Snowflake, où des vues SQL fournissent des indicateurs nationaux, mensuels et départementaux.

### Résultats et fonctionnalités

Pour le millésime **2025**, le jeu analysé contient **55 093 accidents corporels** et **126 376 enregistrements d’usagers**. Parmi ces accidents, **3 323 sont mortels**, soit **6,0 %**. Le nombre de personnes tuées s’élève à **3 515**.

L’application Streamlit permet d’explorer ces résultats par année, département, milieu et gravité. Elle présente les tendances mensuelles et horaires, une carte interactive, des analyses sur les usagers et des contrôles de qualité des données.

### Limites et perspectives

Les résultats décrivent les accidents corporels recensés. La carte peut afficher moins de points que le nombre total d’accidents sélectionnés, en raison de coordonnées manquantes ou d’un échantillonnage.

Les volumes observés ne mesurent pas le risque routier. Une évolution du projet consisterait à intégrer des données de trafic, comme les kilomètres parcourus, afin de calculer des taux comparables entre territoires.
