"""Contrôles du composant JavaScript et de la préparation des points BAAC."""
import pandas as pd
from src.interactive_map import build_map_payload, build_map_html, build_hero_html


def fixture():
    return pd.DataFrame([
        {'latitude':45.764, 'longitude':4.8357, 'gravite_accident':'Mortel',
         'departement':'69', 'date':'2025-02-15', 'annee':2025, 'nb_tues':1,
         'nb_vehicules':2, 'nb_usagers':3},
        {'latitude':48.8566, 'longitude':2.3522, 'gravite_accident':'Avec blessé léger',
         'departement':'75', 'date':'2025-04-03', 'annee':2025, 'nb_tues':0,
         'nb_vehicules':1, 'nb_usagers':2},
        {'latitude':16.2, 'longitude':-61.5, 'gravite_accident':'Mortel',
         'departement':'971', 'date':'2025-05-09', 'annee':2025, 'nb_tues':1,
         'nb_vehicules':1, 'nb_usagers':1},
    ])


def test_map_uses_actual_records_and_metro_filter():
    data = build_map_payload(fixture())
    assert data['sample_size'] == 2
    assert data['total_metro_geocoded'] == 2
    assert {point['dep'] for point in data['points']} == {'69','75'}
    assert data['points'][0]['killed'] == 1
    assert data['points'][0]['date'] == '15/02/2025'


def test_map_sampling_reproducible_and_labeled():
    data = pd.concat([fixture().iloc[:1]] * 20, ignore_index=True)
    one = build_map_payload(data, limit=5)
    two = build_map_payload(data, limit=5)
    assert one == two
    assert one['sample_size'] == 5
    assert one['sampled'] is True
    assert one['total_metro_geocoded'] == 20


def test_map_data_escaped_from_script_and_js_loaded():
    frame = fixture()
    frame.loc[0,'departement'] = '</script><script>alert(1)</script>'
    html = build_map_html(build_map_payload(frame))
    assert '</script><script>alert' not in html
    assert '\\u003c/script\\u003e' in html
    assert 'leaflet.markercluster' in html
    assert 'L.heatLayer' in html
    assert 'data-mode="clusters"' in html


def test_hero_includes_live_canvas_without_fake_data():
    html = build_hero_html()
    assert '<canvas id="terrain"' in html
    assert 'requestAnimationFrame' in html
    assert 'OBSERVATOIRE NATIONAL' in html
