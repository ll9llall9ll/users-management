#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки CSV импорта
"""

import requests
import json

def test_csv_import():
    # URL вашего приложения
    base_url = "http://localhost:5000"
    
    # Тестовые данные CSV
    csv_data = """Сторона,Имя гостя,Имя Гостя в приглашении
София,Мама,Анаит Ервандовна
София,Папа,Ерванд Арамаисович
София,Бабушка,Людмила Петровна"""
    
    # Данные для запроса
    payload = {
        "event_id": "1",  # Замените на реальный event_id
        "csv_data": csv_data,
        "language": "ru"
    }
    
    print("Testing CSV import...")
    print(f"Event ID: {payload['event_id']}")
    print(f"CSV data: {csv_data}")
    print(f"URL: {base_url}/api/import_csv_guests")
    
    try:
        # Отправляем POST запрос
        response = requests.post(
            f"{base_url}/api/import_csv_guests",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Imported count: {result.get('imported_count')}")
            if 'errors' in result:
                print(f"Errors: {result['errors']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_csv_import()
