import psycopg2
from config import getDbConfig

class Invitation:
    def __init__(self, name, event_id, with_spouse, hash, is_male, accepted=None, id=None, comments=None, attendee_count=0):
        self.name = name
        self.event_id = event_id
        self.with_spouse = with_spouse
        self.hash = hash
        self.is_male = is_male
        self.accepted = accepted
        self.id = id
        self.comments = comments
        self.attendee_count = attendee_count

conn_params = getDbConfig()

def debug_table_structure():
    """Выводит в консоль информацию о структуре таблицы invitation."""
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                # Получаем информацию о столбцах
                cur.execute("""
                    SELECT column_name, data_type, ordinal_position 
                    FROM information_schema.columns 
                    WHERE table_name = 'invitation' 
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print("\n=== ТАБЛИЦА INVITATION - СТРУКТУРА ===")
                for col in columns:
                    print(f"Позиция {col[2]}: {col[0]} ({col[1]})")
                print("======================================\n")
                
                # Получаем пример данных
                cur.execute("SELECT * FROM invitation LIMIT 1;")
                sample = cur.fetchone()
                if sample:
                    print("=== ПРИМЕР ДАННЫХ ===")
                    for i, col in enumerate(columns):
                        if i < len(sample):
                            print(f"{col[0]}: {sample[i]}")
                    print("=====================\n")
    except Exception as e:
        print(f"Error in debug_table_structure: {e}")

# Вызываем эту функцию для отладки
debug_table_structure()

def getInvitationByHash(hash):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM invitation WHERE hash = '{hash}'")
            invitation = cur.fetchone()
            
            if invitation is None:
                return None
            
            return constructInv(invitation)    

def createInvitation(invitation):
    try:
        # Обработка комментариев: если None или пусто, то SQL NULL
        comments_value = f"'{invitation.comments}'" if invitation.comments else "NULL"
        
        # Правильные булевы значения для PostgreSQL
        with_spouse_value = 'true' if invitation.with_spouse else 'false'
        is_male_value = 'true' if invitation.is_male else 'false'
        
        insert_query = f"""
            INSERT INTO invitation (name, event_id, with_spouse, hash, is_male, comments, attendee_count)
            VALUES ('{invitation.name}', {invitation.event_id}, {with_spouse_value}, 
                    '{invitation.hash}', {is_male_value}, 
                    {comments_value}, 
                    {invitation.attendee_count});
        """
        
        print(f"Debug - Executing SQL: {insert_query}")
        
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(insert_query)
                conn.commit()
        return True
    except Exception as e:
        print(f"Error in createInvitation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def constructInv(dbRes):
    # Отладочная информация
    print(f"Debug - DB result length: {len(dbRes)}")
    print(f"Debug - DB result columns: {dbRes}")
    
    # Проверка порядка столбцов
    print("Debug - Constructing invitation from DB result:")
    for i, val in enumerate(dbRes):
        print(f"  Column {i}: {val}")
    
    # Зададим значения по умолчанию
    id = None
    name = None
    event_id = None
    with_spouse = False
    hash_val = None
    accepted = None
    is_male = False
    comments = None
    attendee_count = 0
    
    # Определяем по результатам debug_table_structure, 
    # какой столбец какому полю соответствует
    id = dbRes[0]
    name = dbRes[1]
    event_id = dbRes[2]
    with_spouse = dbRes[3]
    hash_val = dbRes[4]
    accepted = dbRes[5]
    comments = dbRes[6] if len(dbRes) > 6 else None
    attendee_count = dbRes[7] if len(dbRes) > 7 and dbRes[7] is not None else 0
    is_male = dbRes[8] if len(dbRes) > 8 else False
    
    print(f"Debug - Assigning fields: id={id}, name={name}, comments={comments}, attendee_count={attendee_count}, is_male={is_male}")
    # Создаем объект приглашения с явным указанием всех параметров
    invitation = Invitation(
        name=name,
        event_id=event_id,
        with_spouse=with_spouse,
        hash=hash_val,
        is_male=is_male,
        accepted=accepted,
        id=id,
        comments=comments,
        attendee_count=attendee_count
    )
    print(f"Debug - Created invitation object with comments: {invitation.comments}, attendee_count: {invitation.attendee_count}")
   
    return invitation

def getInvitationById(invitation_id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM invitation WHERE id = {invitation_id}")
            invitation = cur.fetchone()
            
            if invitation is None:
                return None
            
            return constructInv(invitation)

def getInvitationsListByEventId(event_id):
    invitationlist = []
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                # Выводим схему таблицы для проверки наличия столбцов
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'invitation' 
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print(f"Debug - Table columns: {[col[0] for col in columns]}")
                
                # Теперь получаем данные приглашений
                cur.execute(f"SELECT * FROM invitation WHERE event_id = {event_id}")
                invitations = cur.fetchall()
                
                for invitation in invitations:
                    a = constructInv(invitation)
                    invitationlist.append(a)
                    
        return invitationlist
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return []  # Return empty list on error

def deleteInvitation(id):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            delete_query = f"DELETE FROM invitation WHERE id = {id}"
            cur.execute(delete_query)
            conn.commit()

def updateInvitation(invitation):
    # Правильная обработка значения NULL для accepted
    accepted_value = f"{invitation.accepted}" if invitation.accepted is not None else "NULL"
    
    # Правильная обработка значения NULL для комментариев
    comments_value = f"'{invitation.comments}'" if invitation.comments else "NULL"
    
    # Правильные булевы значения для PostgreSQL
    with_spouse_value = 'true' if invitation.with_spouse else 'false'
    is_male_value = 'true' if invitation.is_male else 'false'
    
    update_query = f"""
        UPDATE invitation SET 
            name = '{invitation.name}', 
            event_id = {invitation.event_id},
            with_spouse = {with_spouse_value},  
            accepted = {accepted_value},
            hash = '{invitation.hash}', 
            is_male = {is_male_value},
            comments = {comments_value},
            attendee_count = {invitation.attendee_count}
        WHERE id = {invitation.id};
    """
    
    print(f"Debug - Executing update SQL: {update_query}")

    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute(update_query)
            conn.commit()

# Function to add the new columns if they don't exist
def ensure_new_columns_exist():
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            # Check if the columns exist
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'invitation' AND column_name = 'comments';
            """)
            comments_exists = cur.fetchone() is not None
            
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'invitation' AND column_name = 'attendee_count';
            """)
            attendee_count_exists = cur.fetchone() is not None
            
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'invitation' AND column_name = 'is_male';
            """)
            is_male_exists = cur.fetchone() is not None
            
            # Add columns if they don't exist
            if not comments_exists:
                cur.execute("ALTER TABLE invitation ADD COLUMN comments TEXT;")
                print("Added 'comments' column to invitation table")
                
            if not attendee_count_exists:
                cur.execute("ALTER TABLE invitation ADD COLUMN attendee_count INTEGER DEFAULT 0;")
                print("Added 'attendee_count' column to invitation table")
                
            if not is_male_exists:
                cur.execute("ALTER TABLE invitation ADD COLUMN is_male BOOLEAN;")
                print("Added 'is_male' column to invitation table")
                
            conn.commit()

# Call this function when the application starts
ensure_new_columns_exist()