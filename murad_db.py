import psycopg2

class User:
    def __init__(self, id, username, name, surname, password):
        self.id = id
        self.username = username
        self.name = name
        self.surname = surname
        self.password = password

# Database connection parameters
conn_params = {
    'dbname': 'test',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',  # Or the appropriate host
    'port': '5432'        # Default PostgreSQL port
}

def getUserListFromDb():
    l = []
    try:
        # Establish a connection to the database
        conn = psycopg2.connect(**conn_params)
        
        # Create a cursor object
        cur = conn.cursor()
        
        # Execute a query to select all users
        cur.execute("SELECT id, username, name, surname FROM users")
        
        # Fetch all rows from the executed query
        users = cur.fetchall()
        
        # Print each user
        
        for user in users:
            a = User(user[0], user[1], user[2], user[3], '')
            l.append(a)

        # Close the cursor and connection
        cur.close()
        conn.close()
        return l
    except Exception as e:
        print(f"An error occurred: {e}")
userlist = getUserListFromDb()

if len(userlist) != 1 or userlist[0].name != 'Jane' or userlist[0].id != 1:
    print('getUserListFromDb test failed')
else:
    print('getUserListFromDb test succeeded') 

def getUserById(user_id):
    #def getUserById(user_id):
    # Establish a connection to the database
    with psycopg2.connect(**conn_params) as conn:
        # Create a cursor object
        with conn.cursor() as cur:
            # Use parameterized query to prevent SQL injection
            query = sql.SQL("SELECT id, username, name, surname FROM users WHERE id = %s")
            cur.execute(query, (user_id,))
            
            # Fetch the result
            user = cur.fetchone()

            if user is None:
                return None

            # Create and return the User object
            a = User(user[0], user[1], user[2], user[3], '')
            return a
user_id = 2
e = getUserById(user_id)
if e is not None:
    print(e.id, e.username, e.name, e.surname, e.password)
else:
    print(f'User with id: {user_id} doesn''t exist')