import requests
import time

def test_web_service():
    """Тестирование веб-сервиса"""
    base_url = "http://localhost:5001"
    
    print("🧪 Тестирование веб-сервиса...")
    
    # Тест 1: Проверка главной страницы
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Главная страница работает")
        else:
            print(f"❌ Главная страница: {response.status_code}")
    except Exception as e:
        print(f"❌ Главная страница: {e}")
        return
    
    # Тест 2: Генерация изображения
    try:
        print("🎨 Тестирование генерации изображения...")
        data = {"prompt": "simple test image, colorful, high quality"}
        response = requests.post(f"{base_url}/generate", json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Изображение сгенерировано за {result['generation_time']} сек")
                print(f"📁 Файл: {result['filename']}")
                print(f"📏 Размер: {result['file_size']} байт")
            else:
                print(f"❌ Ошибка генерации: {result.get('error')}")
        else:
            print(f"❌ Ошибка API: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
    
    # Тест 3: Список изображений
    try:
        print("📋 Тестирование списка изображений...")
        response = requests.get(f"{base_url}/images", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Найдено изображений: {len(data.get('images', []))}")
        else:
            print(f"❌ Ошибка списка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка списка: {e}")
    
    print("\n🌐 Веб-сервис готов к использованию!")
    print("📱 Откройте браузер: http://localhost:5001")

if __name__ == "__main__":
    test_web_service()
