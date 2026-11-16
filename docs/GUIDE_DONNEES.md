# Guide des données & choix de modélisation

## Les 4 fichiers BAAC

| BAAC | Granularité d'origine | Exemples de champs utilisés | Cible |
|---|---|---|---|
| Caract | Accident | Num_Acc, jour, mois, hrmn, dep, lat, long, atm, lum, agg | accidents |
| Lieux | Accident | Num_Acc, catr, vma | accidents |
| Véhicules | Véhicule | Num_Acc | nb_vehicules par accident |
| Usagers | Usager impliqué | Num_Acc, grav, sexe, catu, an_nais | usagers et agrégats par accident |

Le pipeline conserve **une ligne par accident**. Il ne réalise **jamais** une jointure véhicule × usager au niveau individuel.

## Jointures & unicité

- Clé interne de suivi : `annee` + `num_acc`.
- Caractéristiques et lieux : dédoublonnage par identifiant accident après journalisation.
- Véhicules : agrégation `COUNT(*)` avant jointure.
- Usagers : agrégation des catégories de gravité avant jointure.
- Un accident ayant 3 véhicules et 5 usagers reste donc **un accident**, et pas 15 lignes.

## Gravité (codes BAAC)

- 1 : indemne ; 2 : tué ; 3 : blessé hospitalisé ; 4 : blessé léger.
- « Accident mortel » = accident avec au moins un usager codé 2.
- « Personnes tuées » = nombre d'usagers codés 2 ; les valeurs diffèrent souvent.

## Dimensions

- La latitude et longitude sont converties depuis des décimales éventuellement françaises.
- La catégorie météo est l'observation codée dans le BAAC, pas une explication causale de l'accident.
- `vma` est la **vitesse maximale autorisée**, pas la vitesse de circulation du véhicule.
- Les noms des communes ne sont pas reconstitués arbitrairement ; les codes sont conservés tels qu'enregistrés.
- Les DROM et COM restent inclus dans le jeu de données, même si la carte centrée sur la métropole n'y affiche pas de points.

## Provenance et reproductibilité

L'étape `scripts/download_data.py` récupère les ressources de l'API officielle, enregistre l'URL et le SHA256 de chaque CSV dans `data/raw/sources_manifest.json`. Ce fichier reste local car les données peuvent être réactualisées.

Dataset officiel : https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2025

Documentation : https://www.onisr.securite-routiere.gouv.fr/outils-statistiques/open-data
