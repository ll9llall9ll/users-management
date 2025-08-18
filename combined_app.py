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
import time
import random
import string
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


def generate_guest_hash(guest_name, event_id):
    """
    Генерирует короткий хеш для гостя, содержащий его имя.
    Формат: {первые_буквы_имени}{короткий_хеш}
    Пример: Анаит -> ana7x2k, Ерванд -> erv9m4p
    """
    # Словарь для транслитерации русских букв
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Очищаем имя от лишних символов и транслитерируем
    clean_name = ''
    for c in guest_name:
        if c.isalpha():
            # Транслитерируем русские буквы
            if c in translit_map:
                clean_name += translit_map[c]
            else:
                # Оставляем латинские буквы как есть
                clean_name += c.lower()
    
    # Берем первые 3-4 буквы имени
    name_part = clean_name[:4] if len(clean_name) >= 4 else clean_name
    
    # Генерируем короткий случайный хеш (4 символа)
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(4))
    
    # Объединяем имя и случайную часть
    hash_value = f"{name_part}{random_part}"
    
    # Добавляем timestamp для уникальности
    timestamp = str(int(time.time()))[-3:]  # Последние 3 цифры timestamp
    
    return f"{hash_value}{timestamp}"



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
     str_date = d.strftime("%d.%m.%Y")
     return str_date
app.add_template_filter(date)

appData = AppData()


GOOGLE_CLIENT_ID = getFullConfig()['google_oauth_config']['client_id'] 

# Хранилище сессий
active_sessions = set()

# Настройка клиента OpenAI с ключом API
client = OpenAI(api_key=getOpenaiConfig()['api_key'])

# Декоратор для проверки аутентификации
def require_auth(f):
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        if not session_id or session_id not in active_sessions:
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
            session_id = request.cookies.get('session_id')
            if not session_id or session_id not in active_sessions:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            # Если передана фабричная функция для события, используем её
            if event_factory:
                try:
                    event = event_factory()
                    if not event:
                        return jsonify({'success': False, 'error': 'Event not found'}), 404
                    
                    user_id = request.cookies.get('user_id')
                    user = getUserById(user_id)
                    if user.is_admin:
                        return f(*args, **kwargs)
                    elif event.user_id == user.id:
                        return f(*args, **kwargs)
                    else:
                        print("Wtf")
                        return jsonify({'success': False, 'error': 'You are not authorized to access this event'}), 403
                    
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

@app.route('/api/transcribe', methods=['POST'])
@require_auth  # Простая аутентификация без проверки события
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
                    spouse_name = f"{invitation.name}-ի կին" if is_male else f"{invitation.name}-ի ամուսին"
                else:
                    spouse_name = f"Супруга ({invitation.name})" if is_male else f"Супруг ({invitation.name})"
                
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
            guest_link = f"{base_url}/invite?h={invitation.hash}"
            
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

def detect_gender_by_name(name):
    """
    Улучшенная функция для определения пола по имени.
    Учитывает армянские и русские имена.
    """
    name_lower = name.lower()
    
    # Список женских армянских имен
    female_names = [
        'լիլիթ', 'մարիամ', 'սիրանուշ', 'անահիտ', 'հասմիկ', 'նարինե', 'արիանա', 'մարիա', 'սոնա', 'լիզա', 'կարինե',
        'հայկուհի', 'վարդուհի', 'սիրանույշ', 'անահիտ', 'լուսինե', 'հասմիկ', 'նարինե', 'արիանա', 'մարիա', 'սոնա', 'լիզա', 'կարինե',
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
                print(f"Error processing line {line_num}: {str(e)}")
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
            return render_template('invite_accepted_ru.html', 
                                 invitation=invitation,
                                 hall_name=event.hall_name or 'Место будет уточнено', 
                                 event_date=event.date.strftime('%d.%m.%Y') if event.date else 'Дата будет уточнена')
        else:
            return render_template('invite_declined_ru.html', invitation=invitation)
    
    # Если ответа еще нет, показываем форму приглашения
    event = getEventById(invitation.event_id)
    template = get_template_by_id(event.template_id)
    
    if request.method == 'POST':
        accepted = request.form['action'] == 'accepted'
        
        # Получаем комментарии из формы - проверяем на None и empty string
        comments = request.form.get('comment', '')
        if not comments:  # Это проверит на None, пустую строку и строку с пробелами
            comments = None
        
        # Получаем тип участия (attendance_type)
        attendance_type = request.form.get('attendance_type', 'alone')
        
        # Определяем with_spouse на основе attendance_type
        with_spouse = attendance_type == 'with_partner'
        
        # Получаем количество гостей на основе типа участия
        attendee_count = 0
        if accepted:
            if attendance_type == 'alone':
                attendee_count = 1
            elif attendance_type == 'with_partner':
                attendee_count = 2
            else:
                attendee_count = 1
        
        # Получаем информацию о посещении церкви и ресторана
        church_attendance = 'church_attendance' in request.form
        restaurant_attendance = 'restaurant_attendance' in request.form
        
        # Обновляем объект приглашения
        invitation.with_spouse = with_spouse
        invitation.accepted = accepted
        invitation.comments = comments
        invitation.attendee_count = attendee_count
        invitation.church_attendance = church_attendance
        invitation.restaurant_attendance = restaurant_attendance
        invitation.attendance_type = attendance_type
        
        # Отладочная информация
        print(f"Debug - Saving invitation with comments: '{invitation.comments}'")
        print(f"Debug - With spouse: {with_spouse}")
        print(f"Debug - Attendance type: {attendance_type}")
        print(f"Debug - Attendee count: {attendee_count}")
        print(f"Debug - Church attendance: {church_attendance}")
        print(f"Debug - Restaurant attendance: {restaurant_attendance}")
        
        # Сохраняем в базу данных
        updateInvitation(invitation)
        
        # После сохранения показываем соответствующую страницу
        if accepted:
            return render_template('invite_accepted_ru.html', 
                                 invitation=invitation,
                                 hall_name=event.hall_name or 'Место будет уточнено', 
                                 event_date=event.date.strftime('%d.%m.%Y') if event.date else 'Дата будет уточнена')
        else:
            return render_template('invite_declined_ru.html', invitation=invitation)
    
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
        
        # Получаем информацию о посещении церкви и ресторана
        church_attendance = request.form.get('church_attendance') == 'True'
        restaurant_attendance = request.form.get('restaurant_attendance') == 'True'
            
        # Отладочная информация
        print(f"Debug - Updating invitation with comments: '{comments}'")
        print(f"Debug - Church attendance: {church_attendance}")
        print(f"Debug - Restaurant attendance: {restaurant_attendance}")
        
        # Получаем псевдоним гостя
        guest_nickname = request.form.get('guest_nickname', '').strip() or None
        
        # Создаем обновленный объект приглашения со всеми полями
        invitation = Invitation(name, event_id, with_spouse, hash, is_male, accepted, id, comments, attendee_count, church_attendance, restaurant_attendance, None, guest_nickname)
        
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
            guest_nickname = request.form.get('guest_nickname', '').strip() or None
            
            # Отладочная информация
            print(f"Debug - Form data: name={name}, hash={hash}, guest_nickname={guest_nickname}")
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
                0,
                False,  # church_attendance
                False,  # restaurant_attendance
                None,   # attendance_type
                guest_nickname
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
        print(f"Debug - Invitation {i}: name={invitation.name}, comments={invitation.comments}, attendee_count={invitation.attendee_count}, attendance_type={invitation.attendance_type}")
    
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
    
    parsicRuTemplate = get_template_by_id(12)
    if parsicRuTemplate is None:
        create_template_with_id(TemplateDB(12, 'parsicRuTemplate', 'parsic_ru.html', 'Parsic Russian'))
    
    elegantWedding = get_template_by_id(11)
    if elegantWedding is None:
        create_template_with_id(TemplateDB(11, 'elegantWedding_template_Arm', 'elegant_wedding_template.html', 'Elegant Wedding Arm'))
    
    # Добавляем новые шаблоны New Design Template
    newDesignTemplate = get_template_by_id(13)
    if newDesignTemplate is None:
        create_template_with_id(TemplateDB(13, 'New Design Template', 'newDesign_template.html', 'wedding'))
    
    newDesignTemplateAM = get_template_by_id(14)
    if newDesignTemplateAM is None:
        create_template_with_id(TemplateDB(14, 'New Design Template AM', 'newDesign_template_AM.html', 'wedding'))
try:
    print("Attempting to add comments column...")
    result = executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS comments TEXT;")
    print(f"Result: {result}")
    
    print("Attempting to add attendee_count column...")
    result = executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS attendee_count INTEGER DEFAULT 0;")
    print(f"Result: {result}")
    
    print("Attempting to add church_attendance column...")
    result = executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS church_attendance BOOLEAN DEFAULT false;")
    print(f"Result: {result}")
    
    print("Attempting to add restaurant_attendance column...")
    result = executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS restaurant_attendance BOOLEAN DEFAULT false;")
    print(f"Result: {result}")
    
    print("Attempting to add attendance_type column...")
    result = executeQuery("ALTER TABLE invitation ADD COLUMN IF NOT EXISTS attendance_type VARCHAR(50);")
    print(f"Result: {result}")
    
    # Ensure all new columns exist
    from invitation_db import ensure_new_columns_exist
    ensure_new_columns_exist()
except Exception as e:
    print(f"Error adding columns: {e}")
    # Upgrade existing passwords to SHA-256
    

upgrade_passwords_to_sha256()
app.run(host='0.0.0.0', port=getFullConfig()['app']['port'] , debug=getFullConfig()['app']['debug'])