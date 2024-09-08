import psycopg2

class TemplateDB:
    def __init__(self, id, displayname, viewname, type):
        self.id = id
        self.displayname = displayname
        self.viewname = viewname
        self.type = type

conn_params = {
    'dbname': 'test',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def create_template(template):
    conn = psycopg2.connect(**conn_params)

    cur = conn.cursor()
    
    insert_query = f"""
        INSERT INTO templates ( displayname, viewname, type)
        VALUES ('{template.displayname}', '{template.viewname}', '{template.type}');
    """
    
    cur.execute(insert_query)
    
    conn.commit()

    cur.close()
    conn.close()

template = TemplateDB('', 'Update_template2', 'Samplevew3', 'TypeB')
create_template(template)

def get_template_by_id(id):
    conn = psycopg2.connect(**conn_params)
    
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM templates WHERE id = {id}")
    
    template = cur.fetchone()

    if template is None:
        return None

    a = TemplateDB(template[0], template[1], template[2], template[3])
    return a   

#e = get_template_by_id(id = 1)
#print(e.id, e.displayname, e.viewname, e.type)

def update_template(template):
    conn = psycopg2.connect(**conn_params)
    
    cur = conn.cursor()

    insert_query = f"""
        UPDATE templates SET displayname = '{template.displayname}', viewname = '{template.viewname}', 
        type = '{template.type}';
    """
    
    cur.execute(insert_query)
    
    conn.commit()
    
    cur.close()
    conn.close()

#template = TemplateDB('', 'Updated Template', 'SampleView2', 'TypeA')
#update_template(template)
     
def get_all_tamplates():
    l = []
    conn = psycopg2.connect(**conn_params)
    
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM templates;")
    
    templates = cur.fetchall()

    if templates is None:
        return None
    
    for template in templates:
        l.append(template)
    return l
        
print(get_all_tamplates())
        