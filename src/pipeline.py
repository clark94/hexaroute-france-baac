"""Pipeline de préparation BAAC : une ligne par accident, sans jointures multiplicatives."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.sources import KINDS, DATASET_PAGE


REQUIRED = {
    'caract': ['num_acc', 'jour', 'mois', 'dep'],
    'lieux': ['num_acc'],
    'vehicules': ['num_acc'],
    'usagers': ['num_acc', 'grav'],
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f'{path.name} absent. Télécharge les fichiers officiels avant préparation.')
    raw = path.open('rb').read(16384)
    try:
        sample = raw.decode('utf-8-sig')
        encoding = 'utf-8-sig'
    except UnicodeDecodeError:
        sample = raw.decode('cp1252', errors='replace')
        encoding = 'cp1252'
    # Le premier en-tête BAAC contient des points-virgules;
    # analyser cette ligne évite de confondre les virgules décimales des coordonnées.
    header = sample.splitlines()[0] if sample.splitlines() else ''
    sep = ';' if header.count(';') >= header.count(',') else ','
    df = pd.read_csv(path, sep=sep, dtype='string', encoding=encoding, keep_default_na=False,
                     low_memory=False, on_bad_lines='warn')
    df.columns = [str(c).strip().lower().replace('\ufeff', '') for c in df.columns]
    for col in df.columns:
        df[col] = df[col].str.strip()
    return df


def check_columns(df: pd.DataFrame, kind: str, year: int):
    absent = set(REQUIRED[kind]) - set(df.columns)
    if absent:
        raise ValueError(f'{KINDS[kind]}_{year}.csv : colonnes introuvables : {sorted(absent)}; disponibles : {list(df.columns)}')


def col(df: pd.DataFrame, name: str, fallback: str = '') -> pd.Series:
    return df[name] if name in df.columns else pd.Series(fallback, index=df.index, dtype='string')


def number(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype('string').str.replace(',', '.', regex=False), errors='coerce')


def clean_dep(s: pd.Series) -> pd.Series:
    v = s.astype('string').str.strip().str.upper()
    # Conserve 2A, 2B et les codes outre-mer à 3 chiffres; 1 devient 01.
    return v.map(lambda x: x.zfill(2) if isinstance(x, str) and x.isdigit() and len(x) < 2 else x)


def create_year_frames(year: int, raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    raw = {kind: read_csv(raw_dir / f'{pretty}_{year}.csv') for kind, pretty in KINDS.items()}
    for kind, df in raw.items():
        check_columns(df, kind, year)
        df['num_acc'] = df['num_acc'].astype('string')
        df.drop(df.index[df['num_acc'].isna() | (df['num_acc'] == '')], inplace=True)

    c, l, v, u = (raw[k] for k in KINDS)
    c_dups = int(c.duplicated('num_acc').sum())
    l_dups = int(l.duplicated('num_acc').sum())
    c = c.drop_duplicates('num_acc').copy()
    l = l.drop_duplicates('num_acc').copy()

    n = len(c)
    a = pd.DataFrame({'annee': [year] * n, 'num_acc': c['num_acc'].to_numpy()})
    a['departement'] = clean_dep(col(c, 'dep').reset_index(drop=True))
    a['commune_code'] = col(c, 'com').reset_index(drop=True)
    jour, mois = number(col(c, 'jour')).reset_index(drop=True), number(col(c, 'mois')).reset_index(drop=True)
    a['date'] = pd.to_datetime({'year': year, 'month': mois, 'day': jour}, errors='coerce')
    a['mois_num'] = mois.astype('Int64')
    a['jour_semaine'] = a['date'].dt.dayofweek.astype('Int64')
    hrmn = col(c, 'hrmn').reset_index(drop=True).astype('string')
    # BAAC post-2019: hh:mm ; accepte également hhmm.
    hours = hrmn.str.extract(r'^(\d{1,2}):?(\d{2})$')
    h = pd.to_numeric(hours[0], errors='coerce')
    m = pd.to_numeric(hours[1], errors='coerce')
    a['heure'] = h.where(h.between(0, 23) & m.between(0, 59)).astype('Int64')
    a['latitude'] = number(col(c, 'lat')).reset_index(drop=True)
    a['longitude'] = number(col(c, 'long')).reset_index(drop=True)
    a.loc[~a['latitude'].between(-90, 90), 'latitude'] = float('nan')
    a.loc[~a['longitude'].between(-180, 180), 'longitude'] = float('nan')
    for name in ('lum', 'atm', 'agg'):
        a[name] = number(col(c, name).reset_index(drop=True)).astype('Int64')
    a['milieu'] = a['agg'].map({1: 'Hors agglomération', 2: 'En agglomération'}).fillna('Non renseigné')
    a['luminosite'] = a['lum'].map({
        1: 'Plein jour', 2: 'Aube / crépuscule', 3: 'Nuit, sans éclairage',
        4: 'Nuit, éclairage éteint', 5: 'Nuit, éclairage allumé',
    }).fillna('Non renseigné')
    a['meteo'] = a['atm'].map({
        1: 'Normale', 2: 'Pluie légère', 3: 'Pluie forte', 4: 'Neige / grêle',
        5: 'Brouillard / fumée', 6: 'Vent fort / tempête', 7: 'Temps éblouissant',
        8: 'Temps couvert', 9: 'Autre',
    }).fillna('Non renseigné')

    lieux = l[['num_acc']].copy()
    lieux['vma'] = number(col(l, 'vma'))
    lieux['categorie_route'] = col(l, 'catr')
    a = a.merge(lieux, on='num_acc', how='left', validate='one_to_one')

    # Ne jamais joindre directement les lignes véhicules/usagers aux accidents :
    # leur multiplicité créerait de faux accidents.
    vehicles = v.groupby('num_acc', dropna=False).size().rename('nb_vehicules').reset_index()
    a = a.merge(vehicles, on='num_acc', how='left', validate='one_to_one')
    a['nb_vehicules'] = a['nb_vehicules'].fillna(0).astype('int64')

    people = u[['num_acc']].copy()
    people['gravite_code'] = number(col(u, 'grav')).astype('Int64')
    people['sexe'] = number(col(u, 'sexe')).map({1: 'Homme', 2: 'Femme'}).fillna('Non renseigné')
    people['profil'] = number(col(u, 'catu')).map({1: 'Conducteur', 2: 'Passager', 3: 'Piéton'}).fillna('Autre / inconnu')
    people['age'] = (year - number(col(u, 'an_nais'))).where(lambda s: s.between(0, 105))
    people['annee'] = year
    people = people[['annee', 'num_acc', 'gravite_code', 'sexe', 'profil', 'age']]
    severity = people.assign(
        tue=(people.gravite_code == 2).fillna(False).astype('int8'),
        blesse_grave=(people.gravite_code == 3).fillna(False).astype('int8'),
        blesse_leger=(people.gravite_code == 4).fillna(False).astype('int8'),
    ).groupby('num_acc', as_index=False, dropna=False).agg(
        nb_usagers=('gravite_code', 'size'),
        nb_tues=('tue', 'sum'),
        nb_blesses_graves=('blesse_grave', 'sum'),
        nb_blesses_legers=('blesse_leger', 'sum'),
    )
    a = a.merge(severity, on='num_acc', how='left', validate='one_to_one')
    for name in ('nb_usagers', 'nb_tues', 'nb_blesses_graves', 'nb_blesses_legers'):
        a[name] = a[name].fillna(0).astype('int64')
    a['accident_mortel'] = a.nb_tues.gt(0)
    a['gravite_accident'] = 'Indéterminée'
    a.loc[a.nb_blesses_legers > 0, 'gravite_accident'] = 'Avec blessé léger'
    a.loc[a.nb_blesses_graves > 0, 'gravite_accident'] = 'Avec blessé hospitalisé'
    a.loc[a.accident_mortel, 'gravite_accident'] = 'Mortel'

    audit = {
        'annee': year,
        'accidents_csv': len(raw['caract']), 'accidents_uniques': n,
        'doublons_caracteristiques': c_dups, 'doublons_lieux': l_dups,
        'lieux_non_renseignes': int(a.categorie_route.isna().sum()),
        'accidents_sans_usagers': int(a.nb_usagers.eq(0).sum()),
        'accidents_sans_vehicules': int(a.nb_vehicules.eq(0).sum()),
        'coordonnees_manquantes': int((a.latitude.isna() | a.longitude.isna()).sum()),
        'dates_invalides': int(a.date.isna().sum()),
        'usagers_csv': len(raw['usagers']), 'vehicules_csv': len(raw['vehicules']),
        'source': DATASET_PAGE,
    }
    return a, people, audit


def build_dataset(years: list[int], raw_dir: Path, processed_dir: Path, progress=None) -> dict:
    """Construire deux fichiers parquet reproductibles et un journal de qualité JSON."""
    years = sorted(set(int(y) for y in years))
    processed_dir.mkdir(parents=True, exist_ok=True)
    af, uf, qf = [], [], []
    for y in years:
        if progress:
            progress(f'Préparation et jointures de {y}')
        a, u, audit = create_year_frames(y, raw_dir)
        af.append(a)
        uf.append(u)
        qf.append(audit)
    accidents = pd.concat(af, ignore_index=True)
    usagers = pd.concat(uf, ignore_index=True)
    if accidents.duplicated(['annee', 'num_acc']).any():
        raise AssertionError('Doublons inattendus sur (annee, num_acc) après préparation.')
    # Arrow sérialise correctement les colonnes nullable pour les lectures rapides du dashboard.
    for name, frame in [('accidents', accidents), ('usagers', usagers)]:
        tmp = processed_dir / f'{name}.tmp.parquet'
        frame.to_parquet(tmp, index=False, compression='zstd')
        tmp.replace(processed_dir / f'{name}.parquet')
    result = {
        'genere_le_utc': datetime.now(timezone.utc).isoformat(),
        'annees': years, 'accidents': int(len(accidents)), 'usagers': int(len(usagers)),
        'vehicules': sum(x['vehicules_csv'] for x in qf),
        'details_qualite': qf,
        'description': 'Données publiques officielles BAAC, accidents corporels uniquement.',
        'source': DATASET_PAGE,
    }
    (processed_dir / 'qualite.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result
