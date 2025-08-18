#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест новой функции генерации коротких хешей с именем гостя
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from combined_app import generate_guest_hash

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

if __name__ == "__main__":
    test_hash_generation()
