import datetime
import psycopg2

class Event:
    def __init__(self, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted = False, id = None):
        self.internal_name = internal_name
        self.template_id = template_id
        self.user_id = user_id
        self.date = date
        self.address_country = address_country
        self.address_city = address_city
        self.address_line = address_line
        self.display_name = display_name
        self.hall_name = hall_name
        self.unique_domain = unique_domain
        self.is_deleted = is_deleted
        self.id = id

conn_params = {
    'dbname': 'test',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def createEvent(event):
    insert_query = f"""
        INSERT INTO events (internal_name, template_id, user_id, date, 
        address_country, address_city, address_line, display_name, hall_name, unique_domain)
        VALUES ('{event.internal_name}', {event.template_id}, {event.user_id}, 
        '{event.date}', '{event.address_country}', '{event.address_city}', 
        '{event.address_line}', '{event.display_name}', '{event.hall_name}', '{event.unique_domain}');
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(insert_query)
            conn.commit()

def updateEvent(event):
    update_query = f"""
        UPDATE events SET internal_name = '{event.internal_name}', 
        template_id = '{event.template_id}', user_id = {event.user_id}, 
        date = '{event.date}', address_country = '{event.address_country}',
        address_city = '{event.address_city}', address_line = '{event.address_line}',
        display_name = '{event.display_name}', hall_name = '{event.hall_name}',
        unique_domain = '{event.unique_domain}' WHERE id = {event.id};
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(update_query)
            conn.commit()

def getEventById(id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM events WHERE id = {id} AND is_deleted = False")
            site = cur.fetchone()

            if site is None:
                return None

            return Event(site[1], site[2], site[3], site[4], site[5], site[6], site[7], site[8], site[9], site[10], site[0])

def getEventByUserId(user_id):
    events = []

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND is_deleted = False")
            sites = cur.fetchall()

            if sites is None:
                return None

            for site in sites:
                event = Event(site[1], site[2], site[3], site[4], site[5], site[6], site[7], site[8], site[9], site[10], site[11], site[0])
                events.append(event)

    return events

a = getEventByUserId(user_id = 11)
print(a[1].id)

def deleteEvent(id):
    delete_query = f"UPDATE events SET is_deleted = TRUE WHERE id = {id};"

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(delete_query)
            conn.commit()
