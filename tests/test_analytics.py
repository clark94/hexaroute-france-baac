import pandas as pd
from src.analytics import snapshot, year_month_trend, day_hour_matrix


def small_frame():
    return pd.DataFrame({
        'annee': [2024,2024,2025], 'mois_num':[3,5,3],
        'departement':['69','75','69'], 'heure':[8,17,8],
        'jour_semaine':[0,2,0], 'accident_mortel':[True, False, False],
    })


def test_snapshot_from_real_rows_only():
    s = snapshot(small_frame())
    assert (s['n'],s['mortels'],s['departement'],s['heure']) == (3,1,'69',8)
    assert round(s['part_mortels'],2) == 33.33


def test_trend_shape_and_empty_months():
    t = year_month_trend(small_frame())
    assert len(t) == 24
    assert t[(t.annee == 2024) & (t.mois_num == 3)].accidents.iloc[0] == 1
    assert t[(t.annee == 2024) & (t.mois_num == 6)].accidents.iloc[0] == 0


def test_heatmap_matrix():
    m = day_hour_matrix(small_frame())
    assert m.shape == (7,24)
    assert m.loc['Lundi',8] == 2
    assert m.loc['Mercredi',17] == 1
