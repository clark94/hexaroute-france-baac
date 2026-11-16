"""Calculs analytiques pour HexaRoute. Aucun nombre n'est simulé."""
from __future__ import annotations

import pandas as pd

WEEKDAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']


def year_month_trend(accidents: pd.DataFrame) -> pd.DataFrame:
    """Nombre d'accidents par mois et par année, y compris les mois sans observation."""
    d = accidents.dropna(subset=['annee', 'mois_num'])
    if d.empty:
        return pd.DataFrame(columns=['annee', 'mois_num', 'accidents'])
    counts = d.groupby(['annee', 'mois_num'], observed=True).size().rename('accidents')
    years = sorted(d['annee'].astype(int).unique())
    grid = pd.MultiIndex.from_product([years, list(range(1,13))], names=['annee', 'mois_num'])
    return counts.reindex(grid, fill_value=0).reset_index()


def day_hour_matrix(accidents: pd.DataFrame) -> pd.DataFrame:
    """Matrice 7 × 24, zéro si aucune observation ; sans normaliser par le trafic."""
    d = accidents.dropna(subset=['jour_semaine', 'heure'])
    d = d[d['jour_semaine'].between(0,6) & d['heure'].between(0,23)]
    if d.empty:
        return pd.DataFrame(0, index=WEEKDAYS, columns=list(range(24)))
    mat = pd.crosstab(d['jour_semaine'].astype(int), d['heure'].astype(int))
    return mat.reindex(index=range(7), columns=range(24), fill_value=0).set_axis(WEEKDAYS)


def snapshot(accidents: pd.DataFrame) -> dict:
    """Signaux descriptifs, pas d'affirmation de causalité ni de comparaison de risque."""
    n = len(accidents)
    if not n:
        return {'n': 0, 'mortels': 0, 'part_mortels': 0., 'departement': None,
                'departement_nombre': 0, 'heure': None, 'heure_nombre': 0}
    deps = accidents['departement'].dropna().value_counts()
    hours = accidents['heure'].dropna().value_counts()
    morts = int(accidents['accident_mortel'].sum())
    return {'n': n, 'mortels': morts, 'part_mortels': 100*morts/n,
            'departement': str(deps.index[0]) if not deps.empty else None,
            'departement_nombre': int(deps.iloc[0]) if not deps.empty else 0,
            'heure': int(hours.index[0]) if not hours.empty else None,
            'heure_nombre': int(hours.iloc[0]) if not hours.empty else 0}
