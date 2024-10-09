conn_params = {
    'dbname': 'diginv',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5433'
}

def getDbConfig():
    return conn_params