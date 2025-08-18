from flask import Flask, abort, render_template, request, redirect, url_for, session, jsonify
from db_extensions import executeQuery
from murad_db import getUserByUsernameAndPassword, insertUser, getUserById, User, editUser, deleteUser, getUserListFromDb, getUserByUsername
from event_db import Event, createEvent, getEventByUserId, updateEvent, getEventById, deleteEvent
from datetime import datetime
from template_db import get_template_by_id , TemplateDB, create_template_with_id , get_all_templates
from invitation_db import Invitation, createInvitation, getInvitationByHash, getInvitationById, updateInvitation, getInvitationsListByEventId, deleteInvitation
import hashlib
import time
import random
import string

class AppData:
    def __init__(self):
        self.IsLoggedIn = False
        self.loggedInuserId = None 
       
    def change_password(self, new_password):
        self.password = new_password

def check_password(password: str) -> str:
    if len(password) < 8:
        return "Password is too short. It should be at least 8 characters long."
    
    has_number = False
    has_symbol = False
    has_upper = False
    special_characters = '.,:;!?}''()[]{<>+=-*%/$^|@#&_~`'

    for char in password:
        if char.isdigit():
            has_number = True
        if char in special_characters:
            has_symbol = True
        if char.isupper():
            has_upper = True

    if not has_number:
        return "Password should contain at least one number."
    if not has_symbol:
        return "Password should contain at least one special character ('.,:;!?}''()[]{<>+=-*%/$^|@#&_~`')."
    if not has_upper:
        return "The password must contain at least one capital letter."
    return None 

app = Flask(__name__, static_folder='test')

def date(d):
     d.strftime("%d-%m-%y")
     return d
app.add_template_filter(date)

appData = AppData()

# Декоратор для проверки аутентификации
def require_auth(f):
    def decorated_function(*args, **kwargs):
        if not appData.IsLoggedIn:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Декоратор для проверки доступа к событию
# Использование:
# @require_event_access() - стандартная проверка event_id из JSON
# @require_event_access(get_event_by_invitation) - проверка через фабричную функцию
def require_event_access(event_factory=None):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            # Сначала проверяем аутентификацию
            if not appData.IsLoggedIn:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            # Если передана фабричная функция для события, используем её
            if event_factory:
                try:
                    event = event_factory()
                    if not event:
                        return jsonify({'success': False, 'error': 'Event not found'}), 404
                    
                    # Проверяем права доступа к событию
                    # В app.py у нас есть appData.loggedInuserId
                    # Можно добавить проверку, что пользователь является владельцем события
                    # Пока что просто проверяем, что событие существует
                    
                except Exception as e:
                    print(f"Error in event access check: {str(e)}")
                    return jsonify({'success': False, 'error': 'Event access validation failed'}), 400
            else:
                # Стандартная проверка event_id из JSON
                try:
                    data = request.get_json()
                    event_id = data.get('event_id')
                    
                    if not event_id:
                        return jsonify({'success': False, 'error': 'Event ID is required'}), 400
                    
                except Exception as e:
                    return jsonify({'success': False, 'error': 'Invalid request data'}), 400
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator


@app.route('/invite', methods = ['GET', 'POST'])
def invite():
    hash = request.args.get('h')
    invitation = getInvitationByHash(hash)
    if invitation.accepted == True:
        return render_template('invite_accepted4.html', msg = "Դուք ընդունել եք հրավերը, շնորհակալություն!"  )
    event = getEventById(invitation.event_id)
    template = get_template_by_id(event.template_id)
    if request.method == 'POST':
        accepted = request.form['action'] == 'accepted'
        
        # Получаем тип участия (attendance_type) если есть
        attendance_type = request.form.get('attendance_type', 'alone')
        
        # Определяем with_spouse на основе attendance_type
        with_spouse = attendance_type == 'with_partner'
        
        invitation.with_spouse = with_spouse
        invitation.accepted = accepted
        
        # Добавляем отладочную информацию
        print(f"Debug - App.py: accepted={accepted}, with_spouse={with_spouse}, attendance_type={attendance_type}")
        
        updateInvitation(invitation)
        returnMsg = "Դուք ընդունել եք հրավերը, շնորհակալություն!" if accepted else "Ցավում ենք, որ չեք կարողանա միանալ մեզ:"
        return render_template('invite_accepted4.html',  msg = returnMsg  )
    
    return render_template(template.viewname, invitation = invitation, event = event)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/edit_user', methods = ['GET', 'POST'])
def edit_user():
    if  appData.IsLoggedIn == False or getUserById(appData.loggedInuserId).is_admin == False:
        abort(403)
    current_id = request.args.get('id')
    user_info = getUserById(current_id)
    if request.method == 'GET' and getUserById(appData.loggedInuserId).is_admin == True and appData.IsLoggedIn:
        return render_template('user.html', user = user_info, id = current_id) 
    elif request.method == 'POST' and getUserById(appData.loggedInuserId).is_admin == True and appData.IsLoggedIn:
        name = request.form['name']
        surname = request.form['surname']
        password = user_info.password
        user = User(current_id, '', name, surname, password, False) 
        editUser(user)
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        current_username = request.form['username']
        current_password = request.form['password']
        db_user = getUserByUsernameAndPassword(current_username, current_password)
        if db_user != None:
            appData.IsLoggedIn = True
            appData.loggedInuserId = db_user.id
            return redirect(url_for('profile'))
        else:
            error = "Invalid username or password"
    elif appData.IsLoggedIn:
        return redirect(url_for('profile'))
    return render_template('login.html', error=error)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not appData.IsLoggedIn:
        return redirect(url_for('login'))
    user = getUserById(appData.loggedInuserId)    
    if request.method == 'POST':
        user.name = request.form['name']
        user.surname = request.form['surname']  
        editUser(user)
    return render_template('profile.html', loggedInuserId = user.id, username=user.username, name=user.name, surname=user.surname, is_admin=user.is_admin)

@app.route('/view_users', methods=['GET', 'POST'])
def view_users():
    if  appData.IsLoggedIn == False or getUserById(appData.loggedInuserId).is_admin == False:
        abort(403)
    current_user = getUserById(appData.loggedInuserId)
    if not appData.IsLoggedIn or not current_user.is_admin:
        return redirect(url_for('login'))
    return render_template('view_users.html', users = getUserListFromDb())

@app.route('/admin_menu')
def admin_menu():
    if not appData.IsLoggedIn or not getUserById(appData.loggedInuserId).is_admin:
        return redirect(url_for('login'))
    return render_template('admin_menu.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    appData.IsLoggedIn = False
    appData.loggedInuserId = None
    return redirect(url_for('login'))

@app.route('/changePassword', methods=['GET', 'POST'])
def changepassword():
    if not appData.IsLoggedIn:
        return redirect(url_for('login'))
    error = None
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        repeat_new_password = request.form['repeat_new_password']
        password = getUserById(appData.loggedInuserId).password
        if current_password != password:
            error = "Wrong Password."
        elif  check_password(new_password) != None:
            error = check_password(new_password)
        elif repeat_new_password != new_password:
            error = 'incorrect Password Repetition'
        if error is None:
            user = getUserById(appData.loggedInuserId)
            user.password = new_password
            editUser(user)
            return redirect(url_for('profile'))
    return render_template('changepassword.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        current_username = request.form['new_username']
        password = request.form['new_password']
        repeat_password = request.form['repeat_password']
        
        if getUserByUsername(current_username) != None:
            error = "Username already exists, please choose a different username."
        elif password != repeat_password:
            error = "Passwords do not match. Please try again."
        else:
            error = check_password(password)
            if error is None:
                user = User('', current_username, '', '', password, False)
                insertUser(user)
                return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/delete_user', methods=['GET'])
def delete_user():
    if  appData.IsLoggedIn == False or getUserById(appData.loggedInuserId).is_admin == False:
        abort(403)
    current_id = request.args.get('id')
    if getUserById(appData.loggedInuserId).is_admin == True and appData.IsLoggedIn:
        user = User(current_id, '', '', '', '', False) 
        deleteUser(user)
        return redirect(url_for('view_users'))
    return redirect(url_for('login'))

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if appData.IsLoggedIn and request.method == 'GET':
        templates = get_all_templates()
        return render_template('choose_a_template.html', templates=templates)
    elif appData.IsLoggedIn and request.method == 'POST':
        template_id = request.form.get('template_id')
        if template_id:
            return redirect(url_for('create_event_by_template_id', template_id=template_id))
    return redirect(url_for('login'))


@app.route('/create_event_by_template_id', methods=['GET', 'POST'])
def create_event_by_template_id():
    try:
        if not appData.IsLoggedIn:
            return redirect(url_for('login'))
        
        if request.method == 'GET':
            template_id = request.args.get('template_id')
            if not template_id:
                return "Template ID not provided!", 400 
            return render_template('create_event_by_template_id.html', template_id=template_id)
        
        if request.method == 'POST':  
            internal_name = request.form.get('internal_name')
            template_id = request.form.get('template_id')
            user_id = appData.loggedInuserId
            date = request.form.get('date')
            address_country = request.form.get('address_country')
            address_city = request.form.get('address_city')
            address_line = request.form.get('address_line')
            display_name = request.form.get('display_name')
            hall_name = request.form.get('hall_name')
            unique_domain = request.form.get('unique_domain')
            if not internal_name:
                return "Internal name is missing!", 400
            if not template_id:
                return "Template ID is missing!", 400
            if not date:
                return "Event date is missing!", 400
            
            try:
                date_format = '%Y-%m-%dT%H:%M'
                datetime_obj = datetime.strptime(date, date_format)
            except ValueError:
                return "Invalid date format!", 400
            
            event = Event(
                internal_name=internal_name, 
                template_id=template_id, 
                user_id=user_id, 
                date=datetime_obj, 
                address_country=address_country, 
                address_city=address_city, 
                address_line=address_line, 
                display_name=display_name, 
                hall_name=hall_name, 
                unique_domain=unique_domain
            )
            createEvent(event)
            return redirect(url_for('view_events'))
        return redirect(url_for('profile'))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred!", 500



@app.route('/view_events', methods = ['GET', 'POST'])
def view_events():
    if not appData.IsLoggedIn:
        return redirect(url_for('login'))
    user_id = appData.loggedInuserId
    if appData.IsLoggedIn and request.method == 'GET':
        return render_template('view_events.html', events = getEventByUserId(user_id))
        

@app.route('/edit_event', methods = ['GET', 'POST'])
def edit_event():
    id = request.args.get('id')
    event = getEventById(id)
    if appData.IsLoggedIn and request.method == 'GET':
        return render_template('edit_event.html', event = event)
    elif appData.IsLoggedIn and request.method == 'POST':    
        internal_name = request.form['internal_name']
        template_id = request.form['template_id']
        user_id = appData.loggedInuserId
        date = request.form['date']
        address_country = request.form['address_country']
        address_city = request.form['address_city']
        address_line = request.form['address_line']
        display_name = request.form['display_name']
        hall_name = request.form['hall_name']
        unique_domain = request.form['unique_domain']
        date_string = date
        date_format = '%Y-%m-%dT%H:%M'
        datetime_obj = datetime.strptime(date_string, date_format)
        event = Event(internal_name, template_id, user_id, datetime_obj, address_country, address_city, address_line, display_name, hall_name, unique_domain, id = id)
        updateEvent(event)
        return redirect(url_for('view_events'))
    return redirect(url_for('login'))

@app.route('/delete_event', methods = ['GET', 'POST'])
def delete_event(): 
    id = request.args.get('id')
    if appData.IsLoggedIn:
        deleteEvent(id)
        return redirect(url_for('view_events'))
    return redirect(url_for('login'))

@app.route('/create_invitation', methods=['GET', 'POST'])
def create_invitation():
    if appData.IsLoggedIn:
        event_id = request.args.get('event_id')  
        if request.method == 'GET':
            event = getEventByUserId(appData.loggedInuserId)
            return render_template('create_invitation.html', event=event, event_id=event_id)
        elif request.method == 'POST':
            name = request.form['name']
            hash = request.form['hash']
            with_spouse = request.form['with_spouse']
            is_male = request.form['is_male']
            guest_nickname = request.form.get('guest_nickname', '').strip() or None
            invitation = Invitation(name, event_id, with_spouse, hash, is_male, guest_nickname=guest_nickname)
            createInvitation(invitation)
            return redirect(url_for('view_invitation', event_id=event_id))
    return redirect(url_for('login'))


@app.route('/edit_invitation', methods = ['GET', 'POST'])
def edit_invitation():
    id = request.args.get('id')
    invitation = getInvitationById(id)
    if appData.IsLoggedIn and request.method == 'GET':
        return render_template('edit_invitation.html', invitation = invitation)
    elif appData.IsLoggedIn and request.method == 'POST':
        name = request.form['name']
        hash = request.form['hash']
        event_id = request.form['event_id']
        with_spouse = request.form['with_spouse']
        accepted = request.form['accepted']
        is_male = request.form['is_male']
        guest_nickname = request.form.get('guest_nickname', '').strip() or None
        invitation = Invitation(name, event_id, with_spouse, hash, is_male, accepted, id, guest_nickname=guest_nickname)
        updateInvitation(invitation)
        return redirect(url_for('view_invitation', event_id = event_id))
    return redirect(url_for('login'))

@app.route('/delete_invitation', methods = ['GET', 'POST'])
def delete_invitation():
    id = request.args.get('id')
    if appData.IsLoggedIn:
        deleteInvitation(id)
        return redirect(url_for('view_events'))
    return redirect(url_for('login'))


@app.route('/view_invitation', methods=['GET', 'POST'])
def view_invitation():
    event_id = request.args.get('event_id')
    invitations = getInvitationsListByEventId(event_id)
    if appData.IsLoggedIn:
        return render_template('view_invitations.html', invitations=invitations, event_id=event_id)
    return redirect(url_for('login'))


# Фабричная функция для получения события по invitation_id
def get_event_by_invitation():
    try:
        data = request.get_json()
        invitation_id = data.get('invitation_id')
        
        if not invitation_id:
            return None
        
        invitation = getInvitationById(invitation_id)
        if not invitation:
            return None
        
        event = getEventById(invitation.event_id)
        return event
    except Exception as e:
        print(f"Error getting event by invitation: {str(e)}")
        return None

@app.route('/api/update_gender', methods=['POST'])
@require_event_access(get_event_by_invitation)
def update_gender():
    try:
        data = request.get_json()
        invitation_id = data.get('invitation_id')
        is_male = data.get('is_male')
        
        if invitation_id is None or is_male is None:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
        # Получаем приглашение из базы данных
        invitation = getInvitationById(invitation_id)
        if not invitation:
            return jsonify({'success': False, 'error': 'Invitation not found'}), 404
        
        # Обновляем пол
        invitation.is_male = is_male
        
        # Сохраняем изменения в базу данных
        updateInvitation(invitation)
        
        return jsonify({'success': True, 'message': 'Gender updated successfully'})
        
    except Exception as e:
        print(f"Error updating gender: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# Фабричная функция для получения события по event_id
def get_event_by_id():
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        
        if not event_id:
            return None
        
        event = getEventById(event_id)
        return event
    except Exception as e:
        print(f"Error getting event by ID: {str(e)}")
        return None

@app.route('/api/import_csv_guests', methods=['POST'])
@require_event_access(get_event_by_id)
def import_csv_guests():
    try:
        print("=== CSV Import Debug ===")
        data = request.get_json()
        print(f"Received data keys: {list(data.keys()) if data else 'None'}")
        
        event_id = data.get('event_id')
        csv_data = data.get('csv_data')
        language = data.get('language', 'ru')
        
        print(f"Event ID: {event_id}")
        print(f"CSV data length: {len(csv_data) if csv_data else 0}")
        print(f"Language: {language}")
        
        if not event_id:
            return jsonify({'success': False, 'error': 'Event ID is required'}), 400
        
        if not csv_data:
            return jsonify({'success': False, 'error': 'CSV data is required'}), 400
        
        # Проверяем размер данных (примерно 10MB)
        if len(csv_data.encode('utf-8')) > 10 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'CSV file is too large (max 10MB)'}), 400
        
        # Парсим CSV данные
        lines = csv_data.strip().split('\n')
        print(f"Total lines in CSV: {len(lines)}")
        print(f"First line: {lines[0] if lines else 'None'}")
        
        if len(lines) < 2:  # Нужна как минимум заголовок и одна строка данных
            return jsonify({'success': False, 'error': 'CSV file is empty or invalid'}), 400
        
        # Проверяем количество строк (максимум 1000)
        if len(lines) > 1001:  # +1 для заголовка
            return jsonify({'success': False, 'error': 'CSV file has too many rows (max 1000)'}), 400
        
        # Проверяем заголовок
        header = lines[0].strip().split(',')
        print(f"Header parts: {header}")
        print(f"Header length: {len(header)}")
        
        if len(header) < 3:
            return jsonify({'success': False, 'error': 'CSV header must have at least 3 columns: Сторона, Имя гостя, Имя Гостя в приглашении'}), 400
        
        # Пропускаем заголовок (первую строку)
        data_lines = lines[1:]
        print(f"Data lines count: {len(data_lines)}")
        
        imported_count = 0
        errors = []
        processed_names = set()  # Для отслеживания дубликатов
        
        for line_num, line in enumerate(data_lines, start=2):  # Начинаем с 2, так как первая строка - заголовок
            try:
                print(f"Processing line {line_num}: {line}")
                
                # Разделяем строку по запятой, учитывая кавычки
                parts = []
                current_part = ""
                in_quotes = False
                
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        parts.append(current_part.strip())
                        current_part = ""
                    else:
                        current_part += char
                
                # Добавляем последнюю часть
                parts.append(current_part.strip())
                
                # Очищаем кавычки из всех частей
                parts = [part.strip('"').strip() for part in parts]
                print(f"Parsed parts: {parts}")
                
                # Проверяем, что у нас есть нужные колонки
                if len(parts) < 3:
                    print(f"Error: insufficient columns in line {line_num}")
                    errors.append(f"Строка {line_num}: недостаточно колонок (нужно 3, получено {len(parts)})")
                    continue
                
                # Извлекаем данные
                # parts[0] - "Сторона" (игнорируем)
                guest_nickname = parts[1]  # "Имя гостя"
                guest_name = parts[2]      # "Имя Гостя в приглашении"
                
                # Проверяем, что данные не пустые
                if not guest_name:
                    errors.append(f"Строка {line_num}: пустое имя гостя")
                    continue
                
                # Проверяем на дубликаты
                if guest_name in processed_names:
                    errors.append(f"Строка {line_num}: дубликат имени '{guest_name}'")
                    continue
                
                processed_names.add(guest_name)
                
                # Генерируем хеш для приглашения
                hash_value = generate_guest_hash(guest_name, event_id)
                
                # Определяем пол по имени (используем простую логику)
                is_male = detect_gender_by_name(guest_name)
                
                # Создаем приглашение
                invitation = Invitation(
                    name=guest_name,
                    event_id=event_id,
                    with_spouse=False,  # По умолчанию False
                    hash=hash_value,
                    is_male=is_male,
                    accepted=None,  # По умолчанию None (ожидает ответа)
                    guest_nickname=guest_nickname if guest_nickname else None
                )
                
                print(f"Created invitation: name={guest_name}, nickname={guest_nickname}, is_male={is_male}")
                
                # Сохраняем в базу данных
                try:
                    if createInvitation(invitation):
                        imported_count += 1
                        print(f"Successfully imported invitation {imported_count}")
                    else:
                        print(f"Failed to save invitation to database")
                        errors.append(f"Строка {line_num}: ошибка сохранения в базу данных")
                except Exception as db_error:
                    print(f"Database error: {str(db_error)}")
                    errors.append(f"Строка {line_num}: ошибка базы данных - {str(db_error)}")
                    
            except Exception as e:
                errors.append(f"Строка {line_num}: {str(e)}")
        
        print(f"Import completed. Imported: {imported_count}, Errors: {len(errors)}")
        
        # Формируем ответ
        response_data = {
            'success': True,
            'imported_count': imported_count,
            'total_lines': len(data_lines)
        }
        
        if errors:
            response_data['errors'] = errors[:10]  # Показываем только первые 10 ошибок
            response_data['error_count'] = len(errors)
            print(f"First 10 errors: {errors[:10]}")
        
        print("=== CSV Import Debug End ===")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error importing CSV guests: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def detect_gender_by_name(name):
    """
    Улучшенная функция для определения пола по имени.
    Учитывает армянские и русские имена.
    """
    name_lower = name.lower()
    
    # Список женских армянских имен
    female_names = [
        'լիլիթ', 'մարիամ', 'սիրանուշ', 'անահիտ', 'հասմիկ', 'նարինե', 'արիանա', 'մարիա', 'սոնա', 'լիզա', 'կարինե',
        'հայկուհի', 'վարդուհի', 'սիրանույշ', 'անահիտ', 'լուսինե', 'գայանե', 'ռուզան', 'նունե', 'սիրանույշ', 'անահիտ', 'լուսինե',
        'անուշ', 'շուշան', 'հասմիկ', 'նունե', 'ռուզան', 'գայանե', 'սիրանույշ', 'անահիտ', 'լուսինե',
        'սոնա', 'լիզա', 'կարինե', 'հայկուհի', 'վարդուհի',
        # Русские женские имена
        'анна', 'мария', 'елена', 'наталья', 'ольга', 'ирина', 'татьяна', 'светлана', 'людмила', 'галина',
        # Армянские имена, написанные русскими буквами
        'анаит', 'лилит', 'мариам', 'сирануш', 'нарине', 'ариана', 'соня', 'лиза', 'карине',
        'гаяне', 'рузан', 'нуне', 'сирануйш', 'лусине', 'ани', 'галина',
        # Дополнительные армянские женские имена
        'աստղիկ', 'նաիրա', 'սեդա', 'լաուրա', 'դիանա', 'զարուհի', 'զեյնաբ', 'զեյնապ',
        'շողիկ', 'լուսիկ', 'վարդիկ', 'սիրիկ', 'անիկ', 'կարիկ', 'նարիկ', 'մարիկ'
    ]
    
    # Список мужских армянских имен
    male_names = [
        'վահան', 'հայկ', 'արամ', 'սարգիս', 'կարեն', 'ռոբերտ', 'դավիթ', 'մհեր', 'տիգրան', 'վահե', 'հրաչյա', 'սամվել', 'գագիկ', 'ռաֆիկ', 'վիգեն',
        # Русские мужские имена
        'михаил', 'александр', 'дмитрий', 'сергей', 'андрей', 'владимир', 'николай', 'игорь', 'алексей', 'михаил'
    ]
    
    # Проверяем точные совпадения
    if name_lower in female_names:
        return False  # Женский
    
    if name_lower in male_names:
        return True  # Мужской
    
    # Проверяем окончания
    # Женские окончания (армянские и русские)
    female_endings = ['ա', 'ե', 'ի', 'ու', 'а', 'я', 'ь']
    for ending in female_endings:
        if name_lower.endswith(ending):
            return False  # Женский
    
    # Мужские окончания (армянские)
    male_endings = ['ան', 'իկ', 'ուն', 'են', 'ին', 'ոն']
    for ending in male_endings:
        if name_lower.endswith(ending):
            return True  # Мужской
    
    # Если все правила не сработали - используем умное правило по умолчанию
    # Анализируем гласные - женские имена обычно содержат больше гласных
    vowels = name_lower.count('ա') + name_lower.count('ե') + name_lower.count('ը') + name_lower.count('ի') + name_lower.count('ո') + name_lower.count('ու') + name_lower.count('և') + name_lower.count('а') + name_lower.count('е') + name_lower.count('ё') + name_lower.count('и') + name_lower.count('о') + name_lower.count('у') + name_lower.count('ы') + name_lower.count('э') + name_lower.count('ю') + name_lower.count('я')
    vowel_ratio = vowels / len(name_lower)
    
    # Если больше 40% гласных - скорее всего женское
    if vowel_ratio > 0.4:
        return False  # Женский
    else:
        return True  # Мужской

@app.route('/api/export_accepted_guests', methods=['POST'])
@require_event_access(get_event_by_id)
def export_accepted_guests():
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        language = data.get('language', 'ru')  # По умолчанию русский
        
        if not event_id:
            return jsonify({'success': False, 'error': 'Event ID is required'}), 400
        
        # Получаем все приглашения для события
        invitations = getInvitationsListByEventId(event_id)
        
        # Фильтруем только принятые
        accepted_invitations = [inv for inv in invitations if inv.accepted == True]
        
        if not accepted_invitations:
            return jsonify({'success': False, 'error': 'No accepted invitations found'}), 404
        
        # Функция для определения пола по имени
        def detect_gender_by_name(name, is_male_from_db):
            if is_male_from_db is not None:
                return is_male_from_db
            
            name_lower = name.lower()
            
            # Список женских имен
            female_names = [
                'լիլիթ', 'մարիամ', 'սիրանուշ', 'անահիտ', 'հասմիկ', 'նարինե', 'արիանա', 'մարիա', 'սոնա', 'լիզա', 'կարինե',
                'հայկուհի', 'վարդուհի', 'սիրանույշ', 'անահիտ', 'լուսինե', 'գայանե', 'ռուզան', 'նունե',
                'անուշ', 'շուշան', 'նունե', 'ռուզան', 'գայանե', 'սիրանույշ', 'անահիտ', 'լուսինե',
                'սոնա', 'լիզա', 'կարինե', 'հայկուհի', 'վարդուհի',
                'анна', 'мария', 'елена', 'наталья', 'ольга', 'ирина', 'татьяна', 'светлана', 'людмила', 'галина',
                'анаит', 'лилит', 'мариам', 'сирануш', 'нарине', 'ариана', 'соня', 'лиза', 'карине',
                'гаяне', 'рузан', 'нуне', 'сирануйш', 'лусине', 'ани', 'галина',
                'աստղիկ', 'նաիրա', 'սեդա', 'լաուրա', 'դիանա', 'զարուհի', 'զեյնաբ', 'զեյնապ',
                'շողիկ', 'լուսիկ', 'վարդիկ', 'սիրիկ', 'անիկ', 'կարիկ', 'նարիկ', 'մարիկ'
            ]
            
            # Список мужских имен
            male_names = [
                'վահան', 'հայկ', 'արամ', 'սարգիս', 'կարեն', 'ռոբերտ', 'դավիթ', 'մհեր', 'տիգրան', 'վահե', 'հրաչյա', 'սամվել', 'գագիկ', 'ռաֆիկ', 'վիգեն',
                'михаил', 'александр', 'дмитрий', 'сергей', 'андрей', 'владимир', 'николай', 'игорь', 'алексей'
            ]
            
            if name_lower in female_names:
                return False
            if name_lower in male_names:
                return True
            
            # Проверяем окончания
            last_char = name[-1]
            if last_char in ['ա', 'е', 'ի', 'ու', 'а', 'я', 'ь']:
                return False
            if any(name.endswith(ending) for ending in ['ան', 'իկ', 'ուն', 'են', 'ին', 'ոն']):
                return True
            
            # Анализ гласных
            vowels = sum(1 for char in name if char.lower() in 'աեըիոուևаеёиоуыэюя')
            vowel_ratio = vowels / len(name)
            return vowel_ratio <= 0.4
        
        # Подготавливаем данные для экспорта
        export_data = {
            'event_id': event_id,
            'export_date': datetime.now().isoformat(),
            'export_language': language,
            'total_accepted': len(accepted_invitations),
            'total_attendees': sum(inv.attendee_count or 1 for inv in accepted_invitations),
            'guests': []
        }
        
        for invitation in accepted_invitations:
            # Используем флаг is_male из базы данных
            is_male = invitation.is_male
            
            if invitation.with_spouse:
                # Создаем умное имя для супруга/супруги
                if language == 'hy':
                    spouse_name = f"Կին {invitation.name}-ի" if is_male else f"Ամուսին {invitation.name}-ի"
                else:
                    spouse_name = f"Супруга {invitation.name}" if is_male else f"Супруг {invitation.name}"
                
                guest_data = {
                    'guest_name': invitation.name,
                    'second_guest': spouse_name,
                    'group_size': 2,
                    'group_description': '2 մարդ' if language == 'hy' else '2 человека',
                    'has_spouse': True,
                    'guest_gender': 'արական' if is_male else 'իգական' if language == 'hy' else 'мужской' if is_male else 'женский'
                }
            else:
                guest_data = {
                    'guest_name': invitation.name,
                    'second_guest': None,
                    'group_size': 1,
                    'group_description': '1 մարդ' if language == 'hy' else '1 человек',
                    'has_spouse': False,
                    'guest_gender': 'արական' if is_male else 'իգական' if language == 'hy' else 'мужской' if is_male else 'женский'
                }
            
            export_data['guests'].append(guest_data)
        
        return jsonify({
            'success': True,
            'data': export_data
        })
        
    except Exception as e:
        print(f"Error exporting accepted guests: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export_csv_guests_with_links', methods=['POST'])
@require_event_access(get_event_by_id)
def export_csv_guests_with_links():
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        language = data.get('language', 'ru')  # По умолчанию русский
        
        if not event_id:
            return jsonify({'success': False, 'error': 'Event ID is required'}), 400
        
        # Получаем все приглашения для события
        invitations = getInvitationsListByEventId(event_id)
        
        if not invitations:
            return jsonify({'success': False, 'error': 'No invitations found'}), 404
        
        # Создаем CSV данные
        import csv
        import io
        
        # Создаем StringIO объект для записи CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Записываем заголовок
        if language == 'hy':
            header = ['Կողմ', 'Հյուրի անուն', 'Հյուրի անուն հրավերում', 'Հյուրի հղում']
        else:
            header = ['Сторона', 'Имя гостя', 'Имя Гостя в приглашении', 'Ссылка гостя']
        
        writer.writerow(header)
        
        # Получаем базовый URL для генерации ссылок
        base_url = request.host_url.rstrip('/')
        
        # Записываем данные для каждого приглашения
        for invitation in invitations:
            # Генерируем ссылку для гостя
            guest_link = f"{base_url}/invite/{invitation.hash}"
            
            # Определяем сторону (по умолчанию "Гость")
            side = "Հյուր" if language == 'hy' else "Гость"
            
            # Используем guest_nickname если есть, иначе пустая строка
            guest_nickname = invitation.guest_nickname if invitation.guest_nickname else ""
            
            # Записываем строку данных
            row = [
                side,  # Сторона
                guest_nickname,  # Имя гостя (nickname)
                invitation.name,  # Имя Гостя в приглашении
                guest_link  # Ссылка гостя
            ]
            
            writer.writerow(row)
        
        # Получаем CSV данные как строку
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            'success': True,
            'csv_data': csv_data,
            'filename': f'guests_with_links_{event_id}.csv',
            'total_guests': len(invitations)
        })
        
    except Exception as e:
        print(f"Error exporting CSV guests with links: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    baloonTemplate = get_template_by_id(2)
    if baloonTemplate is None:
        create_template_with_id(TemplateDB(2, 'Baloons', 'baloons_template.html', 'birthday'))
    baloonTemplateRu = get_template_by_id(3)
    if baloonTemplateRu is None:
        create_template_with_id(TemplateDB(3, 'Baloons RU', 'baloons_template_ru.html', 'birthday'))
    widTemplate = get_template_by_id(4)
    if widTemplate is None:
        create_template_with_id(TemplateDB(4, 'Wid Template', 'wed_template.html', 'wedding')) 
    birdTemplate = get_template_by_id(5)
    if birdTemplate is None:
        create_template_with_id(TemplateDB(5, 'birdTemplate', 'bird_template.html', 'bird'))
        birdTemplate = get_template_by_id(5)
    pegasTemplate = get_template_by_id(6)
    if pegasTemplate is None:
        create_template_with_id(TemplateDB(6, 'pegasTemplate', 'pegas_template.html', 'Pegas'))
        birdTemplate = get_template_by_id(6)

    executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS is_male BOOLEAN;")
    app.run(debug=False)