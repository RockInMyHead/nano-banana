import requests
import time
import asyncio
import aiohttp

def generate_image_fast(prompt, width=1024, height=1024):
    """
    Ультра-быстрая генерация изображения только через рабочий API
    """
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&nologo=true"
        
        print(f"🚀 Быстрая генерация...")
        start_time = time.time()
        
        # Минимальный timeout для быстрого ответа
        response = requests.get(url, timeout=10)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        if response.status_code == 200:
            print(f"⏱️  Время генерации: {generation_time:.2f} сек")
            return response.content, generation_time
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return None, generation_time
            
    except Exception as e:
        end_time = time.time()
        generation_time = end_time - start_time
        print(f"❌ Ошибка: {e}")
        return None, generation_time

def generate_multiple_images(prompt, count=3):
    """
    Генерация нескольких изображений последовательно (быстрее чем параллельно для одного API)
    """
    print(f"🚀 Генерация {count} изображений...")
    
    total_start = time.time()
    results = []
    total_generation_time = 0
    
    for i in range(count):
        print(f"\n📸 Изображение {i+1}/{count}:")
        result = generate_image_fast(prompt)
        
        if result[0] is not None:
            results.append(result)
            total_generation_time += result[1]
            print(f"✅ Изображение {i+1} готово")
        else:
            print(f"❌ Изображение {i+1} не удалось")
    
    total_time = time.time() - total_start
    return results, total_time, total_generation_time

def save_images_fast(results):
    """
    Быстрое сохранение всех изображений
    """
    print(f"\n💾 Быстрое сохранение {len(results)} изображений...")
    save_start = time.time()
    
    for i, (image_data, gen_time) in enumerate(results):
        filename = f"hogwarts_castle_fast_{i+1}.png"
        with open(filename, "wb") as f:
            f.write(image_data)
        print(f"✅ {filename}")
    
    save_time = time.time() - save_start
    return save_time

# Основная функция
if __name__ == "__main__":
    prompt = "Hogwarts castle, magical school, Harry Potter, magnificent gothic architecture, towering spires, colorful stained glass windows, golden hour lighting, magical floating candles, mystical fog, vibrant autumn colors, detailed stone walls, enchanted forest background, magical atmosphere, cinematic lighting, ultra detailed, 4K resolution, fantasy art"
    
    print("⚡ УЛЬТРА-БЫСТРАЯ генерация изображений")
    print(f"Промпт: {prompt}")
    print("=" * 50)
    
    total_start_time = time.time()
    
    # Генерация одного изображения для максимальной скорости
    results, total_time, total_generation_time = generate_multiple_images(prompt, count=1)
    
    # Быстрое сохранение
    save_time = save_images_fast(results)
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    print(f"\n📊 УЛЬТРА-БЫСТРАЯ СТАТИСТИКА:")
    print(f"   Общее время выполнения: {total_execution_time:.2f} секунд")
    print(f"   Время генерации: {total_generation_time:.2f} секунд")
    print(f"   Время сохранения: {save_time:.2f} секунд")
    print(f"   Успешно сгенерировано: {len(results)} изображений")
    
    if len(results) > 0:
        print(f"   Среднее время на изображение: {total_generation_time/len(results):.2f} секунд")
        print(f"   Скорость генерации: {len(results)/total_generation_time:.2f} изображений/сек")
        print(f"   Эффективность: {total_generation_time/total_execution_time*100:.1f}%")
    
    # Детализация времени
    overhead_time = total_execution_time - total_generation_time - save_time
    print(f"\n🔍 Детализация времени:")
    print(f"   Генерация: {total_generation_time:.2f} сек ({total_generation_time/total_execution_time*100:.1f}%)")
    print(f"   Сохранение: {save_time:.2f} сек ({save_time/total_execution_time*100:.1f}%)")
    print(f"   Накладные расходы: {overhead_time:.2f} сек ({overhead_time/total_execution_time*100:.1f}%)")
    
    print(f"\n⚡ ОПТИМИЗАЦИИ:")
    print(f"   ✅ Только рабочий API (Pollinations)")
    print(f"   ✅ Минимальные таймауты")
    print(f"   ✅ Быстрое сохранение")
    print(f"   ✅ Нет лишних запросов")
    print(f"   ✅ Фокус на производительности")
    
    print(f"\nГотово! Проверьте файлы в текущей папке.")
