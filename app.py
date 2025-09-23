from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import requests
import time
import os
import uuid
from datetime import datetime

app = Flask(__name__)

# Папка для сохранения изображений
UPLOAD_FOLDER = 'generated_images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def generate_image_fast(prompt, width=1024, height=1024):
    """
    Быстрая генерация изображения через Pollinations AI
    """
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&nologo=true"
        
        start_time = time.time()
        response = requests.get(url, timeout=15)
        end_time = time.time()
        generation_time = end_time - start_time
        
        if response.status_code == 200:
            return response.content, generation_time, None
        else:
            return None, generation_time, f"API ошибка: {response.status_code}"
            
    except Exception as e:
        return None, 0, str(e)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Favicon для избежания ошибки 404"""
    return '', 204

@app.route('/generate', methods=['POST'])
def generate_image():
    """API для генерации изображения"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'error': 'Промпт не может быть пустым'}), 400
        
        # Генерируем изображение
        image_data, gen_time, error = generate_image_fast(prompt)
        
        if error:
            return jsonify({'error': f'Ошибка генерации: {error}'}), 500
        
        # Сохраняем изображение
        filename = f"image_{uuid.uuid4().hex[:8]}_{int(time.time())}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'generation_time': round(gen_time, 2),
            'file_size': len(image_data),
            'prompt': prompt
        })
        
    except Exception as e:
        return jsonify({'error': f'Серверная ошибка: {str(e)}'}), 500

@app.route('/generated_images/<filename>')
def serve_image(filename):
    """Обслуживание изображений для отображения"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({'error': f'Ошибка загрузки изображения: {str(e)}'}), 404

@app.route('/download/<filename>')
def download_image(filename):
    """Скачивание изображения"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'Файл не найден'}), 404
    except Exception as e:
        return jsonify({'error': f'Ошибка скачивания: {str(e)}'}), 500

@app.route('/images')
def list_images():
    """Список всех сгенерированных изображений"""
    try:
        images = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.png'):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                stat = os.stat(filepath)
                images.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Сортируем по дате создания (новые сначала)
        images.sort(key=lambda x: x['created'], reverse=True)
        return jsonify({'images': images})
        
    except Exception as e:
        return jsonify({'error': f'Ошибка получения списка: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Запуск веб-сервиса генерации изображений...")
    print("📱 Откройте браузер: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
