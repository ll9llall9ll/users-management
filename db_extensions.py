import psycopg2
from config import getDbConfig

def executeQuery(query, params=None):
    try:
        conn_params = getDbConfig()
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                
                # Если запрос типа SELECT, возвращаем результаты
                if query.strip().upper().startswith('SELECT'):
                    return cur.fetchall()
                
                # Для других типов запросов просто коммитим транзакцию
                conn.commit()
                return True
    except Exception as e:
        print(f"Database error: {e}")
        # Можно добавить логирование ошибки
        return False