from flask import Flask, abort, render_template, request, redirect, url_for, session, make_response
from db_extensions import executeQuery
from murad_db import getUserByUsername, insertUser, getUserById, User, editUser, deleteUser, getUserListFromDb
from event_db import Event, createEvent, getEventByUserId, updateEvent, getEventById, deleteEvent
from datetime import datetime, timedelta
from template_db import get_template_by_id, TemplateDB, create_template_with_id, get_all_templates
from invitation_db import Invitation, createInvitation, getInvitationByHash, getInvitationById, updateInvitation, getInvitationsListByEventId, deleteInvitation
import hashlib
import secrets
import uuid
import openai
from openai import OpenAI
import os
import tempfile
from flask import jsonify, request
from pydub import AudioSegment
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from config_prod import getOpenaiConfig
from config_prod import getFullConfig
# In-memory session storage
active_sessions = set()



def generate_session_id():
    return str(uuid.uuid4())

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

class AppData:
    def __init__(self):
        pass

def check_password(password: str) -> str:
    if len(password) < 8:
        return "Password is too short. It should be at least 8 characters long."
    
    has_number = False
    has_symbol = False
    has_upper = False
    special_characters = '.,:;!?}\'\'()[]{<>+=-*%/$^|@#&_~`'

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
        return "Password should contain at least one special character ('.,:;!?}\'\'()[]{<>+=-*%/$^|@#&_~`')."
    if not has_upper:
        return "The password must contain at least one capital letter."
    return None 

app = Flask(__name__, static_folder='test')
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key
CORS(app, resources={r"/login/google": {"origins": "*"}})
def date(d):
     str_date = d.strftime("%d-%m-%y")
     return str_date
app.add_template_filter(date)

appData = AppData()


GOOGLE_CLIENT_ID = getFullConfig()['google_oauth_config']['client_id'] 

# Хранилище сессий
active_sessions = set()

# Настройка клиента OpenAI с ключом API
client = OpenAI(api_key=getOpenaiConfig()['api_key'])

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        print("Transcribe API endpoint called")

        if 'audio' not in request.files:
            print("No audio file in request")
            return jsonify({'success': False, 'error': 'Аудиофайл не предоставлен'}), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            print("Empty audio filename")
            return jsonify({'success': False, 'error': 'Выбран пустой аудиофайл'}), 400

        print(f"Received audio file: {audio_file.filename}, Content-Type: {audio_file.content_type}")

        language = request.form.get('language', None)  # None = автоопределение
        print(f"Requested language: {language}")

        # Сохранение во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_filename = temp_file.name

        try:
            # Отправляем файл в OpenAI API через новый интерфейс
            with open(temp_filename, 'rb') as f:
                print("Sending file to OpenAI API")
                transcription = client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=f,    
                    language= language,
                   response_format="json"
                )

            print(f"Transcription successful. Text: {transcription.text[:50]}...")

            return jsonify({'success': True, 'text': transcription.text, 'language': language or 'auto'})

        except Exception as api_error:
            print(f"API Error: {api_error}")
            return jsonify({'success': False, 'error': str(api_error)}), 500

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    except Exception as e:
        print(f"Error in transcribe_audio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500




# Authentication middleware
@app.before_request
def check_session():
    print(f"Request endpoint: {request.endpoint}")  # Отладка
    # Skip for public routes or static assets
    if request.endpoint in ['login', 'register', 'invite', 'login_google', 'static'] or request.path.startswith('/static'):
        print(f"Skipping session check for endpoint: {request.endpoint}")  # Отладка
        return None

    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in active_sessions:
        print("No session found, redirecting to login")  # Отладка
        return redirect(url_for('login'))

    # Set user_id from session in the request for easy access
    user_id = request.cookies.get('user_id')
    request.user_id = user_id if user_id else None


@app.route('/invite', methods = ['GET', 'POST'])
def invite():
    hash = request.args.get('h')
    invitation = getInvitationByHash(hash)
    
    # Если уже есть ответ на приглашение, показываем соответствующую страницу
    if invitation.accepted is not None:
        event = getEventById(invitation.event_id)
        if invitation.accepted == True:
            return render_template('invite_accepted_new.html', 
                                 hall_name=event.hall_name or 'Նշված չէ', 
                                 event_date=event.date.strftime('%d.%m.%Y') if event.date else 'Նշված չէ')
        else:
            return render_template('invite_declined_new.html')
    
    # Если ответа еще нет, показываем форму приглашения
    event = getEventById(invitation.event_id)
    template = get_template_by_id(event.template_id)
    
    if request.method == 'POST':
        with_spouse = 'options' in request.form and request.form['options'] == 'with_spouse'
        accepted = request.form['action'] == 'accepted'
        
        # Получаем комментарии из формы - проверяем на None и empty string
        comments = request.form.get('comment', '')
        if not comments:  # Это проверит на None, пустую строку и строку с пробелами
            comments = None
        
        # Получаем количество гостей
        attendee_count = 0
        if accepted:
            try:
                attendee_count = int(request.form.get('attendees_count', 1))
                if attendee_count < 0:
                    attendee_count = 1
            except ValueError:
                attendee_count = 1
        
        # Обновляем объект приглашения
        invitation.with_spouse = with_spouse
        invitation.accepted = accepted
        invitation.comments = comments
        invitation.attendee_count = attendee_count
        
        # Отладочная информация
        print(f"Debug - Saving invitation with comments: '{invitation.comments}'")
        
        # Сохраняем в базу данных
        updateInvitation(invitation)
        
        # После сохранения показываем соответствующую страницу
        if accepted:
            return render_template('invite_accepted_new.html', 
                                 hall_name=event.hall_name or 'Նշված չէ', 
                                 event_date=event.date.strftime('%d.%m.%Y') if event.date else 'Նշված չէ')
        else:
            return render_template('invite_declined_new.html')
    
    return render_template(template.viewname, invitation = invitation, event = event)



# Новый маршрут для просмотра деталей приглашения
@app.route('/invitation_details', methods=['GET'])
def invitation_details():
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        invitation_id = request.args.get('id')
        if not invitation_id:
            return "Invitation ID not provided!", 400
            
        print(f"Debug - Looking for invitation with id: {invitation_id}")
        
        # Получаем приглашение и проверяем, что оно существует
        invitation = getInvitationById(invitation_id)
        if invitation is None:
            return f"Invitation with ID {invitation_id} not found!", 404
            
        print(f"Debug - Found invitation for: {invitation.name}")
        
        # Отладочная информация для комментариев
        print(f"Debug - Comments in invitation: '{invitation.comments}'")
        print(f"Debug - Comments type: {type(invitation.comments)}")
        
        # Получаем событие и проверяем, что оно существует
        event = getEventById(invitation.event_id)
        if event is None:
            return f"Event with ID {invitation.event_id} not found!", 404
            
        print(f"Debug - Found event: {event.display_name}")
        
        # Рендерим шаблон
        return render_template('invitation_details.html', invitation=invitation, event=event)
        
    except Exception as e:
        print(f"Error in invitation_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"An error occurred: {str(e)}", 500
    
    
# Обновленный маршрут редактирования приглашения
@app.route('/edit_invitation', methods = ['GET', 'POST'])
def edit_invitation():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    id = request.args.get('id')
    invitation = getInvitationById(id)
    
    if request.method == 'GET':
        return render_template('edit_invitation.html', invitation=invitation)
    elif request.method == 'POST':
        name = request.form['name']
        hash = request.form['hash']
        event_id = request.form['event_id']
        with_spouse = request.form['with_spouse'] == 'True'
        
        # Обработка значения accepted
        accepted_str = request.form.get('accepted')
        if accepted_str == 'NULL':
            accepted = None
        else:
            accepted = accepted_str == 'True'
            
        is_male = request.form['is_male'] == 'True'
        
        # Получаем комментарии - проверяем на пустую строку
        comments = request.form.get('comments', '')
        if not comments.strip():  # Если строка пуста после удаления пробелов
            comments = None
        
        # Получаем количество гостей
        try:
            attendee_count = int(request.form.get('attendee_count', 0))
            if attendee_count < 0:
                attendee_count = 0
        except ValueError:
            attendee_count = 0
            
        # Отладочная информация
        print(f"Debug - Updating invitation with comments: '{comments}'")
        
        # Создаем обновленный объект приглашения со всеми полями
        invitation = Invitation(name, event_id, with_spouse, hash, is_male, accepted, id, comments, attendee_count)
        
        # Сохраняем в базу данных
        updateInvitation(invitation)
        
        return redirect(url_for('view_invitation', event_id=event_id))
        
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/edit_user', methods = ['GET', 'POST'])
def edit_user():
    user_id = request.cookies.get('user_id')
    if not user_id or not getUserById(user_id).is_admin:
        abort(403)
    
    current_id = request.args.get('id')
    user_info = getUserById(current_id)
    
    if request.method == 'GET':
        return render_template('user.html', user = user_info, id = current_id) 
    elif request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        password = user_info.password
        user = User(current_id, '', name, surname, password, False) 
        editUser(user)
        return redirect(url_for('profile'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Проверка на Google-логин
        if request.form.get('google_login') == 'true':
            try:
                # Получаем токен из формы
                token = request.form.get('credential')
                
                if not token:
                    error = "Отсутствуют учетные данные Google"
                    return render_template('login.html', error=error)
                
                # Верификация токена
                idinfo = id_token.verify_oauth2_token(
                    token,
                    grequests.Request(),
                    GOOGLE_CLIENT_ID
                )
                
                # Извлечение информации о пользователе
                email = idinfo.get('email')
                name = idinfo.get('name', '')
                print(email)
                # Проверка существования пользователя
                user = getUserByUsername(email)
                if not user:
                    # Разделение имени на части
                    name_parts = name.split(' ', 1) if name else ['', '']
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    # Создание нового пользователя
                    new_user = User(
                        id='',
                        username=email,
                        name=first_name,
                        surname=last_name,
                        password='',  # Пустой пароль для Google-пользователей
                        is_admin=False
                    )
                    insertUser(new_user)
                    user = getUserByUsername(email)
                
                # Создание сессии
                session_id = generate_session_id()
                active_sessions.add(session_id)
                
                # Установка cookies
                response = make_response(redirect(url_for('view_events')))
                response.set_cookie('session_id', session_id, httponly=True, max_age=86400)
                response.set_cookie('user_id', str(user.id), httponly=True, max_age=86400)
                
                return response
            
            except ValueError as err:
                error = "Ошибка входа через Google"
                return render_template('login.html', error=error)
        
        # Стандартная авторизация по логину/паролю
        current_username = request.form['username']
        current_password = request.form['password']
        
        user = getUserByUsername(current_username)
        if user and verify_password(user.password, current_password):
            # Создание сессии
            session_id = generate_session_id()
            active_sessions.add(session_id)
            
            # Установка cookies
            response = make_response(redirect(url_for('view_events')))
            response.set_cookie('session_id', session_id, httponly=True, max_age=86400)
            response.set_cookie('user_id', str(user.id), httponly=True, max_age=86400)
            
            return response
        else:
            error = "Неверное имя пользователя или пароль"
    
    # Проверка существующей сессии
    session_id = request.cookies.get('session_id')
    if session_id and session_id in active_sessions:
        return redirect(url_for('view_events'))
        
    return render_template('login.html', error=error)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = getUserById(user_id)    
    if request.method == 'POST':
        user.name = request.form['name']
        user.surname = request.form['surname']  
        editUser(user)
    
    return render_template('profile.html', loggedInuserId=user.id, username=user.username, name=user.name, surname=user.surname, is_admin=user.is_admin)

@app.route('/view_users', methods=['GET', 'POST'])
def view_users():
    user_id = request.cookies.get('user_id')
    if not user_id or not getUserById(user_id).is_admin:
        abort(403)
        
    return render_template('view_users.html', users=getUserListFromDb())

@app.route('/admin_menu')
def admin_menu():
    user_id = request.cookies.get('user_id')
    if not user_id or not getUserById(user_id).is_admin:
        return redirect(url_for('login'))
        
    return render_template('admin_menu.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id and session_id in active_sessions:
        active_sessions.remove(session_id)
    
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_id')
    response.delete_cookie('user_id')
    
    return response

@app.route('/changePassword', methods=['GET', 'POST'])
def changepassword():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    error = None
    user = getUserById(user_id)
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        repeat_new_password = request.form['repeat_new_password']
        
        if not verify_password(user.password, current_password):
            error = "Wrong Password."
        elif check_password(new_password) is not None:
            error = check_password(new_password)
        elif repeat_new_password != new_password:
            error = 'Incorrect Password Repetition'
            
        if error is None:
            user.password = hash_password(new_password)
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
        
        if getUserByUsername(current_username) is not None:
            error = "Username already exists, please choose a different username."
        elif password != repeat_password:
            error = "Passwords do not match. Please try again."
        else:
            error = check_password(password)
            if error is None:
                hashed_password = hash_password(password)
                user = User('', current_username, '', '', hashed_password, False)
                insertUser(user)
                return redirect(url_for('login'))
                
    return render_template('register.html', error=error)

@app.route('/delete_user', methods=['GET'])
def delete_user():
    user_id = request.cookies.get('user_id')
    if not user_id or not getUserById(user_id).is_admin:
        abort(403)
        
    current_id = request.args.get('id')
    user = User(current_id, '', '', '', '', False) 
    deleteUser(user)
    
    return redirect(url_for('view_users'))

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    if request.method == 'GET':
        templates = get_all_templates()
        return render_template('choose_a_template.html', templates=templates)
    elif request.method == 'POST':
        template_id = request.form.get('template_id')
        if template_id:
            return redirect(url_for('create_event_by_template_id', template_id=template_id))
            
    return redirect(url_for('login'))

@app.route('/create_event_by_template_id', methods=['GET', 'POST'])
def create_event_by_template_id():
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        if request.method == 'GET':
            template_id = request.args.get('template_id')
            if not template_id:
                return "Template ID not provided!", 400 
            return render_template('create_event_by_template_id.html', template_id=template_id)
        
        if request.method == 'POST':  
            internal_name = request.form.get('internal_name')
            template_id = request.form.get('template_id')
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
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    if request.method == 'GET':
        return render_template('view_events.html', events=getEventByUserId(user_id))

@app.route('/edit_event', methods = ['GET', 'POST'])
def edit_event():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    id = request.args.get('id')
    event = getEventById(id)
    
    if request.method == 'GET':
        return render_template('edit_event.html', event=event)
    elif request.method == 'POST':    
        internal_name = request.form['internal_name']
        template_id = request.form['template_id']
        date = request.form['date']
        address_country = request.form['address_country']
        address_city = request.form['address_city']
        address_line = request.form['address_line']
        display_name = request.form['display_name']
        hall_name = request.form['hall_name']
        unique_domain = request.form['unique_domain']
        
        date_format = '%Y-%m-%dT%H:%M'
        datetime_obj = datetime.strptime(date, date_format)
        
        event = Event(
            internal_name, 
            template_id, 
            user_id, 
            datetime_obj, 
            address_country, 
            address_city, 
            address_line, 
            display_name, 
            hall_name, 
            unique_domain, 
            id=id
        )
        updateEvent(event)
        return redirect(url_for('view_events'))
        
    return redirect(url_for('login'))

@app.route('/delete_event', methods = ['GET', 'POST'])
def delete_event(): 
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    id = request.args.get('id')
    deleteEvent(id)
    return redirect(url_for('view_events'))

@app.route('/create_invitation', methods=['GET', 'POST'])
def create_invitation():
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
            
        event_id = request.args.get('event_id')  
        if request.method == 'GET':
            event = getEventByUserId(user_id)
            return render_template('create_invitation.html', event=event, event_id=event_id)
        elif request.method == 'POST':
            name = request.form['name']
            hash = request.form['hash']
            
            # Отладочная информация
            print(f"Debug - Form data: name={name}, hash={hash}")
            print(f"Debug - Form with_spouse={request.form['with_spouse']}")
            print(f"Debug - Form is_male={request.form['is_male']}")
            
            # Преобразование строк в булевы значения
            with_spouse = request.form['with_spouse'].lower() in ('true', 'yes', 'on', '1')
            is_male = request.form['is_male'].lower() in ('true', 'yes', 'on', '1')
            
            # Создаем приглашение
            invitation = Invitation(
                name, 
                event_id, 
                with_spouse, 
                hash, 
                is_male, 
                None, 
                None, 
                None, 
                0
            )
            
            result = createInvitation(invitation)
            if not result:
                return "Failed to create invitation. Check server logs for details.", 500
                
            return redirect(url_for('view_invitation', event_id=event_id))
            
        return redirect(url_for('login'))
    except Exception as e:
        print(f"Error in create_invitation view: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"An error occurred: {str(e)}", 500

@app.route('/bulk-delete-invitations', methods=['POST'])
def bulk_delete_invitations():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Получаем список ID приглашений для удаления
    invitation_ids = request.form.getlist('ids[]')
    event_id = request.form.get('event_id')
    
    if not invitation_ids:
        # Если не выбрано ни одного приглашения, возвращаемся на страницу
        return redirect(url_for('view_invitation', event_id=event_id))
    
    try:
        # Удаление выбранных приглашений
        for invitation_id in invitation_ids:
            # Получаем приглашение перед удалением
            invitation = getInvitationById(invitation_id)
            # Проверяем, что приглашение существует и принадлежит текущему событию
            if invitation and str(invitation.event_id) == str(event_id):
                deleteInvitation(invitation_id)
        
        # Можно здесь добавить сообщение о успешном удалении, если ваше приложение поддерживает flash-сообщения
        # flash(f'Успешно удалено {len(invitation_ids)} приглашений', 'success')
    except Exception as e:
        print(f"Error in bulk_delete_invitations: {str(e)}")
        import traceback
        traceback.print_exc()
        # Можно добавить сообщение об ошибке, если поддерживаются flash-сообщения
        # flash(f'Ошибка при удалении приглашений: {str(e)}', 'error')
    
    # Перенаправление обратно на страницу приглашений
    return redirect(url_for('view_invitation', event_id=event_id))


@app.route('/delete_invitation', methods = ['GET', 'POST'])
def delete_invitation():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    id = request.args.get('id')
    invitation = getInvitationById(id)
    event_id = invitation.event_id
    deleteInvitation(id)
    return redirect(url_for('view_invitation', event_id=event_id))
@app.route('/view_invitation', methods=['GET', 'POST'])
def view_invitation():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    event_id = request.args.get('event_id')
    invitations = getInvitationsListByEventId(event_id)
    
    # Отладочная информация
    print(f"Debug - Number of invitations: {len(invitations)}")
    for i, invitation in enumerate(invitations):
        print(f"Debug - Invitation {i}: name={invitation.name}, comments={invitation.comments}, attendee_count={invitation.attendee_count}")
    
    return render_template('view_invitations.html', invitations=invitations, event_id=event_id)

# Function to update existing users' passwords in the database to SHA-256
def upgrade_passwords_to_sha256():
    users = getUserListFromDb()
    for user in users:
        if len(user.password) != 64:  # SHA-256 produces 64 characters in hex
            user.password = hash_password(user.password)
            editUser(user)
    print("Existing passwords upgraded to SHA-256 hashing.")

if __name__ == '__main__':
    # Initialize templates
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

    testTemplate = get_template_by_id(7)
    if testTemplate is None:
        create_template_with_id(TemplateDB(7, 'testTemplate', 'test_template.html', 'Test'))
    
    parsicTemplate = get_template_by_id(8)
    if parsicTemplate is None:
        create_template_with_id(TemplateDB(8, 'parsicTemplate', 'parsic.html', 'Parsic'))

    elegantTemplate = get_template_by_id(9)
    if elegantTemplate is None:
        create_template_with_id(TemplateDB(9, 'elegantTemplate', 'elegant.html', 'Elegant'))

    parsicAmTemplate = get_template_by_id(10)
    if parsicAmTemplate is None:
        create_template_with_id(TemplateDB(10, 'parsicAmTemplate', 'parsic_am.html', 'Parsic Armenian'))
try:
    print("Attempting to add comments column...")
    result = executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS comments TEXT;")
    print(f"Result: {result}")
    
    print("Attempting to add attendee_count column...")
    result = executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS attendee_count INTEGER DEFAULT 0;")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error adding columns: {e}")
    # Upgrade existing passwords to SHA-256
    

upgrade_passwords_to_sha256()
app.run(host='0.0.0.0', port=getFullConfig()['app']['port'] , debug=getFullConfig()['app']['debug'])