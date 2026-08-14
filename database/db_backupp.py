import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )

    test_schema = os.getenv("ERP_TEST_SCHEMA")

    if test_schema:
        if test_schema != "alif_migration_test":
            raise ValueError("Invalid ERP_TEST_SCHEMA")

        with conn.cursor() as cur:
            cur.execute(
                'SET search_path TO "alif_migration_test", public'
            )

    return conn