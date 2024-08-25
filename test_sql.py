import psycopg2

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
        

def getUserById(user_id):
    conn_params = {
        'dbname': 'avecoder',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',  
        'port': '5433'       
    }
    
    # Establish a connection to the database
    with psycopg2.connect(**conn_params) as conn:
        # Create a cursor object
        with conn.cursor() as cur:
            # Use parameterized query to prevent SQL injection
            query = (f"SELECT id, username, name, surname FROM users WHERE id = {user_id}")
            cur.execute(query)
            
            # Fetch the result
            user = cur.fetchone()

            if user is None:
                return None

            # Create and return the User object
            a = User(user[0], user[1], user[2], user[3], '')
            return a

def getUserByUsernameAndPassword(username, password):
    conn_params = {
        'dbname': 'avecoder',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',
        'port': '5433'
    }
    query = (f"SELECT id, username, name, surname, password FROM users WHERE username = {username} AND password = {password}")  
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'name': user[2],
            'surname': user[3],
            'password': user[4]
                }
    else:
        return None
    
userList = getUserListFromDb()
if len(userList) != 1 or userList[0].name != 'Jane' or userList[0].id != 1:
    print('getUserListFromDb test failed')
else:
    print('getUserListFromDb succeeded')

user = getUserById(1)
if user and user.name == 'Jane' and user.id == 1:
    print('getUserById test succeeded')
else:
    print('getUserById test failed')


user = getUserByUsernameAndPassword('JaneDoe', 'securepassword')
if user is None:
    print('getUserByUsernameAndPassword test failed: No user returned')
elif user['username'] != 'JaneDoe' or user['id'] != 1 or user['name'] != 'Jane':
    print('getUserByUsernameAndPassword test failed: Incorrect user data')
else:
    print('getUserByUsernameAndPassword succeeded')
