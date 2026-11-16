from pathlib import Path

from src.pipeline import create_year_frames


def test_pipeline_granularity_and_seriousness(tmp_path: Path):
    # Jeux synthétiques strictement utilisés pour vérifier le code, PAS pour le dashboard.
    (tmp_path / 'Caract_2025.csv').write_text(
        'Num_Acc;jour;mois;hrmn;dep;com;agg;lum;atm;lat;long\n'
        '2025001;04;02;08:35;69;69001;2;1;1;45,76;4,83\n'
        '2025002;15;07;19:20;75;75101;2;3;2;48,86;2,35\n', encoding='utf-8')
    (tmp_path / 'Lieux_2025.csv').write_text(
        'Num_Acc;catr;vma\n2025001;3;50\n2025002;4;30\n', encoding='utf-8')
    (tmp_path / 'Vehicules_2025.csv').write_text(
        'Num_Acc;id_vehicule;catv\n2025001;V1;7\n2025001;V2;7\n2025002;V3;1\n', encoding='utf-8')
    (tmp_path / 'Usagers_2025.csv').write_text(
        'Num_Acc;grav;sexe;catu;an_nais\n'
        '2025001;2;1;1;1980\n2025001;4;2;2;2001\n'
        '2025001;1;1;1;1990\n2025002;3;2;3;2010\n', encoding='utf-8')
    a, u, quality = create_year_frames(2025, tmp_path)
    assert len(a) == 2  # et non 3 véhicules × 4 usagers
    assert len(u) == 4
    assert a.nb_vehicules.tolist() == [2, 1]
    assert a.nb_tues.tolist() == [1, 0]
    assert a.nb_blesses_graves.tolist() == [0, 1]
    assert a.accident_mortel.tolist() == [True, False]
    assert a.departement.tolist() == ['69', '75']
    assert a.heure.tolist() == [8, 19]
    assert abs(a.latitude.iloc[0] - 45.76) < 0.0001
    assert quality['coordonnees_manquantes'] == 0
    assert quality['accidents_uniques'] == 2


def test_clean_dep():
    import pandas as pd
    from src.pipeline import clean_dep
    assert clean_dep(pd.Series(['1', '75', '2A', '971'])).tolist() == ['01','75','2A','971']
