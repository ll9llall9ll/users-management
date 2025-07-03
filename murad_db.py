import psycopg2
from config_prod import getDbConfig

class User:
    def __init__(self, id, username, name, surname, password, is_admin=False):
        self.id = id
        self.username = username
        self.name = name
        self.surname = surname
        self.password = password
        self.is_admin = is_admin

# Database connection parameters
conn_params = getDbConfig()

def getUserListFromDb():
    userlist = []
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users")
                users = cur.fetchall()

                for user in users:
                    a = User(user[0], user[1], user[2], user[3], user[4])
                    userlist.append(a)

        return userlist

    except Exception as e:
        print(f"An error occurred: {e}")

def getUserById(user_id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM users WHERE id = {user_id}")
            user = cur.fetchone()

            if user is None:
                return None

            return User(user[0], user[1], user[2], user[3], user[4], user[5])

def getUserByUsernameAndPassword(user_username, user_password):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM users WHERE username = '{user_username}' AND password = '{user_password}'")
            users = cur.fetchall()

            if len(users) == 0:
                return None

            return User(users[0][0], users[0][1], users[0][2], users[0][3], users[0][4], is_admin=users[0][5])

def insertUser(user):
    insert_query = f"""
        INSERT INTO users (username, name, surname, password, is_admin)
        VALUES ('{user.username}', '{user.name}', '{user.surname}', '{user.password}', '{user.is_admin}');
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(insert_query)
            conn.commit()

def getUserByUsername(current_username):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM users WHERE username = '{current_username}'")
            user = cur.fetchone()

            if user is None:
                return None

            return User(user[0], user[1], user[2], user[3], user[4], user[5])

def editUser(user):
    update_query = f"""
        UPDATE users SET name = '{user.name}', surname = '{user.surname}', password = '{user.password}' WHERE id = '{user.id}';
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(update_query)
            conn.commit()

def deleteUser(user):
    delete_query = f"DELETE FROM users WHERE id = '{user.id}';"

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(delete_query)
            conn.commit()
