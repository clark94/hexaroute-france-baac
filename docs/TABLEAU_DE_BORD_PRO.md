# Tableau de bord PRO — HexaRoute

La nouvelle page **◈ Synthèse** propose une lecture de direction avec les principaux indicateurs, en complément des onglets d'analyse détaillée.

## Les modules visuels

1. **5 KPI principaux** : accidents corporels, accidents mortels, personnes tuées, blessés hospitalisés au sens BAAC, véhicules impliqués.
2. **3 signaux descriptifs** : département avec le plus grand nombre d'accidents enregistrés, heure la plus fréquente, proportion d'accidents mortels.
3. **Courbes de tendance comparées** : nombre d'accidents par mois et par année, sur le périmètre filtré.
4. **Répartition par gravité** : graphique en anneau pour le contexte de sélection.
5. **Carte thermique jours / heures** : matrice 7×24 d'accidents enregistrés.
6. **Top 8 des départements** : classement par volume brut.
7. **Autres onglets** : évolutions détaillées, carte des accidents, usagers, qualité des données, sources et exports.

## Filtres

Tous les graphiques et KPI suivent les filtres du menu latéral : années, département(s), type de milieu, gravité, intervalle mensuel.

## Validité des indicateurs

- Les données sont **téléchargées depuis data.gouv.fr** ; les fichiers sources ne sont pas fournis comme échantillons fictifs.
- Les classements géographiques représentent des **volumes de signalements**, **pas** une mesure de risque routier.
- Les mois sans accident enregistré dans une période sélectionnée sont dessinés à zéro ; vérifier la couverture des fichiers avant de conclure à un phénomène.
- Les taux de mortalité présentés portent sur les **accidents mortels enregistrés** et non sur la mortalité routière rapportée à la population.
- La carte ponctuelle échantillonne les accidents géolocalisés pour des raisons de performance.

## Lancer sur Windows

Depuis le dossier `HexaRoute_France_BAAC`, double-cliquez sur `INSTALLER_ET_LANCER.bat`.

Ou, dans PowerShell :

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

La première utilisation demande un téléchargement des CSV officiels. Cliquer sur **Charger 2023–2025** pour toutes les analyses interannuelles.

## Nouvelle expérience JavaScript

- Bandeau éditorial animé via Canvas JavaScript (`assets/hero.js`) avec animation désactivée en mode mouvement réduit.
- Carte Leaflet (`assets/map.js`) : regroupements, points, carte thermique, popup contextualisée, filtres de gravité, fond clair/sombre et recentrage.
- Interface cartographique pensée pour desktop et mobile (`assets/map.css`).
- HTML/JS embarqué dans Streamlit avec `st.iframe` (versions récentes) et repli compatible `components.v1.html` (versions antérieures).
- Les filtres globaux sont appliqués par Python avant le transfert de points au JavaScript ; le filtre gravité intégré au JS s'applique seulement à l'échantillon de la carte.
- Ne pas confondre les points affichés et le volume total d'accidents enregistré. Les cartes affichent uniquement la France métropolitaine.
- Bibliothèques Leaflet et fonds CARTO chargés via CDN : une connexion Internet est requise pour la carte JS.
