#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой тест функции генерации коротких хешей с именем гостя
"""

import time
import random
import string

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

def test_hash_generation():
    """Тестирует генерацию хешей для разных имен"""
    
    test_names = [
        "Анаит Ервандовна",
        "Ерванд Арамаисович", 
        "Людмила Петровна",
        "Сергей",
        "Мария",
        "Александр",
        "Елена",
        "Дмитрий",
        "Ольга",
        "Михаил"
    ]
    
    event_id = 123
    
    print("Тестирование новой функции генерации хешей:")
    print("=" * 50)
    
    for name in test_names:
        hash_value = generate_guest_hash(name, event_id)
        print(f"Имя: {name:<20} -> Хеш: {hash_value}")
    
    print("\n" + "=" * 50)
    print("Проверка уникальности хешей:")
    
    # Проверяем, что хеши уникальны
    hashes = set()
    for name in test_names:
        for i in range(5):  # Генерируем 5 хешей для каждого имени
            hash_value = generate_guest_hash(name, event_id)
            if hash_value in hashes:
                print(f"❌ Дубликат хеша: {hash_value}")
            else:
                hashes.add(hash_value)
                print(f"✅ Уникальный хеш: {hash_value}")
    
    print(f"\nВсего сгенерировано уникальных хешей: {len(hashes)}")
    print(f"Ожидалось: {len(test_names) * 5}")
    
    print("\n" + "=" * 50)
    print("Примеры ссылок для гостей:")
    
    for name in test_names[:5]:  # Показываем первые 5
        hash_value = generate_guest_hash(name, event_id)
        link = f"http://localhost:5000/invite?h={hash_value}"
        print(f"{name:<20} -> {link}")

if __name__ == "__main__":
    test_hash_generation()
