import psycopg2

class User:
    def __init__(self, id, username, name, surname, password):
        self.id = id
        self.username = username
        self.name = name
        self.surname = surname
        self.password = password


def getUserListFromDb():
    l = []


    return l

def getUserById(id):
    
    return User()

userList = getUserListFromDb()
if len(userList) != 1 or userList[0].name != 'Jane' or userList[0].id != 1:
    print('getUserListFromDb test failed')
else:
    print('getUserListFromDb succeeded')

# Database connection parameters
conn_params = {
    'dbname': 'avecoder',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',  # Or the appropriate host
    'port': '5433'        # Default PostgreSQL port
}

try:
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
        print(f"ID: {user[0]}, Username: {user[1]}, Name: {user[2]}, Surname: {user[3]}")
    
    # Close the cursor and connection
    cur.close()
    conn.close()

except Exception as e:
    print(f"An error occurred: {e}")
