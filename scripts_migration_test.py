import os
import glob
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SCHEMA = "alif_migration_test"

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
conn.autocommit = False

try:
    cur = conn.cursor()

    cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"')
    cur.execute(f'SET search_path TO "{SCHEMA}"')

    files = sorted(glob.glob("database/migrations/*.sql"))

    print(f"Migrations found: {len(files)}")
    print(f"Target schema: {SCHEMA}")
    print()

    for path in files:
        name = os.path.basename(path)
        print(f"RUN: {name}")

        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()

        cur.execute(sql)
        conn.commit()

        print(f"PASS: {name}")
        print()

    cur.close()
    print("========================================")
    print("ALL MIGRATIONS COMPLETED SUCCESSFULLY")
    print("========================================")

except Exception as e:
    conn.rollback()
    print()
    print("========================================")
    print("MIGRATION FAILED")
    print("========================================")
    print(type(e).__name__ + ":", e)
    print()
    raise

finally:
    conn.close()
