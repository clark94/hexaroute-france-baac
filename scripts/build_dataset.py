"""Préparer Parquet + journal qualité à partir des fichiers BAAC officiels."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pipeline import build_dataset

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Construit le modèle analytique BAAC.')
    parser.add_argument('--years', nargs='+', type=int, default=[2025])
    args = parser.parse_args()
    quality = build_dataset(args.years, ROOT/'data'/'raw', ROOT/'data'/'processed', progress=print)
    print(f"\n✅ Modèle prêt : {quality['accidents']:,} accidents, {quality['usagers']:,} usagers.")
    print('Données optimisées : data/processed/accidents.parquet et usagers.parquet')
