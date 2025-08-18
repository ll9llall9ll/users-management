#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функции экспорта CSV с ссылками
Работает с combined_app.py
"""

import requests
import json
import csv
import io

# Конфигурация
BASE_URL = "http://localhost:5000"
TEST_EVENT_ID = 1  # Замените на реальный ID события

def test_csv_export():
    """Тестирует функцию экспорта CSV с ссылками"""
    
    print("=== Тест экспорта CSV с ссылками ===")
    print(f"📍 URL сервера: {BASE_URL}")
    print(f"🎯 ID события: {TEST_EVENT_ID}")
    print()
    
    # Данные для запроса
    data = {
        "event_id": TEST_EVENT_ID,
        "language": "ru"  # или "hy" для армянского
    }
    
    try:
        # Отправляем запрос
        print("📤 Отправляем запрос на экспорт CSV...")
        response = requests.post(
            f"{BASE_URL}/api/export_csv_guests_with_links",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Экспорт успешен!")
                print(f"📊 Всего гостей: {result.get('total_guests')}")
                print(f"📁 Имя файла: {result.get('filename')}")
                
                # Парсим CSV данные для проверки
                csv_data = result.get('csv_data', '')
                print("\n📋 Содержимое CSV:")
                print("=" * 80)
                
                # Читаем CSV
                csv_reader = csv.reader(io.StringIO(csv_data))
                for i, row in enumerate(csv_reader):
                    if i == 0:
                        print(f"Заголовок: {row}")
                    else:
                        print(f"Строка {i}: {row}")
                
                print("=" * 80)
                
                # Сохраняем файл для проверки
                with open(f"test_export_{TEST_EVENT_ID}.csv", "w", encoding="utf-8") as f:
                    f.write(csv_data)
                print(f"💾 Файл сохранен как: test_export_{TEST_EVENT_ID}.csv")
                
            else:
                print(f"❌ Ошибка: {result.get('error')}")
        elif response.status_code == 401:
            print("❌ Ошибка аутентификации: необходимо войти в систему")
        elif response.status_code == 404:
            print("❌ Ошибка: событие или приглашения не найдены")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу. Убедитесь, что combined_app.py запущен.")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

def test_armenian_export():
    """Тестирует экспорт на армянском языке"""
    
    print("\n=== Тест экспорта CSV на армянском языке ===")
    
    data = {
        "event_id": TEST_EVENT_ID,
        "language": "hy"
    }
    
    try:
        print("📤 Отправляем запрос на экспорт CSV (армянский)...")
        response = requests.post(
            f"{BASE_URL}/api/export_csv_guests_with_links",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Экспорт на армянском успешен!")
                
                # Показываем заголовок на армянском
                csv_data = result.get('csv_data', '')
                csv_reader = csv.reader(io.StringIO(csv_data))
                header = next(csv_reader)
                print(f"Заголовок на армянском: {header}")
                
                # Сохраняем файл
                with open(f"test_export_hy_{TEST_EVENT_ID}.csv", "w", encoding="utf-8") as f:
                    f.write(csv_data)
                print(f"💾 Файл сохранен как: test_export_hy_{TEST_EVENT_ID}.csv")
            else:
                print(f"❌ Ошибка: {result.get('error')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

def test_error_cases():
    """Тестирует обработку ошибок"""
    
    print("\n=== Тест обработки ошибок ===")
    
    # Тест без event_id
    print("🔍 Тест без event_id...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/export_csv_guests_with_links",
            json={"language": "ru"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            result = response.json()
            print(f"✅ Правильная обработка ошибки: {result.get('error')}")
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
    
    # Тест с несуществующим event_id
    print("🔍 Тест с несуществующим event_id...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/export_csv_guests_with_links",
            json={"event_id": 99999, "language": "ru"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 404:
            result = response.json()
            print(f"✅ Правильная обработка ошибки: {result.get('error')}")
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Запуск тестов экспорта CSV для combined_app.py...")
    print("=" * 60)
    
    test_csv_export()
    test_armenian_export()
    test_error_cases()
    
    print("\n" + "=" * 60)
    print("✨ Тестирование завершено!")
    print("\n📝 Инструкции:")
    print("1. Убедитесь, что combined_app.py запущен на порту 5000")
    print("2. Измените TEST_EVENT_ID на реальный ID события")
    print("3. Проверьте созданные CSV файлы")
