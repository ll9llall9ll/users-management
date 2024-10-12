import psycopg2
from config import getDbConfig


def executeQuery(query):
    conn_params = getDbConfig()
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()