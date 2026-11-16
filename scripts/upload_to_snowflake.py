"""Charge les données HexaRoute préparées dans Snowflake."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from src.snowflake_io import connect, settings


def main():
    from snowflake.connector.pandas_tools import write_pandas

    parser = argparse.ArgumentParser(
        description="Publie les tables préparées dans Snowflake."
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Vide et recharge les tables ACCIDENTS et USAGERS.",
    )
    args = parser.parse_args()
    if not args.replace:
        raise SystemExit(
            "Utiliser --replace pour confirmer le remplacement des données."
        )

    config = settings()
    if (
        config["database"].upper() != "HEXAROUTE_DB"
        or config["schema"].upper() != "ANALYTICS"
    ):
        raise SystemExit(
            "Ce script est prévu pour HEXAROUTE_DB.ANALYTICS."
        )

    tables = {}
    for name in ("ACCIDENTS", "USAGERS"):
        path = ROOT / "data" / "processed" / f"{name.lower()}.parquet"
        if not path.is_file():
            raise SystemExit(f"Fichier absent : {path}. Lance d'abord build_dataset.py.")

        data = pd.read_parquet(path)
        data.columns = [column.upper() for column in data.columns]

        if "DATE" in data.columns:
            data["DATE"] = pd.to_datetime(data["DATE"], errors="raise").dt.date

        tables[name] = data

    with connect() as conn:
        schema_sql = (ROOT / "sql" / "snowflake_01_schema.sql").read_text(
            encoding="utf-8"
        )
        conn.execute_string(schema_sql)

        for name, data in tables.items():
            with conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE HEXAROUTE_DB.ANALYTICS.{name}")

            success, chunks, rows, _ = write_pandas(
                conn,
                data,
                name,
                database="HEXAROUTE_DB",
                schema="ANALYTICS",
                chunk_size=20_000,
                quote_identifiers=False,
                use_logical_type=True,
            )
            if not success or rows != len(data):
                raise RuntimeError(
                    f"Chargement incomplet pour {name} : {rows}/{len(data)} lignes."
                )
            print(f"✅ {name} : {rows:,} lignes chargées, {chunks} fichiers traités.")

        views_sql = (ROOT / "sql" / "snowflake_02_views.sql").read_text(
            encoding="utf-8"
        )
        conn.execute_string(views_sql)

    print("✅ Vues créées. Exécute snowflake_03_checks.sql dans Snowflake.")


if __name__ == "__main__":
    main()