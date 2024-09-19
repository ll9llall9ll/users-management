import psycopg2

class Invitation:
    def __init__(self, id, name, event_id, with_spouce, accepted):
        self.id = id
        self.name = name
        self.event_id = event_id
        self.with_spouce = with_spouce
        self.accepted = accepted

conn_params = {
    'dbname': 'test',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def getInvitationById(invitation_id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM invitation WHERE id = {invitation_id}")
            invitation = cur.fetchone()
            
            if invitation is None:
                return None
            
            return Invitation(invitation[0], invitation[1], invitation[2], invitation[3], invitation[4], invitation[5])

def getInvitationsList():
    invitationlist = []
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM invitation")
                invitations = cur.fetchall()
                
                for invitation in invitations:
                    a = Invitation(invitation[0], invitation[1], invitation[2], invitation[3], invitation[4], invitation[5])
                    invitationlist.append(a)
                    
        return invitationlist
    except Exception as e:
        print(f"An error occurred: {e}")

def deleteInvitation(id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            delete_query = f"DELETE FROM invitation WHERE id = '{id}'"
            cur.execute(delete_query)
            conn.commit()
