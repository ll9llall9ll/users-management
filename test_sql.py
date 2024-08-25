import psycopg2
from enum import Enum


class Template:
    def __init__(self, id, name, view_name, template_type, preview_url):
        self.id = id
        self.name = name
        self.view_name = view_name
        self.template_type = template_type
        self.preview_url = preview_url

class TemplateType(Enum):
    Wedding = 1
    Birthday = 2


a = TemplateType.Wedding

class User:
    def __init__(self, id, username, name, surname, password):
        self.id = id
        self.username = username
        self.name = name
        self.surname = surname
        self.password = password


def getUserListFromDb():
    # Database connection parameters
    conn_params = {
        'dbname': 'avecoder',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',  # Or the appropriate host
        'port': '5433'        # Default PostgreSQL port
    }
    userList = []

    # Establish a connection to the database
    conn = psycopg2.connect(**conn_params)
    
    # Create a cursor object
    cur = conn.cursor()
    
    # Execute a query to select all users
    cur.execute("SELECT id, username, name, surname FROM users")
    
    # Fetch all rows from the executed query
    users = cur.fetchall()
    [['1', 'janedoe', 'Jane', 'Doe'], []]
    
    # Print each user
    for user in users:
        user_obj = User(
            id=user[0],
            username=user[1],
            name=user[2],
            surname=user[3],
            password=None
        )
        userList.append(user_obj)
    # Close the cursor and connection
    cur.close()
    conn.close()

    return userList
