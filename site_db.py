import datetime
import psycopg2

class Website:
    def __init__(self, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, id = None):
        self.id = id
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



conn_params = {
    'dbname': 'test',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def create_site(websites):
    conn = psycopg2.connect(**conn_params)

    cur = conn.cursor()
    
    insert_query = f"""
        INSERT INTO websites (internal_name, 
        template_id, user_id, date, 
        address_country, address_city, 
        address_line, display_name, 
        hall_name, unique_domain)
        VALUES ('{websites.internal_name}', 
        {websites.template_id}, {websites.user_id}, 
        '{websites.date}', '{websites.address_country}', 
        '{websites.address_city}', '{websites.address_line}', 
        '{websites.display_name}', '{websites.hall_name}', '{websites.unique_domain}');
    """
    
    print(websites.date)

    cur.execute(insert_query)
    
    conn.commit()

    cur.close()
    conn.close()


site = Website('example_internal_name4', 1, 1001, datetime.datetime(2021, 11, 16, 11, 24, 13), 'Armenia', 'Erevan', '123 Main St.', 'Example Site2', 'Main Hall', 'example.com4')
create_site(site)


def update_website(site):
    conn = psycopg2.connect(**conn_params)
    
    cur = conn.cursor()

    insert_query = f"""
        UPDATE websites SET internal_name = {site.id}, '{site.internal_name}', 
        template_id = '{site.template_id}', user_id = '{site.user_id}', 
        date = '{site.date}', address_country = '{site.address_country}',
        address_city = '{site.address_city}', address_line = '{site.address_line}',
        display_name = '{site.display_name}', hall_name = '{site.hall_name}',
        unique_domain = '{site.unique_domain}' WHERE id = {site.id};
    """
    
    cur.execute(insert_query)
    
    conn.commit()
    
    cur.close()
    conn.close()

#site = SiteDb('example_internal_name', 1, 1001, '2024-09-03', 'Armenia', 'Erevan', '123 Main St.', 'Example Site', 'Main Hall', 'example.com', id = 2)
#update_website(site)


def get_site_by_id(id):
    conn = psycopg2.connect(**conn_params)
    
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM websites WHERE id = {id}")
    
    site = cur.fetchone()

    if site is None:
        return None

    a = Website(site[0], site[1], site[2], site[3], site[4], site[5], site[6], site[7], site[8], site[9], site[10])
    return a

e = get_site_by_id(id = 7)
print(e.address_city, e.address_country, e.date)

def get_sites_by_user_id(user_id):
    l = []

    conn = psycopg2.connect(**conn_params)
    
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM websites WHERE user_id = {user_id}")
    
    sites = cur.fetchall()

    if sites is None:
        return None
    
    for site in sites:
        a = Website(site[0], site[1], site[2], site[3], site[4], site[5], site[6], site[7], site[8], site[9], site[10])
        l.append(a)
    return l

#e = get_sites_by_user_id(user_id = 1001)
#print(e[1])