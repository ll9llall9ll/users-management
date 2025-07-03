conn_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5433'
}

openai_params = {
    'api_key': ''
}

def getDbConfig():
    return conn_params

def getOpenaiConfig():
    return openai_params

def getFullConfig():
    return {
        'openai_api_key': '',
        'db_config': conn_params,
        'google_oauth_config': {
            'client_id': ''
        },
        'app': {
            'port': '5006',
            'debug': False
        }
    }
