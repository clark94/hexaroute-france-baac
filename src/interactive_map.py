"""Carte Leaflet/JavaScript isolée pour l'onglet géographie de HexaRoute.

Données : vrais enregistrements BAAC déjà filtrés dans Streamlit.
Pas de pseudo-points ni d'appel à un service de géocodage.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
MAX_MAP_POINTS = 4500
COLORS = {
    'Mortel': '#FB7185',
    'Avec blessé hospitalisé': '#FFCC7D',
    'Avec blessé léger': '#64D9EB',
    'Indéterminée': '#A4AEC6',
}


def build_map_payload(frame: pd.DataFrame, limit: int = MAX_MAP_POINTS) -> dict:
    """Crée un échantillon stable sans modifier ni inventer de données."""
    geo = frame.dropna(subset=['latitude', 'longitude']).copy()
    geo = geo[geo['latitude'].between(41, 52) & geo['longitude'].between(-6, 10)]
    total = len(geo)
    if len(geo) > limit:
        geo = geo.sample(n=limit, random_state=42).sort_index()

    fields = ('latitude', 'longitude', 'gravite_accident', 'departement', 'date',
              'annee', 'nb_tues', 'nb_vehicules', 'nb_usagers')
    records = []
    for values in geo[list(fields)].itertuples(index=False, name=None):
        lat, lon, gravity, department, date, year, killed, vehicles, users = values
        if not (math.isfinite(float(lat)) and math.isfinite(float(lon))):
            continue
        records.append({
            'lat': round(float(lat), 6),
            'lng': round(float(lon), 6),
            'severity': str(gravity) if pd.notna(gravity) else 'Indéterminée',
            'dep': str(department) if pd.notna(department) else '—',
            'date': (pd.Timestamp(date).strftime('%d/%m/%Y') if pd.notna(date) else 'Non renseignée'),
            'year': int(year) if pd.notna(year) else None,
            'killed': max(0, int(killed)) if pd.notna(killed) else 0,
            'vehicles': max(0, int(vehicles)) if pd.notna(vehicles) else 0,
            'users': max(0, int(users)) if pd.notna(users) else 0,
        })
    return {
        'points': records,
        'total_metro_geocoded': total,
        'sample_size': len(records),
        'color': COLORS,
        'sampled': total > limit,
    }


def _json_for_script(data: dict) -> str:
    """Désamorce les séquences HTML dans le JSON (source officielle non fiable en HTML)."""
    return (json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def build_map_html(payload: dict) -> str:
    template = (ASSETS / 'map.html').read_text(encoding='utf-8')
    css = (ASSETS / 'map.css').read_text(encoding='utf-8')
    js = (ASSETS / 'map.js').read_text(encoding='utf-8')
    return (template.replace('/*__MAP_STYLES__*/', css)
            .replace('/*__MAP_SCRIPT__*/', js)
            .replace('__MAP_DATA_JSON__', _json_for_script(payload)))


def build_hero_html() -> str:
    template = (ASSETS / 'hero.html').read_text(encoding='utf-8')
    css = (ASSETS / 'hero.css').read_text(encoding='utf-8')
    js = (ASSETS / 'hero.js').read_text(encoding='utf-8')
    return (template.replace('/*__HERO_STYLES__*/', css)
            .replace('/*__HERO_SCRIPT__*/', js))
