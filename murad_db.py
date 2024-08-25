import psycopg2

class User:
    def __init__(self, id, username, name, surname, password, is_admin = False):
        self.id = id
        self.username = username
        self.name = name
        self.surname = surname
        self.password = password
        self.is_admin = is_admin

# Database connection parameters
conn_params = {
    'dbname': 'avecoder',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',  # Or the appropriate host
    'port': '5433'        # Default PostgreSQL port
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

def getUserById(user_id):
    #def getUserById(user_id):
    # Establish a connection to the database

    conn = psycopg2.connect(**conn_params)
    
    # Create a cursor object
    cur = conn.cursor()
    
    # Execute a query to select all users
    cur.execute(f"SELECT * FROM users WHERE id = {user_id}")
    
    # Fetch all rows from the executed query
    user = cur.fetchone()

    if user is None:
        return None

    # Create and return the User object
    a = User(user[0], user[1], user[2], user[3], user[4])
    return a

user_id = 1
e = getUserById(user_id)
if e is not None:
    print(e.id, e.username, e.name, e.surname, e.password)
else:
    print(f'User with id: {user_id} doesn''t exist')

def getUserByUsernameAndPassword(user_username, user_password):
    # Establish a connection to the database
    conn = psycopg2.connect(**conn_params)
    
    # Create a cursor object
    cur = conn.cursor()
    
    # Execute a query to select all users
    cur.execute(f"SELECT * FROM users WHERE username = '{user_username}' and password = '{user_password}'")
    
    # Fetch all rows from the executed query
    users = cur.fetchall()

    # Close the cursor and connection
    cur.close()
    conn.close()

    if len(users) == 0:
        return None
    b = User(users[0][0], users[0][1], users[0][2], users[0][3], users[0][4], is_admin = users[0][5])
    
    return b

user_username = 'janedoe'
user_password = 'newsecurepassword'
c = getUserByUsernameAndPassword(user_username, user_password)
if c is not None:
    print(c.id, c.username,  c.name, c.surname, c.password)
else:
    print(f"User with username: {user_username} and password: {user_password} doesn't exist")

def insertUser(user):
    conn = psycopg2.connect(**conn_params)
    # Параметры подключения к базе данных
    
    # Создание курсора для выполнения операций с базой данных
    cur = conn.cursor()
    
    # SQL-запрос для вставки нового пользователя
    insert_query = f"""
        INSERT INTO users (username, name, surname, password)
        VALUES ('{user.username}', '{user.name}', '{user.surname}', '{user.password}');
    """
    
    # Выполнение запроса
    cur.execute(insert_query)
    
    # Подтверждение изменений
    conn.commit()
    
    # Закрытие курсора и соединения
    cur.close()
    conn.close()



def getUserByUsername(current_username):
    conn = psycopg2.connect(**conn_params)
    
    # Create a cursor object
    cur = conn.cursor()
    
    # Execute a query to select all users
    cur.execute(f"SELECT * FROM users WHERE username = '{current_username}'")
    
    # Fetch all rows from the executed query
    user = cur.fetchone()

    # Close the cursor and connection
    cur.close()
    conn.close()

    if user == None:
        return None

    return User(user[0], user[1], user[2], user[3], user[4], user[5])
    