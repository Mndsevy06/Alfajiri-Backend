import environ
from pathlib import Path
import psycopg2
import sys

BASE_DIR = Path(__file__).resolve().parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

db_url = env('DATABASE_URL')
print(f"DATABASE_URL: {db_url}")

db_settings = env.db('DATABASE_URL')
print(f"db_settings: {db_settings}")

conn_params = {
    'dbname': db_settings['NAME'],
    'user': db_settings['USER'],
    'password': db_settings['PASSWORD'],
    'host': db_settings['HOST'],
    'port': db_settings['PORT'],
}

try:
    print(f"Attempting connection with: {conn_params}")
    conn = psycopg2.connect(**conn_params)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {repr(e)}")
    import traceback
    traceback.print_exc()
