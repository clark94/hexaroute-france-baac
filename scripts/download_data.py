"""Téléchargement reproductible BAAC, 4 CSV officiels par année."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.sources import fetch_years

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Télécharge 4 CSV officiels BAAC par année depuis data.gouv.fr.')
    parser.add_argument('--years', nargs='+', type=int, default=[2025], help='ex. --years 2023 2024 2025')
    args = parser.parse_args()
    files = fetch_years(args.years, ROOT / 'data' / 'raw', progress=print)
    print(f'\n✅ {len(files)} CSV officiels disponibles. Manifest SHA256 enregistré.')
