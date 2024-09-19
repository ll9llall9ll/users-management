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
    insert_query = f"""
        INSERT INTO templates (displayname, viewname, type)
        VALUES ('{template.displayname}', '{template.viewname}', '{template.type}');
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(insert_query)
            conn.commit()

template = TemplateDB('', 'Update_template2', 'Samplevew3', 'TypeB')
create_template(template)

def get_template_by_id(id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM templates WHERE id = {id}")
            template = cur.fetchone()

            if template is None:
                return None

            return TemplateDB(template[0], template[1], template[2], template[3])

# e = get_template_by_id(id=1)
# print(e.id, e.displayname, e.viewname, e.type)

def update_template(template):
    update_query = f"""
        UPDATE templates SET displayname = '{template.displayname}', 
        viewname = '{template.viewname}', type = '{template.type}'
        WHERE id = {template.id};
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(update_query)
            conn.commit()

# template = TemplateDB(1, 'Updated Template', 'SampleView2', 'TypeA')
# update_template(template)

def get_all_templates():
    templates_list = []
    
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM templates;")
            templates = cur.fetchall()

            for template in templates:
                templates_list.append(TemplateDB(template[0], template[1], template[2], template[3]))

    return templates_list

# templates = get_all_templates()
# for template in templates:
#     print(template.id, template.displayname, template.viewname, template.type)
