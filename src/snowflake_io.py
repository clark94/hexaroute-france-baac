"""Accès facultatif à Snowflake (le mode local Parquet reste la valeur par défaut)."""
from __future__ import annotations
import os
import pandas as pd
from dotenv import load_dotenv


def settings():
    load_dotenv()
    required = ['SNOWFLAKE_ACCOUNT', 'SNOWFLAKE_USER', 'SNOWFLAKE_PASSWORD', 'SNOWFLAKE_WAREHOUSE']
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f'Configuration Snowflake absente : {", ".join(missing)}. Copier .env.example vers .env.')
    return {
        'account': os.environ['SNOWFLAKE_ACCOUNT'],
        'user': os.environ['SNOWFLAKE_USER'],
        'password': os.environ['SNOWFLAKE_PASSWORD'],
        'warehouse': os.environ['SNOWFLAKE_WAREHOUSE'],
        'database': os.getenv('SNOWFLAKE_DATABASE', 'HEXAROUTE_DB'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS'),
        'role': os.getenv('SNOWFLAKE_ROLE') or None,
    }


def connect():
    try:
        import snowflake.connector
    except ImportError as err:
        raise RuntimeError('Installer requirements-snowflake.txt pour utiliser Snowflake.') from err
    return snowflake.connector.connect(**settings(), client_session_keep_alive=False)


def fetch_tables():
    with connect() as conn:
        frames = {}
        for name in ('ACCIDENTS', 'USAGERS'):
            with conn.cursor() as cur:
                cur.execute(f'SELECT * FROM {name}')
                frames[name.lower()] = cur.fetch_pandas_all()
    for frame in frames.values():
        frame.columns = [c.lower() for c in frame.columns]
    return frames['accidents'], frames['usagers']
