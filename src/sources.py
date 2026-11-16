"""Découverte et téléchargement des ressources OFFICIELLES BAAC via data.gouv.fr."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DATASET_PAGE = (
    'https://www.data.gouv.fr/datasets/'
    'bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2025'
)
DATASET_API = (
    'https://www.data.gouv.fr/api/1/datasets/'
    'bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2025/'
)
KINDS = {'caract': 'Caract', 'lieux': 'Lieux', 'vehicules': 'Vehicules', 'usagers': 'Usagers'}
# Identifiants officiels de secours pour 2025, vérifiés sur data.gouv.fr le 15/11/2026.
FALLBACK_2025 = {
    'caract': 'e5a1c21d-17cb-4ee0-b85f-8e34aba4d309',
    'lieux': '29db11b7-dad2-480f-943d-725ffdeb9a27',
    'vehicules': '58ba05bf-661d-4c59-b504-3d77336ccb8f',
    'usagers': '513b5a4a-20cc-4ee2-a0c8-5e5a82ad69a4',
}


def session() -> requests.Session:
    s = requests.Session()
    policy = Retry(total=3, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=policy))
    s.headers['User-Agent'] = 'HexaRoute-OpenData-Portfolio/1.0 (public BAAC research)'
    return s


def normalized(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(name).lower())


def match_resources(resources: list[dict], years: list[int]) -> dict[tuple[int, str], dict]:
    """Identifie exactement 4 CSV / année; exclut le fichier des immatriculations."""
    found = {}
    for yr in years:
        for kind in KINDS:
            expected = f'{kind}{yr}csv'
            candidates = [r for r in resources if normalized(r.get('title') or r.get('filename')) == expected]
            if candidates:
                # Utilise la ressource la plus récemment modifiée si doublons présents.
                found[(yr, kind)] = max(candidates, key=lambda r: str(r.get('last_modified') or ''))
            elif yr == 2025:
                found[(yr, kind)] = {
                    'title': f'{KINDS[kind]}_{yr}.csv',
                    'id': FALLBACK_2025[kind],
                    'url': f'https://www.data.gouv.fr/api/1/datasets/r/{FALLBACK_2025[kind]}',
                }
            else:
                raise ValueError(f'Ressource officielle manquante : {KINDS[kind]}_{yr}.csv')
    return found


def discover(years: list[int], s: requests.Session | None = None) -> dict[tuple[int, str], dict]:
    client = s or session()
    try:
        response = client.get(DATASET_API, timeout=(12, 45))
        response.raise_for_status()
        data = response.json()
        resources = data.get('resources', [])
        return match_resources(resources, years)
    except requests.RequestException:
        if years == [2025]:
            return match_resources([], years)
        raise RuntimeError('Impossible de contacter l’API data.gouv.fr. Vérifie Internet et réessaie.')


def fetch_years(years: list[int], raw_dir: Path, progress=None) -> list[dict]:
    """Télécharge les véritables CSV, avec écriture atomique et métadonnées vérifiables."""
    years = sorted(set(years))
    if not years or min(years) < 2005 or max(years) > 2025:
        raise ValueError('Années autorisées : de 2005 à 2025.')
    raw_dir.mkdir(parents=True, exist_ok=True)
    s = session()
    resources = discover(years, s)
    meta = []
    for year in years:
        for kind, pretty in KINDS.items():
            info = resources[(year, kind)]
            path = raw_dir / f'{pretty}_{year}.csv'
            source_url = info.get('url') or f"https://www.data.gouv.fr/api/1/datasets/r/{info['id']}"
            if not urlparse(source_url).scheme == 'https':
                raise ValueError(f'URL non HTTPS refusée : {source_url}')
            if progress:
                progress(f'{year} · {pretty} : ' + ('déjà présent' if path.exists() and path.stat().st_size else 'téléchargement'))
            if not path.exists() or path.stat().st_size == 0:
                tmp = path.with_suffix('.csv.part')
                digest = hashlib.sha256()
                try:
                    with s.get(source_url, stream=True, timeout=(15, 180)) as r:
                        r.raise_for_status()
                        with tmp.open('wb') as out:
                            for chunk in r.iter_content(chunk_size=1024 * 512):
                                if chunk:
                                    out.write(chunk)
                                    digest.update(chunk)
                    if tmp.stat().st_size < 50:
                        raise ValueError(f'Fichier anormalement court : {path.name}')
                    tmp.replace(path)
                except Exception:
                    tmp.unlink(missing_ok=True)
                    raise
            hashfile = hashlib.sha256()
            with path.open('rb') as inp:
                for chunk in iter(lambda: inp.read(1024 * 1024), b''):
                    hashfile.update(chunk)
            meta.append({
                'annee': year, 'table': kind, 'fichier': str(path.name),
                'taille_octets': path.stat().st_size,
                'sha256': hashfile.hexdigest(), 'source': source_url,
                'ressource_id': info.get('id'), 'telecharge_le': datetime.now(timezone.utc).isoformat(),
            })
    (raw_dir / 'sources_manifest.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return meta
