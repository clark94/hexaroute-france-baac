"""Analyse SQL *réelle* avec DuckDB sur les fichiers Parquet, sans base distante."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import duckdb

if __name__ == '__main__':
    parquet = ROOT/'data'/'processed'/'accidents.parquet'
    if not parquet.exists():
        raise SystemExit('Données absentes : exécuter scripts/download_data.py puis scripts/build_dataset.py.')
    conn = duckdb.connect()
    conn.from_parquet(str(parquet)).create_view('accidents')
    queries = {
        'kpi_mensuels': '''
            SELECT annee, date_trunc('month', date) AS mois, COUNT(*) AS accidents,
                   SUM(nb_tues) AS personnes_tuees,
                   SUM(nb_blesses_graves) AS blesses_hospitalises
            FROM accidents WHERE date IS NOT NULL
            GROUP BY ALL ORDER BY annee, mois''',
        'kpi_departements': '''
            SELECT annee, departement, COUNT(*) AS accidents,
                   SUM(nb_tues) AS personnes_tuees,
                   SUM(nb_vehicules) AS vehicules_impliques
            FROM accidents GROUP BY ALL ORDER BY annee, accidents DESC''',
        'kpi_horaires': '''
            SELECT annee, heure, COUNT(*) AS accidents
            FROM accidents WHERE heure IS NOT NULL
            GROUP BY ALL ORDER BY annee, heure''',
    }
    for name, sql in queries.items():
        output = ROOT/'data'/'processed'/f'{name}.csv'
        conn.execute(sql).df().to_csv(output, index=False)
        print(f'✅ {output.relative_to(ROOT)}')
    conn.close()
