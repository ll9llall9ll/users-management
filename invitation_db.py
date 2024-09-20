import psycopg2

from config import getDbConfig

class Invitation:
    def __init__(self, name, event_id, with_spouse, hash, accepted = None, id = None):
        self.name = name
        self.event_id = event_id
        self.with_spouse = with_spouse
        self.hash = hash
        self.accepted = accepted
        self.id = id

conn_params = getDbConfig()

def getInvitationByHash(hash):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM invitation WHERE hash = '{hash}'")
            invitation = cur.fetchone()
            
            if invitation is None:
                return None
            
            return constructInv(invitation)    

def createInvitation(invitation):
    insert_query = f"""
        INSERT INTO invitation (name, event_id, with_spouse, hash)
        VALUES ('{invitation.name}', {invitation.event_id}, {invitation.with_spouse}, '{invitation.hash}');
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(insert_query)
            conn.commit()

def constructInv(dbRes):
    return Invitation(dbRes[1], dbRes[2], dbRes[3], dbRes[4], dbRes[5], dbRes[0])

def getInvitationById(invitation_id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM invitation WHERE id = {invitation_id}")
            invitation = cur.fetchone()
            
            if invitation is None:
                return None
            
            return constructInv(invitation)

def getInvitationsList(event_id):
    invitationlist = []
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM invitation where event_id = {event_id}")
                invitations = cur.fetchall()
                
                for invitation in invitations:
                    a = constructInv(invitation)
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

def updateInvitation(invitation):
    update_query = f"""
        UPDATE invitation SET name = '{invitation.name}', 
            event_id = '{invitation.event_id}', 
            with_spouse = {invitation.with_spouse}, 
            accepted = {invitation.accepted},
            hash = '{invitation.hash}'
        WHERE id = {invitation.id};
    """

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(update_query)
            conn.commit()